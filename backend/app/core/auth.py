from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time

import bcrypt
from dotenv import load_dotenv
from fastapi import HTTPException, Header

load_dotenv()

# Secrets that must never be used in a real deployment -- if the env var is
# still set to one of these (or unset), the app refuses to start rather than
# silently signing tokens with a value anyone reading this repo (or its git
# history) already knows.
_KNOWN_WEAK_SECRETS = {"", "dev-secret-change-me", "torchproxy-admin-secret-key-123"}


def _require_real_secret(env_var: str) -> str:
    value = os.getenv(env_var, "")
    if value in _KNOWN_WEAK_SECRETS:
        raise RuntimeError(
            f"{env_var} is not set to a real secret. Generate one with "
            f"`python -c \"import secrets; print(secrets.token_urlsafe(48))\"` "
            f"and set it in your .env -- refusing to start with a known/placeholder value."
        )
    return value


AUTH_SECRET = _require_real_secret("AUTH_SECRET")
AUTH_TOKEN_TTL_SECONDS = int(os.getenv("AUTH_TOKEN_TTL_SECONDS", "86400"))


def _b64encode_json(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64decode_json(encoded: str) -> dict:
    padding = "=" * (-len(encoded) % 4)
    raw = base64.urlsafe_b64decode((encoded + padding).encode("utf-8"))
    return json.loads(raw.decode("utf-8"))


def _sign(payload_b64: str) -> str:
    return hmac.new(
        AUTH_SECRET.encode("utf-8"),
        payload_b64.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def create_access_token(payload: dict) -> str:
    now = int(time.time())
    token_payload = dict(payload)
    token_payload["iat"] = now
    token_payload["exp"] = now + AUTH_TOKEN_TTL_SECONDS
    if "sub" not in token_payload:
        token_payload["sub"] = token_payload.get("email", "user")
    payload_b64 = _b64encode_json(token_payload)
    signature = _sign(payload_b64)
    return f"{payload_b64}.{signature}"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, stored_password_hash: str) -> bool:
    """
    bcrypt only -- no demo-password sentinel, no plaintext-equality
    fallback. A row that isn't a valid bcrypt hash (e.g. a leftover 'demo'
    seed sentinel or an old sha256 hash) is rejected rather than silently
    accepted through a weaker path; re-seed/reset the password instead.
    """
    if not stored_password_hash:
        return False

    try:
        return bcrypt.checkpw(password.encode("utf-8"), stored_password_hash.encode("utf-8"))
    except ValueError:
        return False


def require_auth(authorization: str = Header(default="")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload_b64, signature = token.split(".", 1)
        if not hmac.compare_digest(_sign(payload_b64), signature):
            raise HTTPException(status_code=401, detail="Invalid token")

        payload = _b64decode_json(payload_b64)
        if int(payload.get("exp", 0)) < int(time.time()):
            raise HTTPException(status_code=401, detail="Token expired")

        return payload
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid token format") from exc


def require_brand_admin(authorization: str = Header(default="")) -> dict:
    payload = require_auth(authorization)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Allow approved brands OR pending brands to complete onboarding
    if payload.get("brand_status") not in ("approved", "pending_review"):
        raise HTTPException(status_code=403, detail="Brand must be approved or in review")

    return payload


def require_superadmin(authorization: str = Header(default="")) -> dict:
    """
    TorchProxy platform admin -- a real logged-in user with role=superadmin,
    same login system as everyone else. Replaces the old X-TorchProxy-Admin-Key
    static header gate, which was never actually reachable from the frontend
    (it only ever sent the normal Bearer token) and is retired entirely now
    that a real account exists for this.
    """
    payload = require_auth(authorization)
    if payload.get("role") != "superadmin":
        raise HTTPException(status_code=403, detail="Superadmin access required")

    return payload
