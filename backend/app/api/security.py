"""CSRF validation and browser-session cookie helpers."""

import hashlib
import hmac
import secrets
import time

from fastapi import Header, HTTPException, Request, Response

from app.config import (
    AUTH_COOKIE_SAMESITE,
    AUTH_COOKIE_SECURE,
    CORS_ORIGINS,
    CSRF_SECRET,
    ENVIRONMENT,
)

CSRF_HEADER = "X-CSRF-Token"
SESSION_COOKIE = "__session" if ENVIRONMENT == "production" else "bankwise_session"
CSRF_TOKEN_TTL_SECONDS = 60 * 60


def create_csrf_token() -> str:
    expires_at = int(time.time()) + CSRF_TOKEN_TTL_SECONDS
    payload = f"{expires_at}.{secrets.token_urlsafe(24)}"
    signature = hmac.new(
        CSRF_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return f"{payload}.{signature}"


def _is_valid_csrf_token(token: str) -> bool:
    try:
        expires_at_text, nonce, signature = token.split(".", maxsplit=2)
        expires_at = int(expires_at_text)
    except (TypeError, ValueError):
        return False

    now = int(time.time())
    if expires_at < now or expires_at > now + CSRF_TOKEN_TTL_SECONDS + 30:
        return False

    payload = f"{expires_at_text}.{nonce}"
    expected = hmac.new(
        CSRF_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return secrets.compare_digest(signature, expected)


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        SESSION_COOKIE,
        path="/",
        secure=AUTH_COOKIE_SECURE,
        httponly=True,
        samesite=AUTH_COOKIE_SAMESITE,
    )


def expired_session_cookie_header() -> str:
    response = Response()
    clear_session_cookie(response)
    return response.headers["set-cookie"]


def require_csrf(
    request: Request,
    csrf_header: str | None = Header(default=None, alias=CSRF_HEADER),
) -> None:
    if request.headers.get("origin") not in CORS_ORIGINS:
        raise HTTPException(403, "Request origin is not allowed")
    if not csrf_header or not _is_valid_csrf_token(csrf_header):
        raise HTTPException(403, "CSRF validation failed")
