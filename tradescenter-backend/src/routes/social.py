from datetime import datetime, timezone
import re

from flask import Blueprint, g, jsonify, request

from src.authz import get_tier_limits, require_auth
from src.supabase_client import get_supabase_client
from src.utils import error_response, normalize_record, parse_int


social_bp = Blueprint("social", __name__)

ALLOWED_POST_TYPES = {"promotion", "client_post", "tradescenter_news", "showcase"}
ALLOWED_REACTIONS = {"like", "heart", "applaud"}


def _account_type_from_role(role: str | None) -> str:
    mapping = {"user": "client", "contractor": "contractor_company", "admin": "admin"}
    return mapping.get((role or "").strip().lower(), "client")


def _current_month_window():
    now = datetime.now(timezone.utc)
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        next_month = start.replace(year=start.year + 1, month=1)
    else:
        next_month = start.replace(month=start.month + 1)
    return start.isoformat(), next_month.isoformat()


def _fetch_profiles_map(profile_ids: list[int]):
    if not profile_ids:
        return {}

    supabase = get_supabase_client()
    profiles_resp = supabase.table("profiles").select("*").in_("id", profile_ids).execute()
    profiles = [normalize_record(record) for record in (profiles_resp.data or [])]
    profiles_map = {record["id"]: record for record in profiles}

    accounts_resp = supabase.table("accounts").select("*").in_("profile_id", profile_ids).execute()
    accounts = [normalize_record(item) for item in (accounts_resp.data or [])]
    account_by_profile = {item["profile_id"]: item for item in accounts if item.get("profile_id") is not None}

    account_ids = [item["id"] for item in accounts if item.get("id") is not None]
    pages_map = {}
    if account_ids:
        pages_resp = supabase.table("profile_pages").select("*").in_("account_id", account_ids).execute()
        pages = [normalize_record(item) for item in (pages_resp.data or [])]
        pages_map = {item["account_id"]: item for item in pages}

    for profile_id, profile in profiles_map.items():
        account = account_by_profile.get(profile_id)
        profile["account"] = account
        profile["profile_page"] = pages_map.get(account["id"]) if account else None

    return profiles_map


def _safe_slug(label: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (label or "").strip().lower()).strip("-")
    return slug[:64]


def _is_paid_tier(post: dict) -> bool:
    author = post.get("author") or {}
    return author.get("role") == "contractor" and (author.get("contractor_tier") in {"pro", "platinum"})


def _is_showcase_candidate(post: dict) -> bool:
    if post.get("post_type") != "showcase":
        return False
    if not _is_paid_tier(post):
        return False
    before_count = sum(1 for media in (post.get("media") or []) if media.get("phase") == "before")
    after_count = sum(1 for media in (post.get("media") or []) if media.get("phase") == "after")
    return before_count >= 2 and after_count >= 2


