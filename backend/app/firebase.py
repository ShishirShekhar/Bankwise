"""Firebase Admin initialization and verified identity/session operations."""

import time
from datetime import timedelta
from functools import lru_cache
from typing import TypedDict

from app.config import FIREBASE_PROJECT_ID

SESSION_DURATION = timedelta(days=5)
RECENT_AUTH_WINDOW_SECONDS = 5 * 60


class FirebaseUser(TypedDict, total=False):
    uid: str
    email: str
    name: str


class RecentAuthenticationRequired(ValueError):
    """The Firebase identity is valid but its sign-in is too old for a session."""


@lru_cache(maxsize=1)
def get_firebase_app():
    """Initialize Firebase Admin once using Application Default Credentials."""
    import firebase_admin

    try:
        return firebase_admin.get_app()
    except ValueError:
        options = {"projectId": FIREBASE_PROJECT_ID} if FIREBASE_PROJECT_ID else None
        return firebase_admin.initialize_app(options=options)


def create_session_cookie(id_token: str) -> tuple[str, FirebaseUser]:
    from firebase_admin import auth

    app = get_firebase_app()
    decoded = auth.verify_id_token(id_token, check_revoked=True, app=app)
    auth_time = decoded.get("auth_time")
    now = time.time()
    if not isinstance(auth_time, (int, float)) or not 0 <= now - auth_time <= RECENT_AUTH_WINDOW_SECONDS:
        raise RecentAuthenticationRequired("Recent authentication is required")
    cookie = auth.create_session_cookie(id_token, expires_in=SESSION_DURATION, app=app)
    return cookie, _safe_user(decoded)


def verify_session_cookie(cookie: str) -> FirebaseUser:
    from firebase_admin import auth

    decoded = auth.verify_session_cookie(cookie, check_revoked=True, app=get_firebase_app())
    return _safe_user(decoded)


def _safe_user(claims: dict) -> FirebaseUser:
    user: FirebaseUser = {"uid": claims["uid"]}
    if claims.get("email"):
        user["email"] = claims["email"]
    if claims.get("name"):
        user["name"] = claims["name"]
    return user
