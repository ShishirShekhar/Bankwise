"""Natural language assistant route backed by the source grounded ADK workflow."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from app.ai.ask_response import to_ask_response
from app.ai.decision_workflow import run_decision_workflow
from app.api.auth import require_authenticated_user
from app.api.dependencies import get_catalog, get_sessions
from app.api.security import enforce_ask_rate_limit, require_csrf
from app.schemas import DecisionRequest

router = APIRouter()


@router.post("/api/ask", dependencies=[Depends(require_csrf)])
async def ask_endpoint(
    request: DecisionRequest,
    catalog: Annotated[Any, Depends(get_catalog)],
    sessions: Annotated[Any, Depends(get_sessions)],
    user: Annotated[dict, Depends(require_authenticated_user)],
):
    """Answer a natural language request using checked catalogue data and ADK."""
    retry_after = enforce_ask_rate_limit(user["uid"])
    if retry_after is not None:
        raise HTTPException(
            429,
            "Too many comparison requests. Please retry later.",
            headers={"Retry-After": str(retry_after)},
        )
    result = await run_decision_workflow(request.query, catalog, sessions, user["uid"])
    return to_ask_response(result)