def _enrich_posts(posts: list[dict], viewer_city: str | None = None):
    if not posts:
        return []

    supabase = get_supabase_client()
    post_ids = [post["id"] for post in posts]
    author_ids = list({post["author_profile_id"] for post in posts})

    media_resp = supabase.table("post_media").select("*").in_("post_id", post_ids).order("order_index").execute()
    comments_resp = supabase.table("comments").select("id,post_id").in_("post_id", post_ids).eq("is_deleted", False).execute()
    reactions_resp = (
        supabase.table("reactions")
        .select("target_id,reaction_type")
        .eq("target_type", "post")
        .in_("target_id", post_ids)
        .execute()
    )
    shares_resp = supabase.table("shares").select("post_id,share_type").in_("post_id", post_ids).execute()
    post_tags_resp = supabase.table("post_tags").select("*").in_("post_id", post_ids).execute()
    post_tagged_profiles_resp = (
        supabase.table("post_tagged_profiles")
        .select("*")
        .in_("post_id", post_ids)
        .execute()
    )

    tag_ids = list({item["tag_id"] for item in (post_tags_resp.data or [])})
    tags_resp = supabase.table("tags").select("*").in_("id", tag_ids).eq("is_active", True).execute() if tag_ids else None
    tags_map = {item["id"]: normalize_record(item) for item in (tags_resp.data or [])} if tags_resp else {}

    tagged_profile_ids = list({item["tagged_profile_id"] for item in (post_tagged_profiles_resp.data or [])})
    tagged_profiles_map = _fetch_profiles_map(tagged_profile_ids)
    profiles_map = _fetch_profiles_map(author_ids)

    media_by_post: dict[int, list] = {}
    for media in media_resp.data or []:
        media_by_post.setdefault(media["post_id"], []).append(normalize_record(media))

    comments_count: dict[int, int] = {}
    for comment in comments_resp.data or []:
        comments_count[comment["post_id"]] = comments_count.get(comment["post_id"], 0) + 1

    reaction_counts: dict[int, dict[str, int]] = {}
    for reaction in reactions_resp.data or []:
        post_id = reaction["target_id"]
        reaction_type = reaction["reaction_type"]
        entry = reaction_counts.setdefault(post_id, {"like": 0, "heart": 0, "applaud": 0})
        if reaction_type in entry:
            entry[reaction_type] += 1

    share_counts: dict[int, dict[str, int]] = {}
    for share in shares_resp.data or []:
        post_id = share["post_id"]
        entry = share_counts.setdefault(post_id, {"internal": 0, "external": 0})
        if share["share_type"] == "internal":
            entry["internal"] += 1
        else:
            entry["external"] += 1

    tags_by_post: dict[int, list] = {}
    for row in post_tags_resp.data or []:
        tag = tags_map.get(row["tag_id"])
        if tag:
            tags_by_post.setdefault(row["post_id"], []).append(tag)

    tagged_profiles_by_post: dict[int, list] = {}
    for row in post_tagged_profiles_resp.data or []:
        tagged = tagged_profiles_map.get(row["tagged_profile_id"])
        if not tagged:
            continue
        if tagged.get("role") != "contractor":
            continue
        tagged_profiles_by_post.setdefault(row["post_id"], []).append(tagged)

    enriched = []
    now = datetime.now(timezone.utc)
    requested_city = (viewer_city or "").strip().lower()
    for post in posts:
        item = normalize_record(post)
        item["author"] = profiles_map.get(post["author_profile_id"])
        item["media"] = media_by_post.get(post["id"], [])
        item["tags"] = tags_by_post.get(post["id"], [])
        item["tagged_profiles"] = tagged_profiles_by_post.get(post["id"], [])
        item["counts"] = {
            "comments": comments_count.get(post["id"], 0),
            "like": reaction_counts.get(post["id"], {}).get("like", 0),
            "heart": reaction_counts.get(post["id"], {}).get("heart", 0),
            "applaud": reaction_counts.get(post["id"], {}).get("applaud", 0),
            "shares_internal": share_counts.get(post["id"], {}).get("internal", 0),
            "shares_external": share_counts.get(post["id"], {}).get("external", 0),
        }

        created_at = post.get("created_at")
        age_penalty = 0
        if isinstance(created_at, str):
            try:
                created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                age_hours = max((now - created).total_seconds() / 3600, 0)
                age_penalty = age_hours * 0.3
            except ValueError:
                age_penalty = 0

        tier = item["author"].get("contractor_tier") if item["author"] else None
        boost = 0
        if item.get("post_type") == "tradescenter_news":
            boost += 12
        if post.get("promoted") or item.get("post_type") == "promotion":
            if tier == "platinum":
                boost += 35
            elif tier == "pro":
                boost += 20
            else:
                boost += 5
        if item.get("post_type") == "showcase" and _is_showcase_candidate(item):
            boost += 10

        engagement = (
            item["counts"]["comments"] * 2
            + item["counts"]["like"] * 1
            + item["counts"]["heart"] * 1.4
            + item["counts"]["applaud"] * 2.2
            + item["counts"]["shares_internal"] * 2.5
            + item["counts"]["shares_external"] * 2
        )
        item["rank_score"] = round(engagement + boost - age_penalty, 2)
        item["engagement_score"] = round(engagement, 2)

        author_city = (
            (item.get("author") or {})
            .get("profile_page", {})
            .get("location")
            if item.get("author")
            else None
        )
        item["distance_bucket"] = 2
        if requested_city and author_city:
            item["distance_bucket"] = 0 if author_city.strip().lower() == requested_city else 1
        enriched.append(item)

    return enriched


