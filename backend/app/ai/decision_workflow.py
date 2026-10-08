"""Shared source grounded decision workflow used by natural language routes."""

from app.ai.orchestrator import run_decision_agent
from app.config import GOOGLE_CLOUD_PROJECT
from app.domain.identifiers import new_id
from app.domain.input import (
    extract_requirements_from_safe_query as extract_requirements,
)
from app.domain.input import (
    redact_sensitive_input,
)


async def run_decision_workflow(query: str, catalog, sessions) -> dict:
    """Build a deterministic comparison, then use ADK to explain checked results."""
    safe_query = redact_sensitive_input(query)
    requirements = extract_requirements(safe_query)
    request_id = new_id("req")
    session_id = new_id("session")

    if requirements.missing_information:
        sessions.save_decision(
            session_id,
            requirements.model_dump(),
            [],
            requirements.missing_information,
        )
        return {
            "request_id": request_id,
            "session_id": session_id,
            "requirements": requirements.model_dump(),
            "products": [],
            "comparisons": [],
            "tradeoffs": [],
            "tradeoff_summary": None,
            "warnings": [],
            "sources": [],
            "clarification_needed": requirements.missing_information,
            "ai": {
                "provider": "Google ADK + Gemini",
                "status": "clarification_required",
            },
            "session_persisted": True,
        }

    from app.domain.comparison import compare_products

    product_ids = [product["id"] for product in catalog.list_products(category="FD")]
    result = compare_products(
        catalog, product_ids, requirements.amount, requirements.duration_months
    )
    explanation = await run_decision_agent(
        safe_query, requirements.model_dump(), result
    )

    sessions.save_decision(session_id, requirements.model_dump(), result["products"])

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
        "tradeoff_summary": result.get("tradeoff_summary"),
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
        "session_persisted": True,
    }
