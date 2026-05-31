from flask import Blueprint, g, jsonify, request

from src.authz import require_auth
from src.supabase_client import get_supabase_client
from src.utils import error_response, normalize_record


messages_bp = Blueprint("messages", __name__)


def _participant_ids(conversation_id: int):
    supabase = get_supabase_client()
    participants_resp = (
        supabase.table("conversation_participants")
        .select("profile_id")
        .eq("conversation_id", conversation_id)
        .execute()
    )
    return [row["profile_id"] for row in (participants_resp.data or [])]


def _ensure_conversation_member(conversation_id: int, profile_id: int):
    ids = _participant_ids(conversation_id)
    return profile_id in ids


def _account_type_from_role(role: str | None) -> str:
    mapping = {"user": "client", "contractor": "contractor_company", "admin": "admin"}
    return mapping.get((role or "").strip().lower(), "client")


@messages_bp.route("/messages/conversations", methods=["GET"])
@require_auth
def get_conversations():
    try:
        supabase = get_supabase_client()
        participant_rows = (
            supabase.table("conversation_participants")
            .select("conversation_id")
            .eq("profile_id", g.current_profile["id"])
            .execute()
        )
        conversation_ids = [row["conversation_id"] for row in (participant_rows.data or [])]
        if not conversation_ids:
            return jsonify({"conversations": []})

        conversations_resp = (
            supabase.table("conversations")
            .select("*")
            .in_("id", conversation_ids)
            .order("updated_at", desc=True)
            .execute()
        )
        conversations = [normalize_record(item) for item in (conversations_resp.data or [])]

        all_participants = (
            supabase.table("conversation_participants")
            .select("*")
            .in_("conversation_id", conversation_ids)
            .execute()
        )
        profile_ids = list({row["profile_id"] for row in (all_participants.data or [])})
        profiles_resp = supabase.table("profiles").select("*").in_("id", profile_ids).execute() if profile_ids else None
        profiles_map = {row["id"]: normalize_record(row) for row in (profiles_resp.data or [])} if profiles_resp else {}

        participants_by_conv = {}
        for row in all_participants.data or []:
            participants_by_conv.setdefault(row["conversation_id"], []).append(profiles_map.get(row["profile_id"]))

        for convo in conversations:
            convo["participants"] = participants_by_conv.get(convo["id"], [])

        return jsonify({"conversations": conversations})
    except Exception as exc:
        return error_response(str(exc), 500)


@messages_bp.route("/messages/conversations", methods=["POST"])
@require_auth
def create_conversation():
    try:
        data = request.get_json(silent=True) or {}
        conversation_type = (data.get("conversation_type") or "direct").strip().lower()
        participant_ids = data.get("participant_profile_ids") or []
        project_id = data.get("project_id")

        if conversation_type not in {"direct", "project"}:
            return error_response("conversation_type must be direct or project")
        if not isinstance(participant_ids, list):
            return error_response("participant_profile_ids must be an array")

        resolved_ids = set(int(pid) for pid in participant_ids if pid)
        resolved_ids.add(int(g.current_profile["id"]))
        if conversation_type == "direct" and len(resolved_ids) != 2:
            return error_response("Direct conversations must include exactly two participants")

        supabase = get_supabase_client()
        if conversation_type == "direct":
            profile_resp = supabase.table("profiles").select("*").in_("id", list(resolved_ids)).execute()
            profiles = [normalize_record(item) for item in (profile_resp.data or [])]
            if len(profiles) != 2:
                return error_response("Participant profile not found", 404)
            participant_types = {_account_type_from_role(item.get("role")) for item in profiles}
            if participant_types != {"client", "contractor_company"}:
                return error_response("Direct messaging is only available between clients and contractors", 403)

            a, b = sorted([int(item["id"]) for item in profiles])
            access_filter = (
                f"and(requester_profile_id.eq.{a},target_profile_id.eq.{b},status.eq.accepted),"
                f"and(requester_profile_id.eq.{b},target_profile_id.eq.{a},status.eq.accepted)"
            )
            access_resp = (
                supabase.table("profile_access_requests")
                .select("id")
                .or_(access_filter)
                .limit(1)
                .execute()
            )
            if not access_resp.data:
                return error_response("Accepted profile access request required before direct messaging", 403)

        created = (
            supabase.table("conversations")
            .insert({"conversation_type": conversation_type, "project_id": project_id})
            .execute()
        )
        if not created.data:
            return error_response("Failed to create conversation", 500)
        conversation = created.data[0]

        participant_rows = [
            {"conversation_id": conversation["id"], "profile_id": profile_id}
            for profile_id in resolved_ids
        ]
        supabase.table("conversation_participants").insert(participant_rows).execute()

        return jsonify({"conversation": normalize_record(conversation)}), 201
    except Exception as exc:
        return error_response(str(exc), 500)