def _ensure_posting_quota(profile: dict, promoted: bool):
    if profile.get("role") != "contractor":
        return None

    if profile.get("kyc_status") != "verified":
        return error_response("Complete identity verification before publishing contractor posts", 403)

    tier = profile.get("contractor_tier") or "free"
    limits = get_tier_limits(tier)
    start, end = _current_month_window()

    supabase = get_supabase_client()
    base_query = (
        supabase.table("posts")
        .select("id", count="exact")
        .eq("author_profile_id", profile["id"])
        .gte("created_at", start)
        .lt("created_at", end)
    )

    total_posts = (base_query.execute().count) or 0
    if limits["posts_per_month"] is not None and total_posts >= limits["posts_per_month"]:
        return error_response(f"{tier.title()} tier monthly post limit reached", 403)

    if promoted:
        promoted_count = (
            supabase.table("posts")
            .select("id", count="exact")
            .eq("author_profile_id", profile["id"])
            .eq("promoted", True)
            .gte("created_at", start)
            .lt("created_at", end)
            .execute()
            .count
            or 0
        )
        if promoted_count >= limits["promoted_per_month"]:
            return error_response(f"{tier.title()} tier promoted post limit reached", 403)
    return None


def _upsert_tags(raw_labels: list[str]) -> list[dict]:
    supabase = get_supabase_client()
    output = []
    for raw in raw_labels:
        label = (raw or "").strip()
        if not label:
            continue
        slug = _safe_slug(label)
        if not slug:
            continue
        existing = supabase.table("tags").select("*").eq("slug", slug).limit(1).execute()
        if existing.data:
            output.append(normalize_record(existing.data[0]))
            continue
        created = supabase.table("tags").insert({"slug": slug, "label": label}).execute()
        if created.data:
            output.append(normalize_record(created.data[0]))
    return output


@social_bp.route("/feed", methods=["GET"])
def get_feed():
    try:
        page = parse_int(request.args.get("page"), 1)
        per_page = parse_int(request.args.get("per_page"), 20)
        category = (request.args.get("category") or "").strip()
        surface = (request.args.get("surface") or "home").strip().lower()
        sort = (request.args.get("sort") or "interaction").strip().lower()
        tag = (request.args.get("tag") or "").strip().lower()
        viewer_city = (request.args.get("viewer_city") or "").strip()

        if surface not in {"home", "get_inspired"}:
            return error_response("surface must be home or get_inspired")
        if sort not in {"interaction", "recency", "distance"}:
            return error_response("sort must be interaction, recency, or distance")

        supabase = get_supabase_client()
        query = supabase.table("posts").select("*").eq("is_deleted", False).eq("visibility", "public")
        if category:
            query = query.eq("category", category)

        raw_posts = query.order("created_at", desc=True).limit(300).execute().data or []
        enriched = _enrich_posts(raw_posts, viewer_city=viewer_city)

        if surface == "home":
            allowed = {"promotion", "client_post", "tradescenter_news"}
            filtered = [post for post in enriched if post.get("post_type", "client_post") in allowed]
        else:
            filtered = [post for post in enriched if _is_showcase_candidate(post)]

        if tag:
            filtered = [
                post
                for post in filtered
                if any((item.get("slug") or "").lower() == tag or str(item.get("id")) == tag for item in (post.get("tags") or []))
            ]

        if sort == "recency":
            ranked = sorted(filtered, key=lambda post: post.get("created_at") or "", reverse=True)
        elif sort == "distance":
            ranked = sorted(filtered, key=lambda post: (post.get("distance_bucket", 2), -(post.get("rank_score") or 0)))
        else:
            ranked = sorted(filtered, key=lambda post: post.get("rank_score", 0), reverse=True)

        pinned_news = None
        if surface == "home":
            news_items = [post for post in ranked if post.get("post_type") == "tradescenter_news"]
            if news_items:
                pinned_news = sorted(news_items, key=lambda post: post.get("created_at") or "", reverse=True)[0]

        start = (page - 1) * per_page
        end = start + per_page
        paged = ranked[start:end]

        return jsonify(
            {
                "posts": paged,
                "pinned_news": pinned_news,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": len(ranked),
                    "pages": (len(ranked) + per_page - 1) // per_page if per_page > 0 else 0,
                    "has_next": end < len(ranked),
                    "has_prev": page > 1,
                },
            }
        )
    except Exception as exc:
        return error_response(str(exc), 500)


