"""Natural language assistant route backed by the source grounded ADK workflow."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from google.auth.exceptions import GoogleAuthError

from app.ai.ask_response import to_ask_response
from app.ai.decision_workflow import run_decision_workflow
from app.api.auth import require_authenticated_user
from app.api.dependencies import get_catalog, get_sessions
from app.api.security import enforce_ask_rate_limit, require_csrf
from app.config import ENVIRONMENT, GOOGLE_CLOUD_PROJECT
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
    rag_repository = None
    searcher = None
    if ENVIRONMENT == "production":
        try:
            from app.repositories.rag import BigQueryRagRepository

            rag_repository = BigQueryRagRepository()
        except (ImportError, RuntimeError, OSError, ValueError, GoogleAuthError):
            # The workflow records unavailable internal retrieval and continues
            # only with independently verified canonical catalogue records.
            from app.ai.specialists import UnavailableRagRepository

            rag_repository = UnavailableRagRepository()
        if GOOGLE_CLOUD_PROJECT:
            try:
                from app.ai.research import GoogleSearchResearcher

                searcher = GoogleSearchResearcher()
            except (ImportError, RuntimeError, OSError, ValueError, GoogleAuthError):
                from app.ai.specialists import UnavailableSearcher

                searcher = UnavailableSearcher()
    if ENVIRONMENT != "production":
        result = await run_decision_workflow(request.query, catalog, sessions, user["uid"])
    else:
        result = await run_decision_workflow(
            request.query, catalog, sessions, user["uid"], rag_repository, searcher
        )
    return to_ask_response(result)
