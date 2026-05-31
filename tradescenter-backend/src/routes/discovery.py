from flask import Blueprint, jsonify, request

from src.supabase_client import get_supabase_client
from src.utils import error_response, normalize_record, parse_int


discovery_bp = Blueprint("discovery", __name__)


@discovery_bp.route("/indexed-users", methods=["GET"])
def get_indexed_users():
    try:
        page = parse_int(request.args.get("page"), 1)
        per_page = parse_int(request.args.get("per_page"), 20)
        role = (request.args.get("role") or "").strip().lower()
        verified_only = (request.args.get("verified") or "").strip().lower() == "true"
        query_text = (request.args.get("q") or "").strip()

        supabase = get_supabase_client()
        query = supabase.table("indexed_users").select("*", count="exact")
        if role in {"client", "contractor_company", "admin"}:
            query = query.eq("role", role)
        if verified_only:
            query = query.eq("is_verified", True)
        if query_text:
            query = query.ilike("searchable_text", f"%{query_text}%")

        start = (page - 1) * per_page
        end = start + per_page - 1
        response = query.order("updated_at", desc=True).range(start, end).execute()
        records = [normalize_record(item) for item in (response.data or [])]
        total = response.count or 0
        pages = (total + per_page - 1) // per_page if per_page > 0 else 0

        return jsonify(
            {
                "users": records,
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
