"""Shared source grounded decision workflow used by natural language routes."""

from app.domain.identifiers import new_id
from app.domain.input import (
    extract_requirements_from_safe_query as extract_requirements,
)
from app.domain.input import (
    redact_sensitive_input,
)


async def run_decision_workflow(query: str, catalog, sessions, user_id: str) -> dict:
    """Build a deterministic comparison and persist only redacted decision data."""
    safe_query = redact_sensitive_input(query)
    # Deterministic parsing keeps request handling bounded and makes numeric
    # requirements independent from model availability or output.
    requirements = extract_requirements(safe_query, use_gemini=False)
    request_id = new_id("req")
    session_id = new_id("session")

    if requirements.missing_information:
        sessions.save_decision(
            session_id,
            user_id,
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
            "ai": {"provider": "deterministic API", "status": "not_used"},
            "session_persisted": True,
        }

    from app.domain.comparison import compare_products

    product_ids = [product["id"] for product in catalog.list_products(category="FD")]
    result = compare_products(
        catalog, product_ids, requirements.amount, requirements.duration_months
    )
    sessions.save_decision(
        session_id, user_id, requirements.model_dump(), result["products"]
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
        "explanation": None,
        "ai": {"provider": "deterministic API", "status": "not_used"},
        "clarification_needed": [],
        "session_persisted": True,
    }
