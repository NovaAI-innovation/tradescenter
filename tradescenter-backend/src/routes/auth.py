import re

from flask import Blueprint, g, jsonify, request

from src.authz import ALLOWED_ROLES, get_or_create_profile, require_auth, resolve_current_profile
from src.identity import attach_identity_context, ensure_identity_graph
from src.local_auth import create_access_token, create_local_user, is_local_auth_enabled, verify_local_user
from src.supabase_client import get_supabase_client
from src.utils import error_response, normalize_record


auth_bp = Blueprint("auth", __name__)


def _validate_email(email: str):
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def _validate_password(password: str):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    return True, None


def _auth_error_response(exc: Exception):
    message = str(exc).strip() or "Authentication failed"
    lowered = message.lower()

    if "email not confirmed" in lowered or "email_not_confirmed" in lowered:
        return error_response(
            "Email not confirmed. Check your inbox for the verification link or request a new verification email.",
            403,
        )
    if "invalid login credentials" in lowered:
        return error_response("Invalid email or password", 401)
    if "user already registered" in lowered:
        return error_response("An account with that email already exists", 409)

    return error_response(message, 400)


def _create_profile_for_local_user(local_user: dict, role: str):
    supabase = get_supabase_client()
    tier = "free" if role == "contractor" else None
    created = (
        supabase.table("profiles")
        .insert(
            {
                "auth_user_id": local_user["auth_user_id"],
                "email": local_user["email"],
                "display_name": local_user["display_name"],
                "role": role,
                "contractor_tier": tier,
                "tier_status": "active",
                "registration_status": "active",
                "email_verified": True,
                "is_suspended": False,
            }
        )
        .execute()
    )
    if not created.data:
        raise RuntimeError("Profile creation failed")
    profile = normalize_record(created.data[0])
    try:
        ensure_identity_graph(profile, desired_role=role)
        return attach_identity_context(profile)
    except Exception:
        return profile


def _get_profile_by_auth_user_id(auth_user_id: str):
    response = (
        get_supabase_client()
        .table("profiles")
        .select("*")
        .eq("auth_user_id", auth_user_id)
        .limit(1)
        .execute()
    )
    profile = normalize_record(response.data[0]) if response.data else None
    if not profile:
        return None
    try:
        return attach_identity_context(profile)
    except Exception:
        return profile


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        display_name = (data.get("display_name") or "").strip()
        role = (data.get("role") or "user").strip().lower()
        redirect_to = (data.get("redirect_to") or "").strip()

        if not email or not password or not display_name:
            return error_response("email, password, and display_name are required")
        if not _validate_email(email):
            return error_response("Invalid email format")
        valid_password, error = _validate_password(password)
        if not valid_password:
            return error_response(error)
        if role not in ALLOWED_ROLES:
            return error_response("Invalid role")
        if role == "admin":
            role = "user"

        if is_local_auth_enabled():
            local_user = create_local_user(email, password, display_name)
            profile = _create_profile_for_local_user(local_user, role)
            access_token = create_access_token(local_user["auth_user_id"], email)
            return jsonify(
                {
                    "message": "Registration successful",
                    "profile": profile,
                    "requires_email_verification": False,
                    "session": {"token_type": "bearer"},
                    "access_token": access_token,
                    "refresh_token": None,
                }
            ), 201

        supabase = get_supabase_client()
        auth_response = supabase.auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {
                    "data": {"display_name": display_name},
                    **({"email_redirect_to": redirect_to} if redirect_to else {}),
                },
            }
        )
        auth_user = auth_response.user if auth_response else None
        if not auth_user:
            return error_response("Registration failed", 500)

        profile = get_or_create_profile(auth_user, desired_role=role)
        return jsonify(
            {
                "message": (
                    "Registration successful. Check your email to verify your account before logging in."
                    if not auth_response.session
                    else "Registration successful"
                ),
                "profile": profile,
                "requires_email_verification": auth_response.session is None,
                "session": {
                    "expires_at": auth_response.session.expires_at,
                    "token_type": auth_response.session.token_type,
                }
                if auth_response.session
                else None,
                "access_token": auth_response.session.access_token if auth_response.session else None,
                "refresh_token": auth_response.session.refresh_token if auth_response.session else None,
            }
        ), 201
    except Exception as exc:
        return _auth_error_response(exc)


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""
        if not email or not password:
            return error_response("Email and password are required")

        if is_local_auth_enabled():
            local_user = verify_local_user(email, password)
            if not local_user:
                return error_response("Invalid email or password", 401)
            profile = _get_profile_by_auth_user_id(local_user["auth_user_id"])
            if not profile:
                return error_response("Profile not found", 404)
            return jsonify(
                {
                    "message": "Login successful",
                    "profile": profile,
                    "access_token": create_access_token(local_user["auth_user_id"], email),
                    "refresh_token": None,
                }
            )

        supabase = get_supabase_client()
        auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        auth_user = auth_response.user if auth_response else None
        if not auth_user:
            return error_response("Invalid credentials", 401)

        profile = get_or_create_profile(auth_user)
        return jsonify(
            {
                "message": "Login successful",
                "profile": profile,
                "access_token": auth_response.session.access_token if auth_response.session else None,
                "refresh_token": auth_response.session.refresh_token if auth_response.session else None,
            }
        )
    except Exception as exc:
        return _auth_error_response(exc)


