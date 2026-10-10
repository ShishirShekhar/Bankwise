"""Firebase session bootstrap and browser-session routes."""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field

from app.api.security import (
    SESSION_COOKIE,
    clear_session_cookie,
    create_csrf_token,
    expired_session_cookie_header,
    require_csrf,
)
from app.config import AUTH_COOKIE_SAMESITE, AUTH_COOKIE_SECURE
from app.firebase import (
    FirebaseUser,
    RecentAuthenticationRequired,
    create_session_cookie,
    verify_session_cookie,
)

router = APIRouter()
bootstrap_router = APIRouter()
SESSION_MAX_AGE_SECONDS = 5 * 24 * 60 * 60


class SessionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id_token: str = Field(alias="idToken", min_length=1)


class CurrentUserResponse(BaseModel):
    authenticated: bool = True
    uid: str
    email: str | None = None
    name: str | None = None


def require_authenticated_user(
    bankwise_session: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> FirebaseUser:
    if not bankwise_session:
        raise HTTPException(401, "Authentication required")
    try:
        return verify_session_cookie(bankwise_session)
    except Exception as exc:
        raise HTTPException(
            401,
            "Invalid or expired session",
            headers={"Set-Cookie": expired_session_cookie_header()},
        ) from exc


@bootstrap_router.get("/api/auth/csrf")
def csrf_token(response: Response):
    response.headers["Cache-Control"] = "no-store"
    return {"csrfToken": create_csrf_token()}


@bootstrap_router.post("/api/auth/session", dependencies=[Depends(require_csrf)])
def create_session(request: SessionRequest, response: Response):
    try:
        cookie, _user = create_session_cookie(request.id_token)
    except RecentAuthenticationRequired as exc:
        raise HTTPException(401, "Recent Firebase sign-in is required") from exc
    except Exception as exc:
        raise HTTPException(401, "Could not verify Firebase sign-in") from exc

    response.set_cookie(
        SESSION_COOKIE,
        cookie,
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        secure=AUTH_COOKIE_SECURE,
        samesite=AUTH_COOKIE_SAMESITE,
        path="/",
    )
    return {"authenticated": True}


@router.get("/api/auth/me", response_model=CurrentUserResponse)
def current_user(user: Annotated[FirebaseUser, Depends(require_authenticated_user)]):
    return {"authenticated": True, **user}


@router.post(
    "/api/auth/logout",
    dependencies=[Depends(require_authenticated_user), Depends(require_csrf)],
)
def logout(response: Response):
    clear_session_cookie(response)
    return {"signed_out": True}
