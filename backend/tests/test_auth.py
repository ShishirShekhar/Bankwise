import time

import firebase_admin.auth
import pytest
from fastapi.testclient import TestClient

from app.api import assistant, auth
from app.api.auth import require_authenticated_user
from app.api.dependencies import get_sessions
from app.config import AUTH_COOKIE_SAMESITE, AUTH_COOKIE_SECURE
from app.firebase import (
    create_session_cookie as verify_and_create_session_cookie,
)
from app.firebase import (
    verify_session_cookie,
)
from app.main import app


class FakeSessions:
    def get_for_user(self, _session_id, user_id):
        if user_id == "user-1":
            return {"session_id": "session-1", "requirements": {}}
        return None


def csrf_headers(client: TestClient) -> dict[str, str]:
    csrf = client.get("/api/auth/csrf").json()["csrfToken"]
    return {"Origin": "http://localhost:3000", "X-CSRF-Token": csrf}


def test_health_and_api_require_verified_session(monkeypatch):
    app.dependency_overrides.pop(require_authenticated_user, None)
    client = TestClient(app)
    assert client.get("/api/health").status_code == 401
    assert client.get("/api/products").status_code == 401

    monkeypatch.setattr(auth, "verify_session_cookie", lambda _cookie: {"uid": "user-1"})
    response = client.get(
        "/api/health", cookies={auth.SESSION_COOKIE: "valid-session"}
    )
    assert response.status_code == 200
    response = client.get(
        "/api/products", cookies={auth.SESSION_COOKIE: "valid-session"}
    )
    assert response.status_code == 200


def test_missing_cookie_returns_401():
    app.dependency_overrides.pop(require_authenticated_user, None)
    assert TestClient(app).get("/api/auth/me").status_code == 401


def test_invalid_session_cookie_is_cleared(monkeypatch):
    app.dependency_overrides.pop(require_authenticated_user, None)

    def reject_cookie(_cookie):
        raise ValueError("invalid")

    monkeypatch.setattr(auth, "verify_session_cookie", reject_cookie)
    response = TestClient(app).get(
        "/api/auth/me", cookies={auth.SESSION_COOKIE: "invalid-session"}
    )
    assert response.status_code == 401
    assert "Max-Age=0" in response.headers["set-cookie"]


def test_session_bootstrap_verifies_id_token_and_sets_http_only_cookie(monkeypatch):
    app.dependency_overrides.pop(require_authenticated_user, None)
    monkeypatch.setattr(
        auth,
        "create_session_cookie",
        lambda token: ("server-session", {"uid": "user-1"})
        if token == "firebase-id-token"
        else pytest.fail("wrong ID token passed to Firebase Admin"),
    )
    client = TestClient(app)
    response = client.post(
        "/api/auth/session",
        headers=csrf_headers(client),
        json={"idToken": "firebase-id-token"},
    )

    assert response.status_code == 200
    assert response.json() == {"authenticated": True}
    assert response.cookies[auth.SESSION_COOKIE] == "server-session"
    assert "HttpOnly" in response.headers["set-cookie"]
    if AUTH_COOKIE_SECURE:
        assert "Secure" in response.headers["set-cookie"]
    else:
        assert "Secure" not in response.headers["set-cookie"]
    assert (
        f"samesite={AUTH_COOKIE_SAMESITE}" in response.headers["set-cookie"].lower()
    )


def test_invalid_id_token_is_rejected(monkeypatch):
    app.dependency_overrides.pop(require_authenticated_user, None)
    monkeypatch.setattr(
        auth,
        "create_session_cookie",
        lambda _token: (_ for _ in ()).throw(ValueError("bad token")),
    )
    client = TestClient(app)
    response = client.post(
        "/api/auth/session",
        headers=csrf_headers(client),
        json={"idToken": "malformed"},
    )
    assert response.status_code == 401


def test_session_creation_requires_recent_authentication(monkeypatch):
    monkeypatch.setattr("app.firebase.get_firebase_app", lambda: object())
    monkeypatch.setattr(
        firebase_admin.auth,
        "verify_id_token",
        lambda *_args, **_kwargs: {"uid": "user-1", "auth_time": time.time() - 301},
    )
    monkeypatch.setattr(
        firebase_admin.auth,
        "create_session_cookie",
        lambda *_args, **_kwargs: pytest.fail("stale authentication must be rejected"),
    )
    with pytest.raises(ValueError, match="Recent authentication"):
        verify_and_create_session_cookie("firebase-id-token")


