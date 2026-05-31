import os
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from werkzeug.security import check_password_hash, generate_password_hash

from src.supabase_client import get_supabase_client
from src.utils import normalize_record


LOCAL_AUTH_ISSUER = "tradescenter-local-auth"


def is_local_auth_enabled() -> bool:
    return os.getenv("SUPABASE_AUTH_MODE", "").strip().lower() == "local"


def _jwt_secret() -> str:
    return os.getenv("LOCAL_AUTH_JWT_SECRET") or os.getenv("FLASK_SECRET_KEY") or "tradescenter-dev-secret"


def create_access_token(auth_user_id: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "iss": LOCAL_AUTH_ISSUER,
        "sub": auth_user_id,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=30)).timestamp()),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            _jwt_secret(),
            algorithms=["HS256"],
            issuer=LOCAL_AUTH_ISSUER,
        )
    except jwt.PyJWTError:
        return None
    return payload if payload.get("sub") and payload.get("email") else None


def get_local_user_by_email(email: str) -> dict | None:
    response = (
        get_supabase_client()
        .table("local_auth_users")
        .select("*")
        .eq("email", email)
        .limit(1)
        .execute()
    )
    return normalize_record(response.data[0]) if response.data else None


def create_local_user(email: str, password: str, display_name: str) -> dict:
    existing = get_local_user_by_email(email)
    if existing:
        raise ValueError("An account with that email already exists")

    auth_user_id = str(uuid.uuid4())
    created = (
        get_supabase_client()
        .table("local_auth_users")
        .insert(
            {
                "auth_user_id": auth_user_id,
                "email": email,
                "password_hash": generate_password_hash(password),
                "display_name": display_name,
            }
        )
        .execute()
    )
    if not created.data:
        raise RuntimeError("Local registration failed")
    return normalize_record(created.data[0])


def verify_local_user(email: str, password: str) -> dict | None:
    user = get_local_user_by_email(email)
    if not user or not check_password_hash(user["password_hash"], password):
        return None
    return user
