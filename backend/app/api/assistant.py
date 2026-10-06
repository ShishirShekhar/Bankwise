"""Natural language assistant route backed by the source grounded ADK workflow."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.ai.ask_response import to_ask_response
from app.ai.decision_workflow import run_decision_workflow
from app.api.dependencies import get_catalog, get_sessions
from app.repositories.local_json import LocalJsonCatalog
from app.repositories.memory_sessions import MemorySessionRepository
from app.schemas import DecisionRequest

router = APIRouter()


@router.post("/api/ask")
async def ask_endpoint(
    request: DecisionRequest,
    catalog: Annotated[LocalJsonCatalog, Depends(get_catalog)],
    sessions: Annotated[MemorySessionRepository, Depends(get_sessions)],
):
    """Answer a natural language request using checked catalogue data and ADK."""
    result = await run_decision_workflow(request.query, catalog, sessions)
    return to_ask_response(result)