@social_bp.route("/posts/<int:post_id>", methods=["GET"])
def get_post(post_id):
    try:
        supabase = get_supabase_client()
        post_resp = supabase.table("posts").select("*").eq("id", post_id).eq("is_deleted", False).limit(1).execute()
        if not post_resp.data:
            return error_response("Post not found", 404)

        post = _enrich_posts([post_resp.data[0]])[0]
        comments_resp = (
            supabase.table("comments")
            .select("*")
            .eq("post_id", post_id)
            .eq("is_deleted", False)
            .order("created_at")
            .execute()
        )
        comments = [normalize_record(item) for item in (comments_resp.data or [])]
        comment_authors = _fetch_profiles_map(list({comment["author_profile_id"] for comment in comments}))
        for comment in comments:
            comment["author"] = comment_authors.get(comment["author_profile_id"])

        post["comments"] = comments
        return jsonify(post)
    except Exception as exc:
        return error_response(str(exc), 500)


@social_bp.route("/posts", methods=["POST"])
@require_auth
def create_post():
    try:
        data = request.get_json(silent=True) or {}
        caption = (data.get("caption") or "").strip()
        media = data.get("media") or []
        tags = data.get("tags") or []
        tagged_profile_ids = data.get("tagged_profile_ids") or []
        post_type = (data.get("post_type") or "").strip().lower()
        promoted = bool(data.get("promoted", False))

        if not caption:
            return error_response("caption is required")
        if not isinstance(media, list):
            return error_response("media must be an array")
        if not isinstance(tags, list):
            return error_response("tags must be an array")
        if len(tags) > 8:
            return error_response("A maximum of 8 tags is allowed")
        if not isinstance(tagged_profile_ids, list):
            return error_response("tagged_profile_ids must be an array")

        if post_type and post_type not in ALLOWED_POST_TYPES:
            return error_response("Invalid post_type")
        if not post_type:
            if g.current_profile.get("role") == "admin":
                post_type = "tradescenter_news" if data.get("tradescenter_news") else "client_post"
            elif g.current_profile.get("role") == "contractor":
                post_type = "promotion" if promoted else "client_post"
            else:
                post_type = "client_post"

        if post_type == "tradescenter_news" and g.current_profile.get("role") != "admin":
            return error_response("Only admins can publish TradesCenter news", 403)
        if post_type in {"promotion", "showcase"} and g.current_profile.get("role") != "contractor":
            return error_response("Only contractor accounts can publish this post type", 403)

        if post_type in {"promotion", "showcase"}:
            tier = g.current_profile.get("contractor_tier")
            if tier not in {"pro", "platinum"}:
                return error_response("Paid contractor tier required for promotion/showcase posts", 403)

        promoted = promoted or post_type == "promotion"
        quota_error = _ensure_posting_quota(g.current_profile, promoted)
        if quota_error:
            return quota_error

        before_count = 0
        after_count = 0
        for item in media:
            if not isinstance(item, dict):
                continue
            phase = (item.get("phase") or "").strip().lower()
            if phase == "before":
                before_count += 1
            if phase == "after":
                after_count += 1
        if post_type == "showcase" and (before_count < 2 or after_count < 2):
            return error_response("Showcase posts require at least two before and two after photos", 400)

        supabase = get_supabase_client()
        created = (
            supabase.table("posts")
            .insert(
                {
                    "author_profile_id": g.current_profile["id"],
                    "caption": caption,
                    "category": data.get("category"),
                    "post_type": post_type,
                    "showcase_eligible": post_type == "showcase",
                    "visibility": "public",
                    "promoted": promoted,
                    "is_deleted": False,
                }
            )
            .execute()
        )
        if not created.data:
            return error_response("Failed to create post", 500)

        post = created.data[0]
        media_rows = []
        for idx, item in enumerate(media):
            url = (item.get("url") or "").strip() if isinstance(item, dict) else ""
            media_type = (item.get("type") or "").strip().lower() if isinstance(item, dict) else ""
            phase = (item.get("phase") or "").strip().lower() if isinstance(item, dict) else ""
            if not url:
                continue
            if media_type not in {"image", "video"}:
                media_type = "image"
            if phase not in {"before", "after"}:
                phase = None
            media_rows.append(
                {
                    "post_id": post["id"],
                    "media_url": url,
                    "media_type": media_type,
                    "phase": phase,
                    "order_index": idx,
                }
            )
        if media_rows:
            supabase.table("post_media").insert(media_rows).execute()

        upserted_tags = _upsert_tags([str(item) for item in tags])
        if upserted_tags:
            post_tag_rows = [{"post_id": post["id"], "tag_id": item["id"]} for item in upserted_tags]
            supabase.table("post_tags").insert(post_tag_rows).execute()

        if tagged_profile_ids:
            ids = []
            for item in tagged_profile_ids:
                try:
                    ids.append(int(item))
                except (TypeError, ValueError):
                    continue
            if ids:
                tagged_profiles = _fetch_profiles_map(ids)
                valid_ids = [pid for pid, profile in tagged_profiles.items() if profile.get("role") == "contractor"]
                if valid_ids:
                    rows = [{"post_id": post["id"], "tagged_profile_id": pid} for pid in valid_ids]
                    supabase.table("post_tagged_profiles").insert(rows).execute()

        return jsonify(_enrich_posts([post])[0]), 201
    except Exception as exc:
        return error_response(str(exc), 500)


