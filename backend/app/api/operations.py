"""Health and source-verification routes."""

from importlib.util import find_spec
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_catalog
from app.api.security import require_csrf
from app.config import (
    BIGQUERY_PROJECT,
    ENVIRONMENT,
    FIRESTORE_PROJECT,
    GEMINI_MODEL,
    GOOGLE_CLOUD_PROJECT,
)
from app.domain.catalog import conflict_payload
from app.domain.conflicts import OPEN, RESOLVED
from app.domain.sources import (
    condition_verification,
    freshness,
    rate_verification,
    source_is_stale,
    source_issues,
)
from app.schemas import HealthResponse

router = APIRouter()


@router.get("/api/health", response_model=HealthResponse)
def health():
    return {"status": "healthy"}


@router.post("/api/verification/run", dependencies=[Depends(require_csrf)])
def verification_run(
    catalog: Annotated[Any, Depends(get_catalog)],
):
    reports = []
    for product in catalog.list_products(category="FD", status="ACTIVE"):
        conflicts = catalog.get_conflicts(product["id"])
        for rate in product["rates"]:
            status, reason = rate_verification(catalog, product["id"], rate)
            reports.append(
                {
                    "product_id": product["id"],
                    "field": "rate",
                    "rate_id": rate["id"],
                    "status": status,
                    "notes": reason,
                }
            )
        for condition in product.get("conditions", []):
            status, reason = condition_verification(catalog, product["id"], condition)
            reports.append(
                {
                    "product_id": product["id"],
                    "field": condition["condition_type"],
                    "status": status,
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
                    "status": freshness(source),
                    "freshness": freshness(source),
                    "stale": source_is_stale(source),
                    "notes": "; ".join(source_issues(source)) or None,
                }
            )
    return {"checked": len(reports), "records": reports, "web_fetch_performed": False}


@router.get("/api/conflicts")
def list_conflicts(
    catalog: Annotated[Any, Depends(get_catalog)],
    status: str = OPEN,
):
    """Source conflicts for the UI/admin; OPEN ones block the disputed value."""
    status = status.upper()
    if status not in (OPEN, RESOLVED):
        raise HTTPException(422, "status must be OPEN or RESOLVED")
    return {
        "status": status,
        "conflicts": [conflict_payload(c) for c in catalog.list_conflicts(status)],
    }


def _installed(module: str) -> bool:
    try:
        return find_spec(module) is not None
    except (ImportError, ModuleNotFoundError):
        return False


@router.get("/api/agent/health")
def agent_health():
    return {
        "environment": ENVIRONMENT,
        "catalog_source": "bigquery" if ENVIRONMENT == "production" else "local_json",
        "session_store": "firestore" if ENVIRONMENT == "production" else "in_memory",
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
