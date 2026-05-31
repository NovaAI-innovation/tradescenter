from flask import Blueprint, jsonify, request

from src.supabase_client import get_supabase_client
from src.utils import error_response, normalize_record, parse_int


contractors_bp = Blueprint("contractors", __name__)


def _attach_user_data(contractors: list[dict]) -> list[dict]:
    if not contractors:
        return []

    supabase = get_supabase_client()
    user_ids = list({contractor["user_id"] for contractor in contractors if contractor.get("user_id")})
    users_resp = supabase.table("users").select("*").in_("id", user_ids).execute() if user_ids else None
    users_map = {
        user["id"]: normalize_record(user) for user in (users_resp.data or [])
    } if users_resp else {}

    merged = []
    for contractor in contractors:
        enriched = normalize_record(contractor)
        enriched["user"] = users_map.get(contractor.get("user_id"))
        merged.append(enriched)
    return merged


@contractors_bp.route("/contractors", methods=["GET"])
def get_contractors():
    try:
        page = parse_int(request.args.get("page"), 1)
        per_page = parse_int(request.args.get("per_page"), 12)
        location = request.args.get("location", "").strip()
        category = request.args.get("category", "").strip()
        min_rating = float(request.args.get("min_rating", 0) or 0)
        verified_only = request.args.get("verified", "false").lower() == "true"

        supabase = get_supabase_client()
        query = supabase.table("contractors").select("*", count="exact")

        if location:
            query = query.contains("service_areas", [location])
        if category:
            query = query.contains("specialties", [category])
        if min_rating > 0:
            query = query.gte("rating", min_rating)
        if verified_only:
            query = query.eq("verified", True)

        start = (page - 1) * per_page
        end = start + per_page - 1

        response = (
            query.order("rating", desc=True)
            .order("total_reviews", desc=True)
            .range(start, end)
            .execute()
        )

        contractors = _attach_user_data(response.data or [])
        total = response.count or 0
        pages = (total + per_page - 1) // per_page if per_page > 0 else 0

        return jsonify(
            {
                "contractors": contractors,
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


@contractors_bp.route("/contractors/<int:contractor_id>", methods=["GET"])
def get_contractor(contractor_id):
    try:
        supabase = get_supabase_client()
        contractor_resp = supabase.table("contractors").select("*").eq("id", contractor_id).limit(1).execute()
        if not contractor_resp.data:
            return error_response("Contractor not found", 404)

        contractor = contractor_resp.data[0]
        enriched = _attach_user_data([contractor])[0]

        reviews_resp = (
            supabase.table("reviews")
            .select("*")
            .eq("contractor_id", contractor_id)
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )
        enriched["recent_reviews"] = [normalize_record(review) for review in (reviews_resp.data or [])]

        return jsonify(enriched)
    except Exception as exc:
        return error_response(str(exc), 500)


@contractors_bp.route("/contractors", methods=["POST"])
def create_contractor():
    try:
        data = request.get_json(silent=True) or {}
        required = ["user_id", "business_name", "description"]
        for field in required:
            if not data.get(field):
                return error_response(f"Missing required field: {field}")

        supabase = get_supabase_client()

        user_resp = supabase.table("users").select("id").eq("id", data["user_id"]).limit(1).execute()
        if not user_resp.data:
            return error_response("User not found", 404)

        existing = supabase.table("contractors").select("id").eq("user_id", data["user_id"]).limit(1).execute()
        if existing.data:
            return error_response("Contractor profile already exists for this user")

        payload = {
            "user_id": data["user_id"],
            "business_name": data["business_name"],
            "description": data["description"],
            "phone": data.get("phone"),
            "website": data.get("website"),
            "license_number": data.get("license_number"),
            "insurance_info": data.get("insurance_info"),
            "service_areas": data.get("service_areas", []),
            "specialties": data.get("specialties", []),
            "response_time_hours": data.get("response_time_hours", 24),
        }

        created = supabase.table("contractors").insert(payload).execute()
        if not created.data:
            return error_response("Failed to create contractor", 500)

        return jsonify(_attach_user_data([created.data[0]])[0]), 201
    except Exception as exc:
        return error_response(str(exc), 500)


@contractors_bp.route("/contractors/<int:contractor_id>", methods=["PUT"])
def update_contractor(contractor_id):
    try:
        data = request.get_json(silent=True) or {}
        allowed = {
            "business_name",
            "description",
            "phone",
            "website",
            "license_number",
            "insurance_info",
            "service_areas",
            "specialties",
            "response_time_hours",
            "verified",
            "rating",
            "total_reviews",
            "total_projects",
        }
        payload = {key: value for key, value in data.items() if key in allowed}
        if not payload:
            return error_response("No valid fields provided for update")

        supabase = get_supabase_client()
        updated = supabase.table("contractors").update(payload).eq("id", contractor_id).execute()
        if not updated.data:
            return error_response("Contractor not found", 404)

        return jsonify(_attach_user_data([updated.data[0]])[0])
    except Exception as exc:
        return error_response(str(exc), 500)


@contractors_bp.route("/contractors/featured", methods=["GET"])
def get_featured_contractors():
    try:
        supabase = get_supabase_client()
        response = (
            supabase.table("contractors")
            .select("*")
            .eq("verified", True)
            .gte("rating", 4.5)
            .gte("total_reviews", 5)
            .order("rating", desc=True)
            .order("total_reviews", desc=True)
            .limit(8)
            .execute()
        )
        return jsonify({"contractors": _attach_user_data(response.data or [])})
    except Exception as exc:
        return error_response(str(exc), 500)


@contractors_bp.route("/contractors/search", methods=["GET"])
def search_contractors():
    try:
        query_text = request.args.get("q", "").strip()
        location = request.args.get("location", "").strip()
        page = parse_int(request.args.get("page"), 1)
        per_page = parse_int(request.args.get("per_page"), 12)

        if not query_text:
            return error_response("Search query is required")

        start = (page - 1) * per_page
        end = start + per_page - 1

        supabase = get_supabase_client()
        query = (
            supabase.table("contractors")
            .select("*", count="exact")
            .or_(f"business_name.ilike.%{query_text}%,description.ilike.%{query_text}%")
        )

        if location:
            query = query.contains("service_areas", [location])

        response = query.order("rating", desc=True).order("total_reviews", desc=True).range(start, end).execute()
        contractors = _attach_user_data(response.data or [])
        total = response.count or 0
        pages = (total + per_page - 1) // per_page if per_page > 0 else 0

        return jsonify(
            {
                "contractors": contractors,
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