@social_bp.route("/posts/<int:post_id>/comments", methods=["POST"])
@require_auth
def create_comment(post_id):
    try:
        data = request.get_json(silent=True) or {}
        content = (data.get("content") or "").strip()
        if not content:
            return error_response("content is required")

        supabase = get_supabase_client()
        post_resp = supabase.table("posts").select("id,post_type").eq("id", post_id).eq("is_deleted", False).limit(1).execute()
        if not post_resp.data:
            return error_response("Post not found", 404)
        if post_resp.data[0].get("post_type") == "showcase":
            return error_response("Comments are disabled for showcase posts", 403)

        created = (
            supabase.table("comments")
            .insert(
                {
                    "post_id": post_id,
                    "author_profile_id": g.current_profile["id"],
                    "parent_comment_id": None,
                    "content": content,
                    "is_deleted": False,
                }
            )
            .execute()
        )
        return jsonify(normalize_record(created.data[0])), 201
    except Exception as exc:
        return error_response(str(exc), 500)


@social_bp.route("/comments/<int:comment_id>/replies", methods=["POST"])
@require_auth
def create_reply(comment_id):
    try:
        data = request.get_json(silent=True) or {}
        content = (data.get("content") or "").strip()
        if not content:
            return error_response("content is required")

        supabase = get_supabase_client()
        parent_resp = (
            supabase.table("comments")
            .select("*")
            .eq("id", comment_id)
            .eq("is_deleted", False)
            .limit(1)
            .execute()
        )
        if not parent_resp.data:
            return error_response("Comment not found", 404)

        parent = parent_resp.data[0]
        post_resp = supabase.table("posts").select("id,post_type").eq("id", parent["post_id"]).limit(1).execute()
        if post_resp.data and post_resp.data[0].get("post_type") == "showcase":
            return error_response("Comments are disabled for showcase posts", 403)

        if parent.get("parent_comment_id"):
            return error_response("Only one reply level is allowed", 400)

        created = (
            supabase.table("comments")
            .insert(
                {
                    "post_id": parent["post_id"],
                    "author_profile_id": g.current_profile["id"],
                    "parent_comment_id": comment_id,
                    "content": content,
                    "is_deleted": False,
                }
            )
            .execute()
        )
        return jsonify(normalize_record(created.data[0])), 201
    except Exception as exc:
        return error_response(str(exc), 500)


@social_bp.route("/reactions", methods=["POST"])
@require_auth
def add_reaction():
    try:
        data = request.get_json(silent=True) or {}
        target_type = (data.get("target_type") or "").strip().lower()
        target_id = data.get("target_id")
        reaction_type = (data.get("reaction_type") or "").strip().lower()

        if target_type not in {"post", "comment"}:
            return error_response("target_type must be 'post' or 'comment'")
        if reaction_type not in ALLOWED_REACTIONS:
            return error_response("reaction_type must be one of like, heart, applaud")
        if not target_id:
            return error_response("target_id is required")

        supabase = get_supabase_client()
        existing = (
            supabase.table("reactions")
            .select("id")
            .eq("target_type", target_type)
            .eq("target_id", target_id)
            .eq("reaction_type", reaction_type)
            .eq("author_profile_id", g.current_profile["id"])
            .limit(1)
            .execute()
        )
        if existing.data:
            return jsonify({"message": "Reaction already exists", "reaction_id": existing.data[0]["id"]})

        created = (
            supabase.table("reactions")
            .insert(
                {
                    "target_type": target_type,
                    "target_id": target_id,
                    "reaction_type": reaction_type,
                    "author_profile_id": g.current_profile["id"],
                }
            )
            .execute()
        )
        return jsonify(normalize_record(created.data[0])), 201
    except Exception as exc:
        return error_response(str(exc), 500)


