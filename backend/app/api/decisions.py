"""Decision and persisted-session routes."""

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_catalog, get_sessions
from app.ai.orchestrator import run_decision_agent
from app.config import GOOGLE_CLOUD_PROJECT
from app.domain.comparison import compare_products
from app.domain.identifiers import new_id
from app.domain.input import extract_requirements, redact_sensitive_input
from app.repositories.bigquery import BigQueryRepository
from app.repositories.firestore import FirestoreSessionRepository
from app.schemas import DecisionRequest

router = APIRouter()


@router.post("/api/decision")
async def decision(
    request: DecisionRequest,
    catalog: BigQueryRepository = Depends(get_catalog),
    sessions: FirestoreSessionRepository = Depends(get_sessions),
):
    safe_query = redact_sensitive_input(request.query)
    requirements = extract_requirements(safe_query)
    request_id = new_id("req")
    session_id = new_id("session")
    if requirements.missing_information:
        try:
            sessions.save_decision(
                session_id,
                requirements.model_dump(),
                [],
                requirements.missing_information,
            )
            session_persisted = True
        except Exception:
            session_persisted = False
        return {
            "request_id": request_id,
            "session_id": session_id,
            "requirements": requirements.model_dump(),
            "products": [],
            "comparisons": [],
            "tradeoffs": [],
            "warnings": (
                []
                if session_persisted
                else ["Clarification state could not be persisted to Firestore."]
            ),
            "sources": [],
            "clarification_needed": requirements.missing_information,
            "ai": {
                "provider": "Google ADK + Gemini",
                "status": "clarification_required",
            },
            "session_persisted": session_persisted,
        }

    product_ids = [product["id"] for product in catalog.list_products(category="FD")]
    result = compare_products(
        catalog, product_ids, requirements.amount, requirements.duration_months
    )
    explanation = await run_decision_agent(
        safe_query, requirements.model_dump(), result
    )
    try:
        sessions.save_decision(
            session_id, requirements.model_dump(), result["products"]
        )
        session_persisted = True
    except Exception:
        session_persisted = False
        result["warnings"].append(
            "Decision completed, but Firestore session persistence was unavailable."
        )
    ai_status = (
        "completed"
        if explanation
        else ("unavailable" if GOOGLE_CLOUD_PROJECT else "not_configured")
    )
    return {
        "request_id": request_id,
        "session_id": session_id,
        "requirements": requirements.model_dump(),
        "products": [item["product"] for item in result["products"]],
        "comparisons": result["products"],
        "tradeoffs": [
            item["tradeoff"] for item in result["products"] if item.get("tradeoff")
        ],
        "warnings": result["warnings"],
        "sources": list(
            {
                source["id"]: source
                for item in result["products"]
                for source in item["product"]["sources"]
            }.values()
        ),
        "explanation": explanation,
        "ai": {
            "provider": "Google ADK + Gemini",
            "agent": "bankwise_decision_agent",
            "status": ai_status,
        },
        "clarification_needed": [],
        "session_persisted": session_persisted,
    }


@router.get("/api/sessions/{session_id}")
def get_decision_session(
    session_id: str, sessions: FirestoreSessionRepository = Depends(get_sessions)
):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Decision session not found")
    return session
