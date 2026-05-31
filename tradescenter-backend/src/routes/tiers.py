from flask import Blueprint, g, jsonify, request

from src.authz import ALLOWED_TIERS, get_tier_limits, require_auth, require_contractor_profile
from src.stripe_client import stripe_enabled
from src.supabase_client import get_supabase_client
from src.utils import error_response, normalize_record


tiers_bp = Blueprint("tiers", __name__)


@tiers_bp.route("/contractor/tier/status", methods=["GET"])
@require_auth
def get_tier_status():
    contractor_error = require_contractor_profile(g.current_profile)
    if contractor_error:
        return contractor_error

    tier = g.current_profile.get("contractor_tier") or "free"
    return jsonify(
        {
            "tier": tier,
            "status": g.current_profile.get("tier_status", "active"),
            "limits": get_tier_limits(tier),
            "billing_mode": "stripe" if stripe_enabled() else "demo_supabase",
            "kyc_status": g.current_profile.get("kyc_status", "unverified"),
        }
    )


@tiers_bp.route("/contractor/tier/checkout-demo", methods=["POST"])
@require_auth
def checkout_demo():
    contractor_error = require_contractor_profile(g.current_profile)
    if contractor_error:
        return contractor_error

    data = request.get_json(silent=True) or {}
    target_tier = (data.get("target_tier") or "").strip().lower()
    if target_tier not in ALLOWED_TIERS:
        return error_response("target_tier must be free, pro, or platinum")

    supabase = get_supabase_client()
    updated = (
        supabase.table("profiles")
        .update({"contractor_tier": target_tier, "tier_status": "active"})
        .eq("id", g.current_profile["id"])
        .execute()
    )
    if not updated.data:
        return error_response("Profile not found", 404)

    request_log = (
        supabase.table("tier_change_requests")
        .insert(
            {
                "profile_id": g.current_profile["id"],
                "requested_tier": target_tier,
                "status": "approved_demo",
                "provider": "supabase_demo",
            }
        )
        .execute()
    )
    return jsonify(
        {
            "message": "Tier updated (demo mode)",
            "profile": normalize_record(updated.data[0]),
            "tier_request": normalize_record(request_log.data[0]) if request_log.data else None,
            "production_note": "Integrate Stripe Checkout + webhooks for production billing lifecycle.",
        }
    )
