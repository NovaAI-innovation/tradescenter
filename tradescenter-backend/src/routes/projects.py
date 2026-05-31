from datetime import datetime

from flask import Blueprint, jsonify, request

from src.supabase_client import get_supabase_client
from src.utils import error_response, normalize_record, parse_int


projects_bp = Blueprint("projects", __name__)


def _attach_project_relationships(projects: list[dict]) -> list[dict]:
    if not projects:
        return []

    supabase = get_supabase_client()
    client_ids = list({project["client_id"] for project in projects if project.get("client_id")})
    contractor_ids = list({project["contractor_id"] for project in projects if project.get("contractor_id")})

    clients_resp = supabase.table("users").select("*").in_("id", client_ids).execute() if client_ids else None
    contractors_resp = (
        supabase.table("contractors").select("*").in_("id", contractor_ids).execute()
        if contractor_ids
        else None
    )

    clients = {record["id"]: normalize_record(record) for record in (clients_resp.data or [])} if clients_resp else {}
    contractors = {
        record["id"]: normalize_record(record) for record in (contractors_resp.data or [])
    } if contractors_resp else {}

    merged = []
    for project in projects:
        enriched = normalize_record(project)
        enriched["client"] = clients.get(project.get("client_id"))
        if project.get("contractor_id"):
            enriched["contractor"] = contractors.get(project.get("contractor_id"))
        merged.append(enriched)
    return merged


@projects_bp.route("/projects", methods=["GET"])
def get_projects():
    try:
        page = parse_int(request.args.get("page"), 1)
        per_page = parse_int(request.args.get("per_page"), 12)
        status = request.args.get("status", "").strip()
        category = request.args.get("category", "").strip()
        location = request.args.get("location", "").strip()
        client_id = request.args.get("client_id", type=int)
        contractor_id = request.args.get("contractor_id", type=int)

        supabase = get_supabase_client()
        query = supabase.table("projects").select("*", count="exact")

        if status:
            query = query.eq("status", status)
        if category:
            query = query.eq("category", category)
        if location:
            query = query.ilike("location", f"%{location}%")
        if client_id:
            query = query.eq("client_id", client_id)
        if contractor_id:
            query = query.eq("contractor_id", contractor_id)

        start = (page - 1) * per_page
        end = start + per_page - 1
        response = query.order("created_at", desc=True).range(start, end).execute()

        projects = _attach_project_relationships(response.data or [])
        total = response.count or 0
        pages = (total + per_page - 1) // per_page if per_page > 0 else 0

        return jsonify(
            {
                "projects": projects,
                "pagination": {
                    "page": page,
                    "pages": pages,
                    "per_page": per_page,
                    "total": total,
                    "has_next": page < pages,
                    "has_prev": page > 1,
                },
            }
        )
    except Exception as exc:
        return error_response(str(exc), 500)


@projects_bp.route("/projects/<int:project_id>", methods=["GET"])
def get_project(project_id):
    try:
        supabase = get_supabase_client()
        project_resp = supabase.table("projects").select("*").eq("id", project_id).limit(1).execute()
        if not project_resp.data:
            return error_response("Project not found", 404)

        project = _attach_project_relationships([project_resp.data[0]])[0]
        milestones_resp = (
            supabase.table("project_milestones")
            .select("*")
            .eq("project_id", project_id)
            .order("order_index", desc=False)
            .execute()
        )
        files_resp = (
            supabase.table("project_files")
            .select("*")
            .eq("project_id", project_id)
            .order("created_at", desc=True)
            .execute()
        )

        project["milestones"] = [normalize_record(item) for item in (milestones_resp.data or [])]
        project["files"] = [normalize_record(item) for item in (files_resp.data or [])]
        return jsonify(project)
    except Exception as exc:
        return error_response(str(exc), 500)


