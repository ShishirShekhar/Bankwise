"""Persisted decision-session routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_sessions

router = APIRouter()


@router.get("/api/sessions/{session_id}")
def get_decision_session(
    session_id: str,
    sessions: Annotated[Any, Depends(get_sessions)],
):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Decision session not found")
    return session
