import os
from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request

from src.authz import require_auth, require_contractor_profile
from src.identity import attach_identity_context
from src.stripe_client import get_stripe_client, stripe_enabled
from src.supabase_client import get_supabase_client
from src.utils import error_response, normalize_record


verification_bp = Blueprint("verification", __name__)


def _touch_verification_row(session_id: str, status: str, failure_reason: str | None = None, reviewed=False):
    supabase = get_supabase_client()
    updates = {
        "status": status,
        "failure_reason": failure_reason,
    }
    if reviewed:
        updates["reviewed_at"] = datetime.now(timezone.utc).isoformat()
    supabase.table("identity_verifications").update(updates).eq("provider_session_id", session_id).execute()


@verification_bp.route("/verification/status", methods=["GET"])
@require_auth
def verification_status():
    try:
        supabase = get_supabase_client()
        latest = (
            supabase.table("identity_verifications")
            .select("*")
            .eq("profile_id", g.current_profile["id"])
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        profile = attach_identity_context(g.current_profile)
        return jsonify(
            {
                "stripe_enabled": stripe_enabled(),
                "kyc_status": profile.get("kyc_status") or "unverified",
                "latest_verification": normalize_record(latest.data[0]) if latest.data else None,
            }
        )
    except Exception as exc:
        return error_response(str(exc), 500)


@verification_bp.route("/verification/identity/session", methods=["POST"])
@require_auth
def create_identity_session():
    try:
        contractor_error = require_contractor_profile(g.current_profile)
        if contractor_error:
            return contractor_error
        if not stripe_enabled():
            return error_response("Stripe is not configured", 503)

        data = request.get_json(silent=True) or {}
        return_url = (data.get("return_url") or "").strip()
        if not return_url:
            return error_response("return_url is required")

        stripe = get_stripe_client()
        profile = attach_identity_context(g.current_profile)

        session = stripe.identity.VerificationSession.create(
            type="document",
            return_url=return_url,
            metadata={
                "profile_id": str(profile["id"]),
                "account_id": str(profile.get("account", {}).get("id") or ""),
            },
        )

        supabase = get_supabase_client()
        supabase.table("identity_verifications").upsert(
            {
                "profile_id": profile["id"],
                "account_id": profile.get("account", {}).get("id"),
                "provider": "stripe_identity",
                "provider_session_id": session.id,
                "status": session.status or "requires_input",
                "metadata": {"client_reference": profile["id"]},
            },
            on_conflict="provider_session_id",
        ).execute()
        supabase.table("profiles").update({"kyc_status": "pending"}).eq("id", profile["id"]).execute()

        return jsonify(
            {
                "session_id": session.id,
                "client_secret": session.client_secret,
                "status": session.status,
            }
        )
    except Exception as exc:
        return error_response(str(exc), 500)


@verification_bp.route("/verification/webhooks", methods=["POST"])
def verification_webhooks():
    if not stripe_enabled():
        return jsonify({"received": False, "reason": "stripe_not_configured"}), 503

    try:
        stripe = get_stripe_client()
        payload = request.get_data(as_text=True)
        signature = request.headers.get("Stripe-Signature")
        secret = os.getenv("STRIPE_IDENTITY_WEBHOOK_SECRET") or os.getenv("STRIPE_WEBHOOK_SECRET")

        if secret:
            event = stripe.Webhook.construct_event(payload, signature, secret)
        else:
            event = request.get_json(silent=True) or {}

        event_type = event.get("type", "")
        obj = event.get("data", {}).get("object", {}) or {}
        session_id = obj.get("id")
        if not session_id:
            return jsonify({"received": True})

        supabase = get_supabase_client()
        verification = (
            supabase.table("identity_verifications")
            .select("*")
            .eq("provider_session_id", session_id)
            .limit(1)
            .execute()
        )
        profile_id = verification.data[0]["profile_id"] if verification.data else None

        if event_type == "identity.verification_session.verified":
            _touch_verification_row(session_id, "verified", reviewed=True)
            if profile_id:
                supabase.table("profiles").update({"kyc_status": "verified"}).eq("id", profile_id).execute()
        elif event_type in {"identity.verification_session.canceled", "identity.verification_session.requires_input"}:
            reason = (obj.get("last_error") or {}).get("reason")
            status = "failed" if event_type.endswith("requires_input") else "canceled"
            _touch_verification_row(session_id, status, failure_reason=reason, reviewed=True)
            if profile_id:
                supabase.table("profiles").update({"kyc_status": status if status != "canceled" else "unverified"}).eq(
                    "id", profile_id
                ).execute()
        elif event_type == "identity.verification_session.processing":
            _touch_verification_row(session_id, "processing")
            if profile_id:
                supabase.table("profiles").update({"kyc_status": "pending"}).eq("id", profile_id).execute()

        return jsonify({"received": True})
    except Exception as exc:
        return error_response(str(exc), 400)
