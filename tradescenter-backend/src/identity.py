from __future__ import annotations

from src.supabase_client import get_supabase_client
from src.utils import normalize_record


ROLE_TO_ACCOUNT_TYPE = {
    "user": "client",
    "contractor": "contractor_company",
    "admin": "admin",
}


def role_to_account_type(role: str | None) -> str:
    return ROLE_TO_ACCOUNT_TYPE.get((role or "").strip().lower(), "client")


def _upsert_index(account: dict, page: dict, profile: dict):
    supabase = get_supabase_client()
    search_parts = [page.get("display_name") or "", page.get("headline") or "", page.get("bio") or ""]
    search_parts = [part.strip() for part in search_parts if part and part.strip()]
    payload = {
        "account_id": account["id"],
        "profile_page_id": page["id"],
        "role": page["role"],
        "display_name": page["display_name"],
        "headline": page.get("headline"),
        "contractor_tier": profile.get("contractor_tier") if page["role"] == "contractor_company" else None,
        "is_verified": profile.get("kyc_status") == "verified",
        "searchable_text": " ".join(search_parts),
    }
    supabase.table("indexed_users").upsert(payload, on_conflict="account_id").execute()


def ensure_identity_graph(profile: dict, desired_role: str | None = None):
    """
    Creates/keeps additive identity tables in sync with existing profiles table.
    Returns a tuple: (account, profile_page). If tables are not available yet, returns (None, None).
    """
    supabase = get_supabase_client()

    role = (desired_role or profile.get("role") or "user").strip().lower()
    account_type = role_to_account_type(role)

    account = (
        supabase.table("accounts")
        .select("*")
        .eq("auth_user_id", profile["auth_user_id"])
        .limit(1)
        .execute()
    )
    account_row = normalize_record(account.data[0]) if account.data else None
    if not account_row:
        created = (
            supabase.table("accounts")
            .insert(
                {
                    "auth_user_id": profile["auth_user_id"],
                    "profile_id": profile["id"],
                    "account_type": account_type,
                    "email": profile["email"],
                    "status": profile.get("registration_status") or "active",
                }
            )
            .execute()
        )
        if not created.data:
            return None, None
        account_row = normalize_record(created.data[0])
    else:
        supabase.table("accounts").update(
            {
                "profile_id": profile["id"],
                "account_type": account_type,
                "email": profile["email"],
                "status": profile.get("registration_status") or "active",
            }
        ).eq("id", account_row["id"]).execute()

    page = (
        supabase.table("profile_pages")
        .select("*")
        .eq("account_id", account_row["id"])
        .limit(1)
        .execute()
    )
    page_row = normalize_record(page.data[0]) if page.data else None
    if not page_row:
        created = (
            supabase.table("profile_pages")
            .insert(
                {
                    "account_id": account_row["id"],
                    "display_name": profile["display_name"],
                    "role": account_type,
                    "avatar_url": profile.get("avatar_url"),
                    "bio": profile.get("bio"),
                    "visibility": "public",
                }
            )
            .execute()
        )
        if not created.data:
            return account_row, None
        page_row = normalize_record(created.data[0])
    else:
        supabase.table("profile_pages").update(
            {
                "display_name": profile["display_name"],
                "role": account_type,
                "avatar_url": profile.get("avatar_url"),
                "bio": profile.get("bio"),
            }
        ).eq("id", page_row["id"]).execute()

    if account_type == "contractor_company":
        supabase.table("contractor_company_profiles").upsert(
            {
                "page_id": page_row["id"],
                "business_name": profile["display_name"],
                "verified": profile.get("kyc_status") == "verified",
            },
            on_conflict="page_id",
        ).execute()
    elif account_type == "client":
        supabase.table("client_profiles").upsert({"page_id": page_row["id"]}, on_conflict="page_id").execute()

    _upsert_index(account_row, page_row, profile)
    return account_row, page_row


def attach_identity_context(profile: dict) -> dict:
    """
    Adds account/profile_page metadata to auth profile responses.
    Designed to fail soft during gradual rollout.
    """
    if not profile:
        return profile

    supabase = get_supabase_client()
    account_resp = (
        supabase.table("accounts")
        .select("*")
        .eq("auth_user_id", profile["auth_user_id"])
        .limit(1)
        .execute()
    )
    account = normalize_record(account_resp.data[0]) if account_resp.data else None
    page = None
    if account:
        page_resp = (
            supabase.table("profile_pages")
            .select("*")
            .eq("account_id", account["id"])
            .limit(1)
            .execute()
        )
        page = normalize_record(page_resp.data[0]) if page_resp.data else None

    enriched = dict(profile)
    enriched["account"] = account
    enriched["profile_page"] = page
    return enriched