@messages_bp.route("/messages/conversations/<int:conversation_id>/messages", methods=["GET"])
@require_auth
def get_messages(conversation_id):
    try:
        if not _ensure_conversation_member(conversation_id, int(g.current_profile["id"])):
            return error_response("Forbidden", 403)

        supabase = get_supabase_client()
        messages_resp = (
            supabase.table("messages")
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=False)
            .execute()
        )
        messages = [normalize_record(item) for item in (messages_resp.data or [])]

        profile_ids = list({msg["sender_profile_id"] for msg in messages})
        profiles_resp = supabase.table("profiles").select("*").in_("id", profile_ids).execute() if profile_ids else None
        profiles_map = {item["id"]: normalize_record(item) for item in (profiles_resp.data or [])} if profiles_resp else {}
        for msg in messages:
            msg["sender"] = profiles_map.get(msg["sender_profile_id"])

        return jsonify({"messages": messages})
    except Exception as exc:
        return error_response(str(exc), 500)


@messages_bp.route("/messages/conversations/<int:conversation_id>/messages", methods=["POST"])
@require_auth
def create_message(conversation_id):
    try:
        if not _ensure_conversation_member(conversation_id, int(g.current_profile["id"])):
            return error_response("Forbidden", 403)

        data = request.get_json(silent=True) or {}
        content = (data.get("content") or "").strip()
        if not content:
            return error_response("content is required")

        supabase = get_supabase_client()
        created = (
            supabase.table("messages")
            .insert(
                {
                    "conversation_id": conversation_id,
                    "sender_profile_id": g.current_profile["id"],
                    "content": content,
                }
            )
            .execute()
        )
        if not created.data:
            return error_response("Failed to send message", 500)

        return jsonify({"message": normalize_record(created.data[0])}), 201
    except Exception as exc:
        return error_response(str(exc), 500)


@messages_bp.route("/projects/<int:project_id>/thread", methods=["GET"])
@require_auth
def get_or_create_project_thread(project_id):
    try:
        supabase = get_supabase_client()
        existing = (
            supabase.table("conversations")
            .select("*")
            .eq("conversation_type", "project")
            .eq("project_id", project_id)
            .limit(1)
            .execute()
        )
        if existing.data:
            return jsonify({"conversation": normalize_record(existing.data[0])})

        project_resp = supabase.table("projects").select("id").eq("id", project_id).limit(1).execute()
        if not project_resp.data:
            return error_response("Project not found", 404)

        created = (
            supabase.table("conversations")
            .insert({"conversation_type": "project", "project_id": project_id})
            .execute()
        )
        conversation = created.data[0]
        supabase.table("conversation_participants").insert(
            [{"conversation_id": conversation["id"], "profile_id": g.current_profile["id"]}]
        ).execute()

        return jsonify({"conversation": normalize_record(conversation)}), 201
    except Exception as exc:
        return error_response(str(exc), 500)