@social_bp.route("/reactions", methods=["DELETE"])
@require_auth
def remove_reaction():
    try:
        target_type = (request.args.get("target_type") or "").strip().lower()
        target_id = request.args.get("target_id")
        reaction_type = (request.args.get("reaction_type") or "").strip().lower()

        if target_type not in {"post", "comment"} or reaction_type not in ALLOWED_REACTIONS:
            return error_response("Invalid reaction identifier")
        if not target_id:
            return error_response("target_id is required")

        supabase = get_supabase_client()
        deleted = (
            supabase.table("reactions")
            .delete()
            .eq("target_type", target_type)
            .eq("target_id", target_id)
            .eq("reaction_type", reaction_type)
            .eq("author_profile_id", g.current_profile["id"])
            .execute()
        )
        if not deleted.data:
            return error_response("Reaction not found", 404)
        return "", 204
    except Exception as exc:
        return error_response(str(exc), 500)


@social_bp.route("/posts/<int:post_id>/share", methods=["POST"])
@require_auth
def share_post(post_id):
    try:
        data = request.get_json(silent=True) or {}
        share_type = (data.get("share_type") or "internal").strip().lower()
        if share_type not in {"internal", "external"}:
            return error_response("share_type must be internal or external")

        supabase = get_supabase_client()
        post_resp = supabase.table("posts").select("*").eq("id", post_id).eq("is_deleted", False).limit(1).execute()
        if not post_resp.data:
            return error_response("Post not found", 404)

        payload = {
            "post_id": post_id,
            "author_profile_id": g.current_profile["id"],
            "share_type": share_type,
            "external_platform": data.get("external_platform"),
        }
        created_share = supabase.table("shares").insert(payload).execute()

        repost = None
        if share_type == "internal":
            repost_payload = {
                "author_profile_id": g.current_profile["id"],
                "caption": (data.get("caption") or post_resp.data[0]["caption"]),
                "visibility": "public",
                "promoted": False,
                "is_deleted": False,
                "repost_of_post_id": post_id,
                "category": post_resp.data[0].get("category"),
                "post_type": "client_post",
                "showcase_eligible": False,
            }
            repost_resp = supabase.table("posts").insert(repost_payload).execute()
            repost = _enrich_posts([repost_resp.data[0]])[0] if repost_resp.data else None

        return jsonify(
            {
                "share": normalize_record(created_share.data[0]) if created_share.data else None,
                "repost": repost,
            }
        ), 201
    except Exception as exc:
        return error_response(str(exc), 500)


@social_bp.route("/posts/<int:post_id>", methods=["DELETE"])
@require_auth
def delete_post(post_id):
    try:
        supabase = get_supabase_client()
        post_resp = supabase.table("posts").select("*").eq("id", post_id).eq("is_deleted", False).limit(1).execute()
        if not post_resp.data:
            return error_response("Post not found", 404)
        post = post_resp.data[0]

        is_owner = int(post["author_profile_id"]) == int(g.current_profile["id"])
        is_admin = g.current_profile.get("role") == "admin"
        if not is_owner and not is_admin:
            return error_response("Forbidden", 403)

        supabase.table("posts").update({"is_deleted": True}).eq("id", post_id).execute()
        return "", 204
    except Exception as exc:
        return error_response(str(exc), 500)


@social_bp.route("/categories", methods=["GET"])
def get_categories():
    categories = [
        "Kitchen",
        "Bathroom",
        "Basement",
        "Exterior",
        "Flooring",
        "Lighting",
        "Custom Build",
    ]
    return jsonify({"categories": categories})


@social_bp.route("/tags", methods=["GET"])
def get_tags():
    try:
        supabase = get_supabase_client()
        tags_resp = supabase.table("tags").select("*").eq("is_active", True).order("label").execute()
        tags = [normalize_record(item) for item in (tags_resp.data or [])]
        return jsonify({"tags": tags})
    except Exception as exc:
        return error_response(str(exc), 500)
