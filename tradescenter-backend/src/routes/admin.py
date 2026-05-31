from flask import Blueprint, jsonify, request

from src.authz import ALLOWED_TIERS, require_roles
from src.supabase_client import get_supabase_client
from src.utils import error_response, normalize_record


admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/moderation", methods=["GET"])
@require_roles("admin")
def moderation_overview():
    try:
        supabase = get_supabase_client()
        recent_posts = (
            supabase.table("posts")
            .select("*")
            .order("created_at", desc=True)
            .limit(30)
            .execute()
        )
        recent_comments = (
            supabase.table("comments")
            .select("*")
            .order("created_at", desc=True)
            .limit(30)
            .execute()
        )
        suspended_users = (
            supabase.table("profiles")
            .select("*")
            .eq("is_suspended", True)
            .order("updated_at", desc=True)
            .execute()
        )
        return jsonify(
            {
                "recent_posts": [normalize_record(item) for item in (recent_posts.data or [])],
                "recent_comments": [normalize_record(item) for item in (recent_comments.data or [])],
                "suspended_users": [normalize_record(item) for item in (suspended_users.data or [])],
            }
        )
    except Exception as exc:
        return error_response(str(exc), 500)


@admin_bp.route("/admin/moderation/action", methods=["POST"])
@require_roles("admin")
def moderation_action():
    try:
        data = request.get_json(silent=True) or {}
        action = (data.get("action") or "").strip().lower()
        target_type = (data.get("target_type") or "").strip().lower()
        target_id = data.get("target_id")

        if action not in {"delete", "suspend", "unsuspend", "set_tier"}:
            return error_response("Unsupported action")
        if target_type not in {"post", "comment", "profile"}:
            return error_response("Unsupported target_type")
        if not target_id:
            return error_response("target_id is required")

        supabase = get_supabase_client()
        if action == "delete" and target_type == "post":
            supabase.table("posts").update({"is_deleted": True}).eq("id", target_id).execute()
            return jsonify({"message": "Post deleted"})
        if action == "delete" and target_type == "comment":
            supabase.table("comments").update({"is_deleted": True}).eq("id", target_id).execute()
            return jsonify({"message": "Comment deleted"})
        if action in {"suspend", "unsuspend"} and target_type == "profile":
            suspended = action == "suspend"
            supabase.table("profiles").update({"is_suspended": suspended}).eq("id", target_id).execute()
            return jsonify({"message": "Profile suspension status updated"})
        if action == "set_tier" and target_type == "profile":
            tier = (data.get("tier") or "").strip().lower()
            if tier not in ALLOWED_TIERS:
                return error_response("tier must be free, pro, or platinum")
            profile_resp = (
                supabase.table("profiles")
                .select("id, role")
                .eq("id", target_id)
                .limit(1)
                .execute()
            )
            if not profile_resp.data:
                return error_response("Profile not found", 404)
            if profile_resp.data[0].get("role") != "contractor":
                return error_response("Tiers can only be assigned to contractor profiles", 400)
            updated = (
                supabase.table("profiles")
                .update({"contractor_tier": tier, "tier_status": "active"})
                .eq("id", target_id)
                .execute()
            )
            return jsonify({"message": "Tier updated", "profile": normalize_record(updated.data[0]) if updated.data else None})

        return error_response("Invalid action/target combination")
    except Exception as exc:
        return error_response(str(exc), 500)
