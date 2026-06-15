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


def create_access_token(email: str) -> str:
    now = int(time.time())
    payload = {"sub": email, "iat": now, "exp": now + AUTH_TOKEN_TTL_SECONDS}
    payload_b64 = _b64encode_json(payload)
    signature = _sign(payload_b64)
    return f"{payload_b64}.{signature}"


def authenticate_user(email: str, password: str) -> bool:
    return email == DEMO_AUTH_EMAIL and password == DEMO_AUTH_PASSWORD


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