@projects_bp.route("/projects", methods=["POST"])
def create_project():
    try:
        data = request.get_json(silent=True) or {}
        required = ["client_id", "title", "description", "category", "location"]
        for field in required:
            if not data.get(field):
                return error_response(f"Missing required field: {field}")

        supabase = get_supabase_client()
        client_resp = supabase.table("users").select("id").eq("id", data["client_id"]).limit(1).execute()
        if not client_resp.data:
            return error_response("Client not found", 404)

        start_date = data.get("start_date")
        end_date = data.get("end_date")
        if start_date:
            datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            datetime.strptime(end_date, "%Y-%m-%d")

        payload = {
            "client_id": data["client_id"],
            "contractor_id": data.get("contractor_id"),
            "title": data["title"],
            "description": data["description"],
            "category": data["category"],
            "location": data["location"],
            "budget_min": data.get("budget_min"),
            "budget_max": data.get("budget_max"),
            "status": data.get("status", "open"),
            "priority": data.get("priority", "medium"),
            "start_date": start_date,
            "end_date": end_date,
            "completion_date": data.get("completion_date"),
        }

        created = supabase.table("projects").insert(payload).execute()
        if not created.data:
            return error_response("Failed to create project", 500)
        return jsonify(_attach_project_relationships([created.data[0]])[0]), 201
    except ValueError:
        return error_response("Dates must use YYYY-MM-DD format")
    except Exception as exc:
        return error_response(str(exc), 500)


@projects_bp.route("/projects/<int:project_id>", methods=["PUT"])
def update_project(project_id):
    try:
        data = request.get_json(silent=True) or {}
        allowed = {
            "title",
            "description",
            "category",
            "location",
            "budget_min",
            "budget_max",
            "status",
            "priority",
            "contractor_id",
            "start_date",
            "end_date",
            "completion_date",
        }
        payload = {key: value for key, value in data.items() if key in allowed}
        if not payload:
            return error_response("No valid fields provided for update")

        for date_field in ("start_date", "end_date", "completion_date"):
            if payload.get(date_field):
                datetime.strptime(payload[date_field], "%Y-%m-%d")

        supabase = get_supabase_client()
        updated = supabase.table("projects").update(payload).eq("id", project_id).execute()
        if not updated.data:
            return error_response("Project not found", 404)
        return jsonify(_attach_project_relationships([updated.data[0]])[0])
    except ValueError:
        return error_response("Dates must use YYYY-MM-DD format")
    except Exception as exc:
        return error_response(str(exc), 500)


@projects_bp.route("/projects/<int:project_id>/milestones", methods=["POST"])
def create_milestone(project_id):
    try:
        data = request.get_json(silent=True) or {}
        if not data.get("title"):
            return error_response("Missing required field: title")

        supabase = get_supabase_client()
        project_resp = supabase.table("projects").select("id").eq("id", project_id).limit(1).execute()
        if not project_resp.data:
            return error_response("Project not found", 404)

        order_resp = (
            supabase.table("project_milestones")
            .select("order_index")
            .eq("project_id", project_id)
            .order("order_index", desc=True)
            .limit(1)
            .execute()
        )
        max_order = order_resp.data[0]["order_index"] if order_resp.data else 0

        payload = {
            "project_id": project_id,
            "title": data["title"],
            "description": data.get("description"),
            "status": data.get("status", "pending"),
            "due_date": data.get("due_date"),
            "completion_date": data.get("completion_date"),
            "order_index": max_order + 1,
        }

        created = supabase.table("project_milestones").insert(payload).execute()
        if not created.data:
            return error_response("Failed to create milestone", 500)
        return jsonify(normalize_record(created.data[0])), 201
    except Exception as exc:
        return error_response(str(exc), 500)


@projects_bp.route("/projects/search", methods=["GET"])
def search_projects():
    try:
        query_text = request.args.get("q", "").strip()
        location = request.args.get("location", "").strip()
        category = request.args.get("category", "").strip()
        status = request.args.get("status", "").strip()
        page = parse_int(request.args.get("page"), 1)
        per_page = parse_int(request.args.get("per_page"), 12)

        if not query_text:
            return error_response("Search query is required")

        start = (page - 1) * per_page
        end = start + per_page - 1

        supabase = get_supabase_client()
        query = (
            supabase.table("projects")
            .select("*", count="exact")
            .or_(f"title.ilike.%{query_text}%,description.ilike.%{query_text}%")
        )

        if location:
            query = query.ilike("location", f"%{location}%")
        if category:
            query = query.eq("category", category)
        if status:
            query = query.eq("status", status)

        response = query.order("created_at", desc=True).range(start, end).execute()
        projects = _attach_project_relationships(response.data or [])
        total = response.count or 0
        pages = (total + per_page - 1) // per_page if per_page > 0 else 0

        return jsonify(
            {
                "projects": projects,
                "pagination": {
                    "page": page,
                    "pages": pages,
                    "per_page": per_page,
                    "total": total,
                    "has_next": page < pages,
                    "has_prev": page > 1,
                },
            }
        )
    except Exception as exc:
        return error_response(str(exc), 500)

