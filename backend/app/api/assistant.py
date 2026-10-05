"""Natural language assistant route."""

from fastapi import APIRouter

from app.ai.pipeline import PipelineResult, run
from app.schemas import DecisionRequest

router = APIRouter()


@router.post("/api/ask", response_model=PipelineResult)
def ask_endpoint(request: DecisionRequest):
    return run(request.query)
