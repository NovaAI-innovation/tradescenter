from functools import wraps
from typing import Callable

from flask import g, request

from src.identity import attach_identity_context, ensure_identity_graph
from src.local_auth import decode_access_token, is_local_auth_enabled
from src.supabase_client import get_supabase_client
from src.utils import error_response, normalize_record


ALLOWED_ROLES = {"admin", "user", "contractor"}
ALLOWED_TIERS = {"free", "pro", "platinum"}


def get_bearer_token() -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip()


def is_contractor_profile(profile: dict | None) -> bool:
    return (profile or {}).get("role") == "contractor"


def require_contractor_profile(profile: dict | None):
    if not is_contractor_profile(profile):
        return error_response("Contractor account required", 403)
    return None


def get_or_create_profile(auth_user, desired_role: str = "user"):
    supabase = get_supabase_client()
    auth_user_id = auth_user.id

    profile_resp = (
        supabase.table("profiles")
        .select("*")
        .eq("auth_user_id", auth_user_id)
        .limit(1)
        .execute()
    )
    if profile_resp.data:
        existing = normalize_record(profile_resp.data[0])
        if not is_contractor_profile(existing) and existing.get("contractor_tier") is not None:
            repaired = (
                supabase.table("profiles")
                .update({"contractor_tier": None, "tier_status": "active"})
                .eq("id", existing["id"])
                .execute()
            )
            if repaired.data:
                existing = normalize_record(repaired.data[0])
        try:
            ensure_identity_graph(existing, desired_role=desired_role)
            return attach_identity_context(existing)
        except Exception:
            return existing

    role = desired_role if desired_role in ALLOWED_ROLES else "user"
    tier = "free" if role == "contractor" else None

    created = (
        supabase.table("profiles")
        .insert(
            {
                "auth_user_id": auth_user_id,
                "email": auth_user.email,
                "display_name": auth_user.user_metadata.get("display_name")
                if auth_user.user_metadata
                else auth_user.email.split("@")[0],
                "role": role,
                "contractor_tier": tier,
                "tier_status": "active",
                "is_suspended": False,
            }
        )
        .execute()
    )
    profile = normalize_record(created.data[0])
    try:
        ensure_identity_graph(profile, desired_role=desired_role)
        return attach_identity_context(profile)
    except Exception:
        return profile


def resolve_current_profile():
    token = get_bearer_token()
    if not token:
        return None, error_response("Authentication required", 401)

    supabase = get_supabase_client()
    if is_local_auth_enabled():
        payload = decode_access_token(token)
        if not payload:
            return None, error_response("Invalid authentication token", 401)
        profile_resp = (
            supabase.table("profiles")
            .select("*")
            .eq("auth_user_id", payload["sub"])
            .limit(1)
            .execute()
        )
        profile = normalize_record(profile_resp.data[0]) if profile_resp.data else None
        if not profile:
            return None, error_response("Invalid authentication token", 401)
        if profile.get("is_suspended"):
            return None, error_response("Account is suspended", 403)
        try:
            return attach_identity_context(profile), None
        except Exception:
            return profile, None

    try:
        user_response = supabase.auth.get_user(jwt=token)
    except Exception:
        return None, error_response("Invalid authentication token", 401)

    auth_user = user_response.user if user_response else None
    if not auth_user:
        return None, error_response("Invalid authentication token", 401)

    profile = get_or_create_profile(auth_user)
    if profile.get("is_suspended"):
        return None, error_response("Account is suspended", 403)
    try:
        return attach_identity_context(profile), None
    except Exception:
        return profile, None


def require_auth(handler: Callable):
    @wraps(handler)
    def wrapped(*args, **kwargs):
        profile, error = resolve_current_profile()
        if error:
            return error
        g.current_profile = profile
        return handler(*args, **kwargs)

    return wrapped


def require_roles(*roles: str):
    accepted = set(roles)

    def decorator(handler: Callable):
        @wraps(handler)
        def wrapped(*args, **kwargs):
            profile, error = resolve_current_profile()
            if error:
                return error
            if profile.get("role") not in accepted:
                return error_response("Forbidden", 403)
            g.current_profile = profile
            return handler(*args, **kwargs)

        return wrapped

    return decorator


def get_tier_limits(tier: str | None):
    if tier == "pro":
        return {"posts_per_month": None, "promoted_per_month": 2}
    if tier == "platinum":
        return {"posts_per_month": None, "promoted_per_month": 10}
    return {"posts_per_month": 5, "promoted_per_month": 0}
