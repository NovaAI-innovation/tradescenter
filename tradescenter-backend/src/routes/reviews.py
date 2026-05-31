from flask import Blueprint, jsonify, request

from src.supabase_client import get_supabase_client
from src.utils import error_response, normalize_record, parse_int


reviews_bp = Blueprint("reviews", __name__)


def _attach_review_relationships(reviews: list[dict]) -> list[dict]:
    if not reviews:
        return []

    supabase = get_supabase_client()
    client_ids = list({review["client_id"] for review in reviews if review.get("client_id")})
    contractor_ids = list({review["contractor_id"] for review in reviews if review.get("contractor_id")})
    project_ids = list({review["project_id"] for review in reviews if review.get("project_id")})
    review_ids = [review["id"] for review in reviews]

    clients_resp = supabase.table("users").select("*").in_("id", client_ids).execute() if client_ids else None
    contractors_resp = (
        supabase.table("contractors").select("*").in_("id", contractor_ids).execute() if contractor_ids else None
    )
    projects_resp = supabase.table("projects").select("*").in_("id", project_ids).execute() if project_ids else None
    responses_resp = (
        supabase.table("review_responses").select("*").in_("review_id", review_ids).execute() if review_ids else None
    )

    clients = {item["id"]: normalize_record(item) for item in (clients_resp.data or [])} if clients_resp else {}
    contractors = {
        item["id"]: normalize_record(item) for item in (contractors_resp.data or [])
    } if contractors_resp else {}
    projects = {item["id"]: normalize_record(item) for item in (projects_resp.data or [])} if projects_resp else {}
    responses = {
        item["review_id"]: normalize_record(item) for item in (responses_resp.data or [])
    } if responses_resp else {}

    merged = []
    for review in reviews:
        enriched = normalize_record(review)
        enriched["client"] = clients.get(review.get("client_id"))
        enriched["contractor"] = contractors.get(review.get("contractor_id"))
        enriched["project"] = projects.get(review.get("project_id"))
        if responses.get(review["id"]):
            enriched["response"] = responses[review["id"]]
        merged.append(enriched)
    return merged


def _update_contractor_rating(contractor_id: int):
    supabase = get_supabase_client()
    reviews_resp = supabase.table("reviews").select("rating").eq("contractor_id", contractor_id).execute()
    ratings = [review["rating"] for review in (reviews_resp.data or []) if review.get("rating") is not None]
    count = len(ratings)
    average = round(sum(ratings) / count, 1) if count > 0 else 0
    supabase.table("contractors").update({"rating": average, "total_reviews": count}).eq("id", contractor_id).execute()