@auth_bp.route("/auth/verification/resend", methods=["POST"])
def resend_verification():
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        phone = (data.get("phone") or "").strip()
        otp_type = (data.get("type") or "signup").strip().lower()
        redirect_to = (data.get("redirect_to") or "").strip()

        if not email and not phone:
            return error_response("email or phone is required")

        allowed_types = {"signup", "email", "sms", "recovery", "email_change", "phone_change"}
        if otp_type not in allowed_types:
            return error_response("Invalid verification type")

        payload = {
            "type": otp_type,
            "email": email or None,
            "phone": phone or None,
            "options": {"email_redirect_to": redirect_to} if redirect_to else {},
        }

        supabase = get_supabase_client()
        supabase.auth.resend(payload)
        return jsonify({"message": "Verification code resent"})
    except Exception as exc:
        return error_response(str(exc), 400)


@auth_bp.route("/auth/otp/request", methods=["POST"])
def request_sms_otp():
    try:
        data = request.get_json(silent=True) or {}
        phone = (data.get("phone") or "").strip()
        channel = (data.get("channel") or "sms").strip().lower()

        if not phone:
            return error_response("phone is required")
        if channel not in {"sms", "whatsapp"}:
            return error_response("Invalid channel")

        supabase = get_supabase_client()
        supabase.auth.sign_in_with_otp(
            {
                "phone": phone,
                "options": {"should_create_user": False, "channel": channel},
            }
        )
        return jsonify({"message": "OTP sent"})
    except Exception as exc:
        return error_response(str(exc), 400)


@auth_bp.route("/auth/otp/verify", methods=["POST"])
def verify_otp():
    try:
        data = request.get_json(silent=True) or {}
        token = (data.get("token") or "").strip()
        email = (data.get("email") or "").strip().lower()
        phone = (data.get("phone") or "").strip()
        otp_type = (data.get("type") or "").strip().lower()

        if not token:
            return error_response("token is required")
        if not otp_type:
            return error_response("type is required")
        if not email and not phone:
            return error_response("email or phone is required")

        params = {
            "token": token,
            "type": otp_type,
            "email": email or None,
            "phone": phone or None,
        }

        supabase = get_supabase_client()
        auth_response = supabase.auth.verify_otp(params)
        auth_user = auth_response.user if auth_response else None
        if not auth_user:
            return error_response("OTP verification failed", 401)

        profile = get_or_create_profile(auth_user)
        return jsonify(
            {
                "message": "Verification successful",
                "profile": profile,
                "access_token": auth_response.session.access_token if auth_response.session else None,
                "refresh_token": auth_response.session.refresh_token if auth_response.session else None,
            }
        )
    except Exception as exc:
        return error_response(str(exc), 400)


@auth_bp.route("/auth/password/recover", methods=["POST"])
def recover_password():
    try:
        data = request.get_json(silent=True) or {}
        email = (data.get("email") or "").strip().lower()
        redirect_to = (data.get("redirect_to") or "").strip()

        if not email:
            return error_response("email is required")
        if not _validate_email(email):
            return error_response("Invalid email format")

        options = {"redirect_to": redirect_to} if redirect_to else {}
        supabase = get_supabase_client()
        supabase.auth.reset_password_for_email(email, options)
        return jsonify({"message": "Password recovery email sent"})
    except Exception as exc:
        return error_response(str(exc), 400)


@auth_bp.route("/auth/me", methods=["GET"])
def me():
    profile, error = resolve_current_profile()
    if error:
        return error
    return jsonify({"profile": profile})


@auth_bp.route("/auth/logout", methods=["POST"])
def logout():
    return jsonify({"message": "Logout successful"})


@auth_bp.route("/auth/profile", methods=["PUT"])
@require_auth
def update_profile():
    try:
        data = request.get_json(silent=True) or {}
        allowed = {"display_name", "bio", "avatar_url"}
        payload = {key: value for key, value in data.items() if key in allowed}
        if not payload:
            return error_response("No valid fields provided for update")

        supabase = get_supabase_client()
        updated = (
            supabase.table("profiles")
            .update(payload)
            .eq("id", g.current_profile["id"])
            .execute()
        )
        if not updated.data:
            return error_response("Profile not found", 404)
        return jsonify({"profile": normalize_record(updated.data[0])})
    except Exception as exc:
        return error_response(str(exc), 500)
