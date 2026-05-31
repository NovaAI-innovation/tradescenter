from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request

from src.authz import require_auth
from src.supabase_client import get_supabase_client
from src.utils import error_response, normalize_record


profile_access_bp = Blueprint("profile_access", __name__)


def _fetch_profiles(profile_ids: list[int]) -> dict[int, dict]:
    if not profile_ids:
        return {}
    supabase = get_supabase_client()
    resp = supabase.table("profiles").select("*").in_("id", profile_ids).execute()
    return {item["id"]: normalize_record(item) for item in (resp.data or [])}


@profile_access_bp.route("/profile-access/requests", methods=["POST"])
@require_auth
def create_profile_access_request():
    try:
        data = request.get_json(silent=True) or {}
        target_profile_id = data.get("target_profile_id")
        if not target_profile_id:
            return error_response("target_profile_id is required")
        try:
            target_profile_id = int(target_profile_id)
        except (TypeError, ValueError):
            return error_response("target_profile_id must be an integer")

        requester_profile_id = int(g.current_profile["id"])
        if target_profile_id == requester_profile_id:
            return error_response("You cannot request access to your own profile")

        supabase = get_supabase_client()
        target = supabase.table("profiles").select("id").eq("id", target_profile_id).limit(1).execute()
        if not target.data:
            return error_response("Target profile not found", 404)

        existing_pending = (
            supabase.table("profile_access_requests")
            .select("*")
            .eq("requester_profile_id", requester_profile_id)
            .eq("target_profile_id", target_profile_id)
            .eq("status", "pending")
            .limit(1)
            .execute()
        )
        if existing_pending.data:
            return jsonify({"request": normalize_record(existing_pending.data[0]), "already_pending": True})

        created = (
            supabase.table("profile_access_requests")
            .insert(
                {
                    "requester_profile_id": requester_profile_id,
                    "target_profile_id": target_profile_id,
                    "status": "pending",
                }
            )
            .execute()
        )
        if not created.data:
            return error_response("Failed to create access request", 500)
        return jsonify({"request": normalize_record(created.data[0])}), 201
    except Exception as exc:
        return error_response(str(exc), 500)


@profile_access_bp.route("/profile-access/requests", methods=["GET"])
@require_auth
def list_profile_access_requests():
    try:
        scope = (request.args.get("scope") or "inbox").strip().lower()
        status = (request.args.get("status") or "").strip().lower()
        if scope not in {"inbox", "sent"}:
            return error_response("scope must be inbox or sent")
        if status and status not in {"pending", "accepted", "declined"}:
            return error_response("Invalid status")

        supabase = get_supabase_client()
        query = supabase.table("profile_access_requests").select("*")
        profile_id = int(g.current_profile["id"])
        if scope == "inbox":
            query = query.eq("target_profile_id", profile_id)
        else:
            query = query.eq("requester_profile_id", profile_id)
        if status:
            query = query.eq("status", status)
        response = query.order("created_at", desc=True).limit(200).execute()
        rows = [normalize_record(item) for item in (response.data or [])]

        ids = list(
            {
                item["requester_profile_id"]
                for item in rows
                if item.get("requester_profile_id") is not None
            }
            | {
                item["target_profile_id"]
                for item in rows
                if item.get("target_profile_id") is not None
            }
        )
        profiles = _fetch_profiles(ids)
        for item in rows:
            item["requester_profile"] = profiles.get(item.get("requester_profile_id"))
            item["target_profile"] = profiles.get(item.get("target_profile_id"))

        return jsonify({"requests": rows})
    except Exception as exc:
        return error_response(str(exc), 500)


@profile_access_bp.route("/profile-access/requests/<int:request_id>/respond", methods=["POST"])
@require_auth
def respond_profile_access_request(request_id: int):
    try:
        data = request.get_json(silent=True) or {}
        action = (data.get("action") or "").strip().lower()
        if action not in {"accept", "decline"}:
            return error_response("action must be accept or decline")

        supabase = get_supabase_client()
        existing = (
            supabase.table("profile_access_requests")
            .select("*")
            .eq("id", request_id)
            .limit(1)
            .execute()
        )
        if not existing.data:
            return error_response("Request not found", 404)
        current = normalize_record(existing.data[0])

        if int(current["target_profile_id"]) != int(g.current_profile["id"]):
            return error_response("Forbidden", 403)
        if current.get("status") != "pending":
            return error_response("Only pending requests can be updated", 400)

        new_status = "accepted" if action == "accept" else "declined"
        updated = (
            supabase.table("profile_access_requests")
            .update(
                {
                    "status": new_status,
                    "responded_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            .eq("id", request_id)
            .execute()
        )
        if not updated.data:
            return error_response("Failed to update request", 500)

        return jsonify({"request": normalize_record(updated.data[0])})
    except Exception as exc:
        return error_response(str(exc), 500)


@profile_access_bp.route("/profile-access/allowed/<int:target_profile_id>", methods=["GET"])
@require_auth
def has_profile_access(target_profile_id: int):
    try:
        if int(target_profile_id) == int(g.current_profile["id"]):
            return jsonify({"allowed": True})

        supabase = get_supabase_client()
        granted = (
            supabase.table("profile_access_requests")
            .select("id")
            .eq("requester_profile_id", g.current_profile["id"])
            .eq("target_profile_id", target_profile_id)
            .eq("status", "accepted")
            .limit(1)
            .execute()
        )
        return jsonify({"allowed": bool(granted.data)})
    except Exception as exc:
        return error_response(str(exc), 500)
