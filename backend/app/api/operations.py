"""Health and source-verification routes."""

from importlib.util import find_spec

from fastapi import APIRouter, Depends

from app.api.dependencies import get_catalog
from app.config import (
    BIGQUERY_PROJECT,
    FIRESTORE_PROJECT,
    GEMINI_MODEL,
    GOOGLE_CLOUD_PROJECT,
)
from app.repositories.bigquery import BigQueryRepository
from app.schemas import HealthResponse
from app.domain.sources import freshness, rate_is_usable

router = APIRouter()


@router.get("/api/health", response_model=HealthResponse)
def health():
    return {"status": "healthy"}


@router.post("/api/verification/run")
def verification_run(catalog: BigQueryRepository = Depends(get_catalog)):
    reports = []
    for product in catalog.list_products(category="FD", status="ACTIVE"):
        conflicts = catalog.get_conflicts(product["id"])
        for rate in product["rates"]:
            usable, reason = rate_is_usable(catalog, product["id"], rate)
            reports.append(
                {
                    "product_id": product["id"],
                    "field": "rate",
                    "rate_id": rate["id"],
                    "status": (
                        "HIGH"
                        if usable
                        else (
                            "CONFLICT"
                            if reason and "conflict" in reason.lower()
                            else "LOW"
                        )
                    ),
                    "notes": reason,
                }
            )
        for conflict in conflicts:
            reports.append(
                {
                    "product_id": product["id"],
                    "field": conflict["field_name"],
                    "status": "CONFLICT",
                    "conflict_id": conflict["id"],
                }
            )
        for source in product["sources"]:
            reports.append(
                {
                    "product_id": product["id"],
                    "field": "source",
                    "source_id": source["id"],
                    "freshness": freshness(source),
                }
            )
    return {"checked": len(reports), "records": reports, "web_fetch_performed": False}


def _installed(module: str) -> bool:
    try:
        return find_spec(module) is not None
    except (ImportError, ModuleNotFoundError):
        return False


@router.get("/api/agent/health")
def agent_health():
    return {
        "adk_configured": bool(GOOGLE_CLOUD_PROJECT and _installed("google.adk")),
        "gemini_configured": bool(GOOGLE_CLOUD_PROJECT and _installed("google.genai")),
        "bigquery_configured": bool(
            BIGQUERY_PROJECT and _installed("google.cloud.bigquery")
        ),
        "firestore_configured": bool(
            FIRESTORE_PROJECT and _installed("google.cloud.firestore")
        ),
        "model": GEMINI_MODEL,
    }