@reviews_bp.route("/reviews", methods=["GET"])
def get_reviews():
    try:
        page = parse_int(request.args.get("page"), 1)
        per_page = parse_int(request.args.get("per_page"), 12)
        contractor_id = request.args.get("contractor_id", type=int)
        client_id = request.args.get("client_id", type=int)
        min_rating = parse_int(request.args.get("min_rating"), 0)

        supabase = get_supabase_client()
        query = supabase.table("reviews").select("*", count="exact")

        if contractor_id:
            query = query.eq("contractor_id", contractor_id)
        if client_id:
            query = query.eq("client_id", client_id)
        if min_rating > 0:
            query = query.gte("rating", min_rating)

        start = (page - 1) * per_page
        end = start + per_page - 1
        response = query.order("created_at", desc=True).range(start, end).execute()

        reviews = _attach_review_relationships(response.data or [])
        total = response.count or 0
        pages = (total + per_page - 1) // per_page if per_page > 0 else 0

        return jsonify(
            {
                "reviews": reviews,
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


@reviews_bp.route("/reviews/<int:review_id>", methods=["GET"])
def get_review(review_id):
    try:
        supabase = get_supabase_client()
        review_resp = supabase.table("reviews").select("*").eq("id", review_id).limit(1).execute()
        if not review_resp.data:
            return error_response("Review not found", 404)
        return jsonify(_attach_review_relationships([review_resp.data[0]])[0])
    except Exception as exc:
        return error_response(str(exc), 500)


@reviews_bp.route("/reviews", methods=["POST"])
def create_review():
    try:
        data = request.get_json(silent=True) or {}
        required = ["project_id", "contractor_id", "client_id", "rating"]
        for field in required:
            if field not in data:
                return error_response(f"Missing required field: {field}")

        rating = int(data["rating"])
        if rating < 1 or rating > 5:
            return error_response("Rating must be between 1 and 5")

        supabase = get_supabase_client()

        project_resp = supabase.table("projects").select("id").eq("id", data["project_id"]).limit(1).execute()
        contractor_resp = (
            supabase.table("contractors").select("id").eq("id", data["contractor_id"]).limit(1).execute()
        )
        client_resp = supabase.table("users").select("id").eq("id", data["client_id"]).limit(1).execute()
        existing_review = (
            supabase.table("reviews").select("id").eq("project_id", data["project_id"]).limit(1).execute()
        )

        if not project_resp.data:
            return error_response("Project not found", 404)
        if not contractor_resp.data:
            return error_response("Contractor not found", 404)
        if not client_resp.data:
            return error_response("Client not found", 404)
        if existing_review.data:
            return error_response("Review already exists for this project")

        detail_fields = [
            "quality_rating",
            "communication_rating",
            "timeliness_rating",
            "professionalism_rating",
            "value_rating",
        ]
        for field in detail_fields:
            if data.get(field) is not None:
                score = int(data[field])
                if score < 1 or score > 5:
                    return error_response(f"{field} must be between 1 and 5")

        payload = {
            "project_id": data["project_id"],
            "contractor_id": data["contractor_id"],
            "client_id": data["client_id"],
            "rating": rating,
            "title": data.get("title"),
            "comment": data.get("comment"),
            "quality_rating": data.get("quality_rating"),
            "communication_rating": data.get("communication_rating"),
            "timeliness_rating": data.get("timeliness_rating"),
            "professionalism_rating": data.get("professionalism_rating"),
            "value_rating": data.get("value_rating"),
            "verified_project": bool(data.get("verified_project", False)),
        }

        created = supabase.table("reviews").insert(payload).execute()
        if not created.data:
            return error_response("Failed to create review", 500)

        _update_contractor_rating(data["contractor_id"])
        return jsonify(_attach_review_relationships([created.data[0]])[0]), 201
    except Exception as exc:
        return error_response(str(exc), 500)


@reviews_bp.route("/reviews/<int:review_id>/response", methods=["POST"])
def create_review_response(review_id):
    try:
        data = request.get_json(silent=True) or {}
        if not data.get("response_text"):
            return error_response("Missing required field: response_text")
        if not data.get("contractor_id"):
            return error_response("Missing required field: contractor_id")

        supabase = get_supabase_client()
        review_resp = supabase.table("reviews").select("*").eq("id", review_id).limit(1).execute()
        if not review_resp.data:
            return error_response("Review not found", 404)

        review = review_resp.data[0]
        contractor_resp = (
            supabase.table("contractors").select("id").eq("id", data["contractor_id"]).limit(1).execute()
        )
        if not contractor_resp.data:
            return error_response("Contractor not found", 404)
        if int(review["contractor_id"]) != int(data["contractor_id"]):
            return error_response("Contractor can only respond to their own reviews", 403)

        existing_resp = (
            supabase.table("review_responses").select("id").eq("review_id", review_id).limit(1).execute()
        )
        if existing_resp.data:
            return error_response("Response already exists for this review")

        created = (
            supabase.table("review_responses")
            .insert(
                {
                    "review_id": review_id,
                    "contractor_id": data["contractor_id"],
                    "response_text": data["response_text"],
                }
            )
            .execute()
        )
        if not created.data:
            return error_response("Failed to create response", 500)

        return jsonify(normalize_record(created.data[0])), 201
    except Exception as exc:
        return error_response(str(exc), 500)


@reviews_bp.route("/contractors/<int:contractor_id>/rating-summary", methods=["GET"])
def get_contractor_rating_summary(contractor_id):
    try:
        supabase = get_supabase_client()
        contractor_resp = supabase.table("contractors").select("*").eq("id", contractor_id).limit(1).execute()
        if not contractor_resp.data:
            return error_response("Contractor not found", 404)

        reviews_resp = supabase.table("reviews").select("*").eq("contractor_id", contractor_id).execute()
        reviews = reviews_resp.data or []

        distribution = {str(i): 0 for i in range(1, 6)}
        quality = []
        communication = []
        timeliness = []
        professionalism = []
        value = []

        for review in reviews:
            rating = int(review.get("rating", 0))
            if 1 <= rating <= 5:
                distribution[str(rating)] += 1
            if review.get("quality_rating"):
                quality.append(review["quality_rating"])
            if review.get("communication_rating"):
                communication.append(review["communication_rating"])
            if review.get("timeliness_rating"):
                timeliness.append(review["timeliness_rating"])
            if review.get("professionalism_rating"):
                professionalism.append(review["professionalism_rating"])
            if review.get("value_rating"):
                value.append(review["value_rating"])

        def avg(values):
            return round(sum(values) / len(values), 1) if values else 0

        contractor = contractor_resp.data[0]
        return jsonify(
            {
                "contractor_id": contractor_id,
                "overall_rating": contractor.get("rating", 0),
                "total_reviews": contractor.get("total_reviews", 0),
                "rating_distribution": distribution,
                "detailed_ratings": {
                    "quality": avg(quality),
                    "communication": avg(communication),
                    "timeliness": avg(timeliness),
                    "professionalism": avg(professionalism),
                    "value": avg(value),
                },
            }
        )
    except Exception as exc:
        return error_response(str(exc), 500)

