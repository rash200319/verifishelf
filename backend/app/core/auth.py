from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time

from dotenv import load_dotenv
from fastapi import HTTPException, Header

load_dotenv()

AUTH_SECRET = os.getenv("AUTH_SECRET", "dev-secret-change-me")
DEMO_AUTH_EMAIL = os.getenv("DEMO_AUTH_EMAIL", "admin@verifishelf.local")
DEMO_AUTH_PASSWORD = os.getenv("DEMO_AUTH_PASSWORD", "admin123")
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
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, stored_password_hash: str) -> bool:
    if stored_password_hash in {"hashed_password_here", "demo"}:
        return password == DEMO_AUTH_PASSWORD

    if stored_password_hash == password:
        return True

    return hmac.compare_digest(hash_password(password), stored_password_hash)


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


def require_admin(authorization: str = Header(default="")) -> dict:
    payload = require_auth(authorization)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return payload
