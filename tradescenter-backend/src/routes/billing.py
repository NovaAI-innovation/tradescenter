import os
from datetime import datetime, timezone

from flask import Blueprint, g, jsonify, request

from src.authz import require_auth, require_contractor_profile
from src.identity import attach_identity_context
from src.stripe_client import get_stripe_client, stripe_enabled
from src.supabase_client import get_supabase_client
from src.utils import error_response, normalize_record


billing_bp = Blueprint("billing", __name__)


def _tier_to_price_id(tier: str):
    mapping = {
        "pro": os.getenv("STRIPE_PRICE_PRO"),
        "platinum": os.getenv("STRIPE_PRICE_PLATINUM"),
    }
    return mapping.get(tier)


def _price_id_to_tier(price_id: str | None):
    if not price_id:
        return "free"
    if price_id == os.getenv("STRIPE_PRICE_PRO"):
        return "pro"
    if price_id == os.getenv("STRIPE_PRICE_PLATINUM"):
        return "platinum"
    return "free"


def _sync_profile_tier(profile_id: int, tier: str, status: str, stripe_customer_id: str | None = None):
    supabase = get_supabase_client()
    payload = {"contractor_tier": tier, "tier_status": status}
    if stripe_customer_id:
        payload["stripe_customer_id"] = stripe_customer_id
    supabase.table("profiles").update(payload).eq("id", profile_id).execute()


