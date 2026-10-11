"""Validated contracts and deterministic coordination for Bankwise's six specialists.

ADK model output is limited to search/explanation language. Trust-critical stages
are executable Python checks and their validated outputs are passed in sequence.
"""

from __future__ import annotations

import asyncio
import inspect
from datetime import UTC, datetime
from typing import Any

from google.api_core.exceptions import GoogleAPIError
from google.auth.exceptions import GoogleAuthError
from google.genai.errors import APIError
from pydantic import BaseModel, ConfigDict, Field

from app.schemas import Requirements


class RequirementOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    requirements: Requirements
    missing: list[str] = Field(default_factory=list)
    clarification_required: bool = False


class ResearchOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    catalogue_count: int = 0
    canonical_evidence_sufficient: bool = False
    rag_invoked: bool = False
    rag_status: str = "not_configured"
    rag_chunks: list[dict[str, Any]] = Field(default_factory=list)
    search_invoked: bool = False
    search_status: str = "not_needed"
    search_sources: list[dict[str, Any]] = Field(default_factory=list)
    search_text: str = ""
    search_suggestions: Any | None = None
    retrieved_at: str | None = None


class VerificationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    eligible_rate_count: int = 0
    excluded_count: int = 0
    evidence_only_count: int = 0
    status: str


class CalculationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: str
    products: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    comparison: dict[str, Any] = Field(default_factory=dict)


class ExplanationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str
    source_urls: list[str] = Field(default_factory=list)
    requirements: Requirements
    comparison_count: int
    warnings: list[str] = Field(default_factory=list)


class UnavailableRagRepository:
    def retrieve(self, query: str):
        raise RuntimeError("RAG provider unavailable")


class UnavailableSearcher:
    def search(self, query: str):
        raise RuntimeError("Search provider unavailable")