def test_session_creation_accepts_recent_authentication(monkeypatch):
    monkeypatch.setattr("app.firebase.get_firebase_app", lambda: object())
    monkeypatch.setattr(
        firebase_admin.auth,
        "verify_id_token",
        lambda *_args, **_kwargs: {
            "uid": "user-1",
            "email": "user@example.com",
            "auth_time": time.time() - 10,
        },
    )
    monkeypatch.setattr(
        firebase_admin.auth,
        "create_session_cookie",
        lambda *_args, **_kwargs: "signed-session",
    )
    cookie, user = verify_and_create_session_cookie("firebase-id-token")
    assert cookie == "signed-session"
    assert user == {"uid": "user-1", "email": "user@example.com"}


def test_session_and_id_tokens_are_checked_for_revocation(monkeypatch):
    calls = []
    monkeypatch.setattr("app.firebase.get_firebase_app", lambda: object())
    monkeypatch.setattr(
        firebase_admin.auth,
        "verify_id_token",
        lambda token, **kwargs: calls.append(("id", token, kwargs["check_revoked"]))
        or {"uid": "user-1", "auth_time": time.time()},
    )
    monkeypatch.setattr(
        firebase_admin.auth,
        "create_session_cookie",
        lambda *_args, **_kwargs: "signed-session",
    )
    monkeypatch.setattr(
        firebase_admin.auth,
        "verify_session_cookie",
        lambda token, **kwargs: calls.append(
            ("session", token, kwargs["check_revoked"])
        )
        or {"uid": "user-1"},
    )

    verify_and_create_session_cookie("id-token")
    verify_session_cookie("session-cookie")

    assert calls == [
        ("id", "id-token", True),
        ("session", "session-cookie", True),
    ]


def test_session_bootstrap_rejects_missing_or_malformed_id_token():
    client = TestClient(app)
    headers = csrf_headers(client)
    assert client.post("/api/auth/session", headers=headers, json={}).status_code == 422
    assert (
        client.post(
            "/api/auth/session", headers=headers, json={"idToken": ""}
        ).status_code
        == 422
    )


def test_csrf_rejects_missing_and_wrong_tokens():
    client = TestClient(app)
    client.cookies.set(auth.SESSION_COOKIE, "session")
    headers = csrf_headers(client)
    missing = client.post(
        "/api/auth/logout",
        headers={"Origin": headers["Origin"]},
    )
    wrong = client.post(
        "/api/auth/logout",
        headers={**headers, "X-CSRF-Token": "wrong"},
    )
    assert missing.status_code == 403
    assert wrong.status_code == 403


def test_logout_clears_server_session_cookie(monkeypatch):
    monkeypatch.setattr(auth, "verify_session_cookie", lambda _cookie: {"uid": "user-1"})
    client = TestClient(app)
    client.cookies.set(auth.SESSION_COOKIE, "valid-session")
    response = client.post("/api/auth/logout", headers=csrf_headers(client))
    assert response.status_code == 200
    assert any(
        f"{auth.SESSION_COOKIE}=" in cookie and "Max-Age=0" in cookie
        for cookie in response.headers.get_list("set-cookie")
    )


def test_api_ask_uses_authenticated_uid_and_csrf(monkeypatch):
    saved_user_ids = []

    async def fake_workflow(_query, _catalog, _sessions, user_id):
        saved_user_ids.append(user_id)
        return {}

    monkeypatch.setattr(assistant, "run_decision_workflow", fake_workflow)
    monkeypatch.setattr(assistant, "to_ask_response", lambda _result: {"ok": True})
    client = TestClient(app)

    denied = client.post("/api/ask", json={"query": "₹1 lakh for 1 year"})
    accepted = client.post(
        "/api/ask",
        headers=csrf_headers(client),
        json={"query": "₹1 lakh for 1 year", "user_id": "attacker-chosen"},
    )

    assert denied.status_code == 403
    assert accepted.status_code == 200
    assert saved_user_ids == ["test-user"]


def test_session_endpoint_hides_sessions_owned_by_another_user():
    app.dependency_overrides[get_sessions] = FakeSessions
    response = TestClient(app).get("/api/sessions/session-1")
    assert response.status_code == 404
    app.dependency_overrides.pop(get_sessions, None)