def _latest_subscription(profile_id: int):
    supabase = get_supabase_client()
    row = (
        supabase.table("subscriptions")
        .select("*")
        .eq("profile_id", profile_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return normalize_record(row.data[0]) if row.data else None


@billing_bp.route("/billing/subscription-status", methods=["GET"])
@require_auth
def subscription_status():
    try:
        contractor_error = require_contractor_profile(g.current_profile)
        if contractor_error:
            return contractor_error
        profile = attach_identity_context(g.current_profile)
        latest = _latest_subscription(profile["id"])
        return jsonify(
            {
                "stripe_enabled": stripe_enabled(),
                "tier": profile.get("contractor_tier") or "free",
                "status": profile.get("tier_status") or "active",
                "subscription": latest,
            }
        )
    except Exception as exc:
        return error_response(str(exc), 500)


@billing_bp.route("/billing/checkout-session", methods=["POST"])
@require_auth
def create_checkout_session():
    try:
        contractor_error = require_contractor_profile(g.current_profile)
        if contractor_error:
            return contractor_error

        data = request.get_json(silent=True) or {}
        target_tier = (data.get("target_tier") or "").strip().lower()
        if target_tier not in {"free", "pro", "platinum"}:
            return error_response("target_tier must be free, pro, or platinum")

        if target_tier == "free":
            _sync_profile_tier(g.current_profile["id"], "free", "active")
            return jsonify({"message": "Tier set to free", "tier": "free", "status": "active"})

        if not stripe_enabled():
            return error_response("Stripe is not configured", 503)

        stripe = get_stripe_client()
        price_id = _tier_to_price_id(target_tier)
        if not price_id:
            return error_response(f"Price is not configured for {target_tier}")

        profile = attach_identity_context(g.current_profile)
        customer_id = profile.get("stripe_customer_id")
        if not customer_id:
            customer = stripe.Customer.create(
                email=profile.get("email"),
                name=profile.get("display_name"),
                metadata={"profile_id": str(profile["id"])},
            )
            customer_id = customer.id
            supabase = get_supabase_client()
            supabase.table("billing_customers").upsert(
                {
                    "profile_id": profile["id"],
                    "account_id": profile.get("account", {}).get("id"),
                    "stripe_customer_id": customer_id,
                    "email": profile.get("email"),
                },
                on_conflict="profile_id",
            ).execute()
            supabase.table("profiles").update({"stripe_customer_id": customer_id}).eq("id", profile["id"]).execute()

        success_url = (data.get("success_url") or "").strip()
        cancel_url = (data.get("cancel_url") or "").strip()
        if not success_url or not cancel_url:
            return error_response("success_url and cancel_url are required")

        session = stripe.checkout.Session.create(
            mode="subscription",
            customer=customer_id,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "profile_id": str(profile["id"]),
                "target_tier": target_tier,
                "account_id": str(profile.get("account", {}).get("id") or ""),
            },
        )

        get_supabase_client().table("subscription_events").insert(
            {
                "profile_id": profile["id"],
                "account_id": profile.get("account", {}).get("id"),
                "event_type": "checkout.session.created",
                "payload": {"session_id": session.id, "target_tier": target_tier},
            }
        ).execute()

        return jsonify({"session_id": session.id, "checkout_url": session.url})
    except Exception as exc:
        return error_response(str(exc), 500)


@billing_bp.route("/billing/customer-portal", methods=["POST"])
@require_auth
def customer_portal():
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

        profile = g.current_profile
        customer_id = profile.get("stripe_customer_id")
        if not customer_id:
            return error_response("No Stripe customer on file", 404)

        stripe = get_stripe_client()
        session = stripe.billing_portal.Session.create(customer=customer_id, return_url=return_url)
        return jsonify({"portal_url": session.url})
    except Exception as exc:
        return error_response(str(exc), 500)


def _handle_subscription_event(event: dict):
    data_object = event.get("data", {}).get("object", {})
    subscription_id = data_object.get("id")
    customer_id = data_object.get("customer")
    status = data_object.get("status") or "incomplete"
    items = data_object.get("items", {}).get("data", [])
    first_price = items[0].get("price", {}).get("id") if items else None
    tier = _price_id_to_tier(first_price)

    profile_id = None
    metadata = data_object.get("metadata") or {}
    if metadata.get("profile_id"):
        try:
            profile_id = int(metadata.get("profile_id"))
        except (TypeError, ValueError):
            profile_id = None

    supabase = get_supabase_client()
    if not profile_id and customer_id:
        profile_resp = supabase.table("profiles").select("id, role").eq("stripe_customer_id", customer_id).limit(1).execute()
        if profile_resp.data:
            if profile_resp.data[0].get("role") != "contractor":
                return
            profile_id = profile_resp.data[0]["id"]

    if profile_id:
        profile_role_resp = supabase.table("profiles").select("role").eq("id", profile_id).limit(1).execute()
        if not profile_role_resp.data or profile_role_resp.data[0].get("role") != "contractor":
            return

    if not profile_id:
        return

    account_id = None
    account_resp = supabase.table("accounts").select("id").eq("profile_id", profile_id).limit(1).execute()
    if account_resp.data:
        account_id = account_resp.data[0]["id"]

    subscription_payload = {
        "profile_id": profile_id,
        "account_id": account_id,
        "stripe_subscription_id": subscription_id,
        "stripe_customer_id": customer_id,
        "tier": tier,
        "status": status,
        "current_period_start": datetime.fromtimestamp(data_object.get("current_period_start", 0), tz=timezone.utc).isoformat()
        if data_object.get("current_period_start")
        else None,
        "current_period_end": datetime.fromtimestamp(data_object.get("current_period_end", 0), tz=timezone.utc).isoformat()
        if data_object.get("current_period_end")
        else None,
        "cancel_at": datetime.fromtimestamp(data_object.get("cancel_at", 0), tz=timezone.utc).isoformat()
        if data_object.get("cancel_at")
        else None,
        "canceled_at": datetime.fromtimestamp(data_object.get("canceled_at", 0), tz=timezone.utc).isoformat()
        if data_object.get("canceled_at")
        else None,
        "metadata": metadata,
    }
    upserted = supabase.table("subscriptions").upsert(subscription_payload, on_conflict="stripe_subscription_id").execute()
    record = upserted.data[0] if upserted.data else None
    if record:
        _sync_profile_tier(profile_id, tier, status, stripe_customer_id=customer_id)
        supabase.table("profiles").update({"current_subscription_id": record["id"]}).eq("id", profile_id).execute()

    supabase.table("subscription_events").upsert(
        {
            "profile_id": profile_id,
            "account_id": account_id,
            "subscription_id": record["id"] if record else None,
            "stripe_event_id": event.get("id"),
            "event_type": event.get("type"),
            "payload": data_object,
        },
        on_conflict="stripe_event_id",
    ).execute()


def _handle_invoice_event(event: dict):
    invoice = event.get("data", {}).get("object", {})
    customer_id = invoice.get("customer")
    subscription_id = invoice.get("subscription")

    supabase = get_supabase_client()
    profile_id = None
    account_id = None
    subscription_pk = None

    if customer_id:
        profile_resp = supabase.table("profiles").select("id, role").eq("stripe_customer_id", customer_id).limit(1).execute()
        if profile_resp.data:
            if profile_resp.data[0].get("role") != "contractor":
                return
            profile_id = profile_resp.data[0]["id"]
            account_resp = supabase.table("accounts").select("id").eq("profile_id", profile_id).limit(1).execute()
            if account_resp.data:
                account_id = account_resp.data[0]["id"]

    if subscription_id:
        sub_resp = supabase.table("subscriptions").select("id").eq("stripe_subscription_id", subscription_id).limit(1).execute()
        if sub_resp.data:
            subscription_pk = sub_resp.data[0]["id"]

    supabase.table("invoices").upsert(
        {
            "profile_id": profile_id,
            "account_id": account_id,
            "subscription_id": subscription_pk,
            "stripe_invoice_id": invoice.get("id"),
            "status": invoice.get("status") or "open",
            "amount_due": invoice.get("amount_due") or 0,
            "amount_paid": invoice.get("amount_paid") or 0,
            "currency": invoice.get("currency") or "usd",
            "hosted_invoice_url": invoice.get("hosted_invoice_url"),
            "invoice_pdf": invoice.get("invoice_pdf"),
            "period_start": datetime.fromtimestamp(invoice.get("period_start", 0), tz=timezone.utc).isoformat()
            if invoice.get("period_start")
            else None,
            "period_end": datetime.fromtimestamp(invoice.get("period_end", 0), tz=timezone.utc).isoformat()
            if invoice.get("period_end")
            else None,
        },
        on_conflict="stripe_invoice_id",
    ).execute()


@billing_bp.route("/billing/webhooks", methods=["POST"])
def billing_webhooks():
    if not stripe_enabled():
        return jsonify({"received": False, "reason": "stripe_not_configured"}), 503

    try:
        stripe = get_stripe_client()
        payload = request.get_data(as_text=True)
        signature = request.headers.get("Stripe-Signature")
        secret = os.getenv("STRIPE_WEBHOOK_SECRET")

        if secret:
            event = stripe.Webhook.construct_event(payload, signature, secret)
        else:
            event = request.get_json(silent=True) or {}

        event_type = event.get("type", "")
        if event_type.startswith("customer.subscription."):
            _handle_subscription_event(event)
        elif event_type.startswith("invoice."):
            _handle_invoice_event(event)

        return jsonify({"received": True})
    except Exception as exc:
        return error_response(str(exc), 400)
