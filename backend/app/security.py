from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta

import jwt
from fastapi import HTTPException, Request

from app.config import get_settings

PBKDF2_ROUNDS = 200_000
_BUCKETS: dict[str, list[float]] = {}


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PBKDF2_ROUNDS).hex()
    return f"pbkdf2_sha256${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, salt, digest = stored.split("$")
    except ValueError:
        return False
    if algo != "pbkdf2_sha256":
        return False
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), PBKDF2_ROUNDS).hex()
    return hmac.compare_digest(check, digest)


def make_token(user_id: int, role: str) -> str:
    settings = get_settings()
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=settings.access_token_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def read_token(token: str) -> dict | None:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None


def new_csrf() -> str:
    return secrets.token_urlsafe(32)


def csrf_ok(request: Request) -> None:
    cookie = request.cookies.get("wise_csrf", "")
    header = request.headers.get("x-csrf-token", "")
    if not cookie or not header or not hmac.compare_digest(cookie, header):
        raise HTTPException(status_code=403, detail="CSRF token missing or mismatched.")


def rate_limit(request: Request, bucket: str, limit: int = 12, window: int = 60) -> None:
    ip = request.client.host if request.client else "unknown"
    key = f"{bucket}:{ip}"
    now = time.time()
    hits = [stamp for stamp in _BUCKETS.get(key, []) if now - stamp < window]
    if len(hits) >= limit:
        raise HTTPException(status_code=429, detail="Too many requests. Try again shortly.")
    hits.append(now)
    _BUCKETS[key] = hits


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
