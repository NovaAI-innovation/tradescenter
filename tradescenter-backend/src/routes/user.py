from flask import Blueprint, jsonify, request

from src.supabase_client import get_supabase_client
from src.utils import error_response, normalize_record


user_bp = Blueprint("user", __name__)


@user_bp.route("/users", methods=["GET"])
def get_users():
    try:
        supabase = get_supabase_client()
        response = supabase.table("users").select("*").order("created_at", desc=True).execute()
        users = [normalize_record(user) for user in response.data or []]
        return jsonify(users)
    except Exception as exc:
        return error_response(str(exc), 500)


@user_bp.route("/users", methods=["POST"])
def create_user():
    try:
        data = request.get_json(silent=True) or {}

        required = ["email", "first_name", "last_name", "user_type"]
        for field in required:
            if not data.get(field):
                return error_response(f"Missing required field: {field}")

        payload = {
            "email": data["email"],
            "first_name": data["first_name"],
            "last_name": data["last_name"],
            "phone": data.get("phone"),
            "user_type": data.get("user_type", "homeowner"),
            "profile_image": data.get("profile_image"),
            "bio": data.get("bio"),
            "location": data.get("location"),
            "is_verified": bool(data.get("is_verified", False)),
            "is_active": bool(data.get("is_active", True)),
            "email_verified": bool(data.get("email_verified", False)),
        }

        supabase = get_supabase_client()
        created = supabase.table("users").insert(payload).execute()
        if not created.data:
            return error_response("Failed to create user", 500)

        return jsonify(normalize_record(created.data[0])), 201
    except Exception as exc:
        return error_response(str(exc), 500)


@user_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    try:
        supabase = get_supabase_client()
        response = supabase.table("users").select("*").eq("id", user_id).limit(1).execute()
        if not response.data:
            return error_response("User not found", 404)
        return jsonify(normalize_record(response.data[0]))
    except Exception as exc:
        return error_response(str(exc), 500)


@user_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    try:
        data = request.get_json(silent=True) or {}
        allowed = {
            "email",
            "first_name",
            "last_name",
            "phone",
            "user_type",
            "profile_image",
            "bio",
            "location",
            "is_verified",
            "is_active",
            "email_verified",
            "last_login",
        }

        payload = {key: value for key, value in data.items() if key in allowed}
        if not payload:
            return error_response("No valid fields provided for update")

        supabase = get_supabase_client()
        updated = supabase.table("users").update(payload).eq("id", user_id).execute()
        if not updated.data:
            return error_response("User not found", 404)

        return jsonify(normalize_record(updated.data[0]))
    except Exception as exc:
        return error_response(str(exc), 500)


@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    try:
        supabase = get_supabase_client()
        deleted = supabase.table("users").delete().eq("id", user_id).execute()
        if not deleted.data:
            return error_response("User not found", 404)
        return "", 204
    except Exception as exc:
        return error_response(str(exc), 500)

