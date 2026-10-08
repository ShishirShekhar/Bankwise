"""Decision and persisted-session routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from app.ai.decision_workflow import run_decision_workflow
from app.api.dependencies import get_catalog, get_sessions
from app.schemas import DecisionRequest

router = APIRouter()


@router.post("/api/decision")
async def decision(
    request: DecisionRequest,
    catalog: Annotated[Any, Depends(get_catalog)],
    sessions: Annotated[Any, Depends(get_sessions)],
):
    return await run_decision_workflow(request.query, catalog, sessions)


@router.get("/api/sessions/{session_id}")
def get_decision_session(
    session_id: str,
    sessions: Annotated[Any, Depends(get_sessions)],
):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Decision session not found")
    return session
