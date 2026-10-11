"""Shared source grounded decision workflow used by natural language routes."""

from app.domain.identifiers import new_id
from app.domain.input import (
    extract_requirements_from_safe_query as extract_requirements,
)
from app.domain.input import (
    redact_sensitive_input,
)


async def run_decision_workflow(query: str, catalog, sessions, user_id: str, rag_repository=None, searcher=None) -> dict:
    """Build a deterministic comparison and persist only redacted decision data."""
    safe_query = redact_sensitive_input(query)
    # Deterministic parsing keeps request handling bounded and makes numeric
    # requirements independent from model availability or output.
    requirements = extract_requirements(safe_query, use_gemini=False)
    request_id = new_id("req")
    session_id = new_id("session")

    if requirements.product_category != "FD":
        sessions.save_decision(session_id, user_id, requirements.model_dump(), [], [])
        return {
            "request_id": request_id, "session_id": session_id,
            "requirements": requirements.model_dump(), "products": [], "comparisons": [],
            "tradeoffs": [], "tradeoff_summary": None, "warnings": [], "sources": [],
            "clarification_needed": [], "explanation": None,
            "ai": {"provider": "deterministic API", "status": "not_used"},
            "session_persisted": True,
            "research": {"rag_invoked": False, "search_invoked": False, "search_status": "not_needed"},
        }

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
            "research": {"rag_invoked": False, "search_invoked": False, "search_status": "not_needed"},
        }

    # Research is a separate evidence path. Its output is never merged into the
    # catalogue and therefore cannot supply rates to the calculator.
    from app.ai.specialists import BankwiseAgentWorkflow

    specialists = BankwiseAgentWorkflow(catalog, rag_repository, searcher)
    specialists.trace.append("orchestrator.start")
    requirement_output = specialists.requirements(safe_query)
    research_output = await specialists.research(safe_query, requirement_output)
    catalog_products = catalog.list_products(category="FD")
    verification_output = specialists.verify(catalog_products, research_output)

    calculation_output = specialists.calculate(requirement_output)
    result = calculation_output.comparison
    specialists.explain(result, requirements, research_output)
    from app.ai.orchestrator import run_decision_agent
    from app.config import ENABLE_ADK_EXPLANATION, GOOGLE_CLOUD_PROJECT

    ai_explanation = None
    ai_status = "not_used"
    if ENABLE_ADK_EXPLANATION and GOOGLE_CLOUD_PROJECT:
        decision_context = {
            "requirements": requirements.model_dump(),
            "products": result["products"],
            "tradeoff_summary": result.get("tradeoff_summary"),
            "warnings": result.get("warnings", []),
            "verified_sources": [
                source
                for item in result["products"]
                for source in item["product"].get("sources", [])
            ],
        }
        ai_explanation = await run_decision_agent(safe_query, requirements.model_dump(), decision_context)
        headings = (
            "Executive Decision Summary",
            "The Key Trade-off",
            "Conditions & Transparency",
        )
        if ai_explanation and all(heading.lower() in ai_explanation.lower() for heading in headings):
            ai_status = "generated"
        else:
            ai_explanation = None
            ai_status = "unavailable"
    sessions.save_decision(
        session_id, user_id, requirements.model_dump(), result["products"]
    )

    rag_sources = {
        chunk.get("document_id"): {
            "id": "rag-" + str(chunk.get("document_id")),
            "url": chunk.get("canonical_url"),
            "title": chunk.get("title") or chunk.get("canonical_url"),
            "source_type": "RAG_SOURCE_DOCUMENT",
            "retrieved_at": chunk.get("retrieved_at"),
            "verified_at": None,
            "verification_status": chunk.get("verification_status", "PENDING"),
        }
        for chunk in research_output.rag_chunks
        if chunk.get("document_id") and chunk.get("canonical_url")
    }
    external_sources = list(rag_sources.values()) + [
        {
            "id": "search-" + str(index), "url": item["url"],
            "title": item.get("title") or item["url"], "source_type": "GOOGLE_SEARCH_GROUNDING",
            "retrieved_at": research_output.retrieved_at,
            "verified_at": None, "verification_status": "PENDING",
        }
        for index, item in enumerate(research_output.search_sources)
        if item.get("url")
    ]
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
        ) + external_sources,
        "explanation": None,
        "ai": {
            "provider": "Google ADK explanation agent" if ai_status == "generated" else "deterministic API",
            "status": ai_status,
            "explanation": ai_explanation,
        },
        "clarification_needed": [],
        "session_persisted": True,
        "research": {
            **research_output.model_dump(),
            "evidence_status": "EVIDENCE_ONLY_NOT_ELIGIBLE_FOR_FINANCIAL_CALCULATIONS",
            "stage_order": specialists.trace,
            "verification": verification_output.model_dump(),
        },
    }