class BankwiseAgentWorkflow:
    """Six request-scoped stages; retrieval never becomes canonical rate data."""

    def __init__(self, catalog, rag_repository=None, searcher=None):
        self.catalog = catalog
        self.rag_repository = rag_repository
        self.searcher = searcher
        self.trace: list[str] = []

    def requirements(self, query: str) -> RequirementOutput:
        from app.domain.input import extract_requirements_from_safe_query

        parsed = extract_requirements_from_safe_query(query, use_gemini=False)
        missing = list(parsed.missing_information)
        self.trace.append("requirement")
        return RequirementOutput(
            requirements=parsed, missing=missing, clarification_required=bool(missing)
        )

    async def research(self, query: str, requirements: RequirementOutput) -> ResearchOutput:
        from app.domain.input import redact_sensitive_input

        query = redact_sensitive_input(query)
        product_category = requirements.requirements.product_category
        products = self.catalog.list_products(category=product_category)
        self.trace.append("research.catalogue")
        canonical_sufficient = False
        amount = requirements.requirements.amount
        tenure = requirements.requirements.duration_months
        if amount is not None and tenure is not None:
            from app.domain.rates import matching_rates
            from app.domain.sources import rate_is_usable

            for product in products:
                matches = matching_rates(product.get("rates", []), amount, tenure)
                if len(matches) == 1 and rate_is_usable(self.catalog, product["id"], matches[0])[0]:
                    canonical_sufficient = True
                    break
        rag_chunks = []
        rag_invoked = False
        rag_status = "not_configured"
        if self.rag_repository is not None:
            rag_invoked = True
            rag_query = (f"Fixed deposit amount {requirements.requirements.amount} INR, "
                         f"tenure {requirements.requirements.duration_months} months; "
                         "rate slabs, effective dates, compounding and premature withdrawal conditions. "
                         f"Research intent: {query[:1000]}")
            try:
                rag_chunks = await _invoke(self.rag_repository.retrieve, rag_query)
                rag_status = "succeeded_with_matches" if rag_chunks else "succeeded_empty"
            except (GoogleAPIError, GoogleAuthError, APIError, RuntimeError, OSError, ValueError, TimeoutError):
                # Search may still be attempted; failure is represented explicitly.
                rag_chunks = []
                rag_status = "failed"
                search_status = "rag_failed"
            self.trace.append("research.rag")
        search_invoked = False
        search_sources: list[dict[str, Any]] = []
        search_text = ""
        search_suggestions = None
        if rag_chunks:
            search_status = "not_needed"
        elif canonical_sufficient:
            search_status = "not_needed_catalogue_sufficient"
        elif self.rag_repository is None:
            search_status = "rag_unavailable"
        elif "search_status" not in locals():
            search_status = "unavailable"
        retrieved_at = None
        # Catalog facts are still separately verified before calculation. Search is
        # required when the RAG corpus has no currently eligible evidence.
        if not rag_chunks and not canonical_sufficient and self.searcher is not None:
            search_invoked = True
            self.trace.append("research.search")
            try:
                found = await _invoke(self.searcher.search, query)
                search_sources = found.get("sources", [])
                search_text = found.get("text", "")
                search_suggestions = found.get("search_suggestions")
                retrieved_at = found.get("retrieved_at") or datetime.now(UTC).isoformat()
                search_status = "grounded" if search_sources else "no_grounded_sources"
            except (GoogleAPIError, GoogleAuthError, APIError, RuntimeError, OSError, ValueError, TimeoutError) as exc:
                # Never imply a fresh search succeeded; curated data remains independently usable.
                search_status = f"failed:{type(exc).__name__}"
        self.trace.append("research.complete")
        return ResearchOutput(catalogue_count=len(products), canonical_evidence_sufficient=canonical_sufficient,
                              rag_invoked=rag_invoked, rag_status=rag_status,
                              rag_chunks=rag_chunks, search_invoked=search_invoked,
                              search_status=search_status, search_sources=search_sources,
                              search_text=search_text, search_suggestions=search_suggestions,
                              retrieved_at=retrieved_at)

    def verify(self, catalog_products: list[dict], research: ResearchOutput) -> VerificationOutput:
        from app.domain.sources import rate_is_usable

        usable = excluded = 0
        for product in catalog_products:
            for rate in product.get("rates", []):
                eligible, _reason = rate_is_usable(self.catalog, product["id"], rate)
                if eligible:
                    usable += 1
                else:
                    excluded += 1
        self.trace.append("verification")
        return VerificationOutput(eligible_rate_count=usable, excluded_count=excluded,
                                  evidence_only_count=len(research.rag_chunks) + len(research.search_sources),
                                  status="CHECKED")

    def calculate(self, requirements: RequirementOutput) -> CalculationOutput:
        from app.domain.comparison import compare_products

        category = requirements.requirements.product_category
        products = self.catalog.list_products(category=category or "FD") if category == "FD" else []
        compared = compare_products(self.catalog, [p["id"] for p in products],
                                    requirements.requirements.amount,
                                    requirements.requirements.duration_months)
        self.trace.append("calculation")
        return CalculationOutput(
            status="CALCULATED" if compared["products"] else "UNAVAILABLE",
            products=compared["products"],
            warnings=compared["warnings"],
            comparison=compared,
        )

    def explain(
        self, decision: dict, requirements: Requirements, research: ResearchOutput
    ) -> ExplanationOutput:
        urls = {
            source["url"]
            for item in decision.get("products", [])
            for source in item.get("product", {}).get("sources", [])
            if source.get("url")
        }
        urls.update(
            source["url"]
            for source in research.search_sources
            if source.get("url")
        )
        self.trace.append("explanation")
        # The deterministic API response adapter composes primary user-facing prose.
        # This output carries only source references for downstream context.
        return ExplanationOutput(
            text="",
            source_urls=sorted(urls),
            requirements=requirements,
            comparison_count=len(decision.get("products", [])),
            warnings=decision.get("warnings", []),
        )


async def _invoke(function, *args):
    if inspect.iscoroutinefunction(function):
        return await function(*args)
    return await asyncio.to_thread(function, *args)
