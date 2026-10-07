"""Product discovery, comparison, and deterministic calculation routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_catalog
from app.calculators.fd import CalculationError, calculate_fd
from app.domain.catalog import product_payload
from app.domain.comparison import compare_products
from app.domain.sources import rate_is_usable

# from app.repositories.local_json import LocalJsonCatalog
from app.repositories.bigquery import BigQueryRepository
from app.schemas import CompareRequest, FDCalculationRequest

router = APIRouter()


@router.get("/api/products")
def list_products(
    # catalog: Annotated[LocalJsonCatalog, Depends(get_catalog)],
    catalog: Annotated[BigQueryRepository, Depends(get_catalog)],
    category: str = "FD",
    amount: float = Query(default=None, gt=0),
    tenure_months: int = Query(default=None, alias="tenureMonths", gt=0),
):
    products = catalog.list_products(category=category.upper())
    return {
        "products": [
            product_payload(product, catalog, amount, tenure_months)
            for product in products
        ]
    }


@router.get("/api/products/{product_id}")
def get_product(
    # product_id: str, catalog: Annotated[LocalJsonCatalog, Depends(get_catalog)]
    product_id: str, catalog: Annotated[BigQueryRepository, Depends(get_catalog)]
):
    product = catalog.get_product(product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    return product_payload(product, catalog)


@router.get("/api/products/{product_id}/sources")
def get_product_sources(
    # product_id: str, catalog: Annotated[LocalJsonCatalog, Depends(get_catalog)]
    product_id: str, catalog: Annotated[BigQueryRepository, Depends(get_catalog)]
):
    product = catalog.get_product(product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    return {
        "product_id": product_id,
        "sources": product_payload(product, catalog)["sources"],
    }


@router.post("/api/calculations/fd")
def calculate_fd_endpoint(
    request: FDCalculationRequest,
    # catalog: Annotated[LocalJsonCatalog, Depends(get_catalog)],
    catalog: Annotated[BigQueryRepository, Depends(get_catalog)],
):
    if not request.product_id:
        raise HTTPException(
            422,
            "Calculations require a product_id so the rate and source can be verified",
        )
    product = catalog.get_product(request.product_id, category="FD", status="ACTIVE")
    if not product:
        raise HTTPException(404, "FD product not found")
    matching = [
        rate
        for rate in product["rates"]
        if (
            rate.get("tenure_months") == request.tenure_months
            or (
                rate.get("tenure_months") is None
                and (
                    rate.get("tenure_min_months") is None
                    or request.tenure_months >= rate["tenure_min_months"]
                )
                and (
                    rate.get("tenure_max_months") is None
                    or request.tenure_months <= rate["tenure_max_months"]
                )
            )
        )
        and (rate.get("min_amount") is None or request.principal >= rate["min_amount"])
        and (rate.get("max_amount") is None or request.principal <= rate["max_amount"])
    ]
    if len(matching) != 1:
        raise HTTPException(
            422, "No unique rate matches the supplied amount and tenure"
        )
    rate = matching[0]
    usable, reason = rate_is_usable(catalog, product["id"], rate)
    if not usable:
        raise HTTPException(409, "Calculation blocked: " + str(reason))
    if (rate.get("payout_type") or "").upper() != "CUMULATIVE":
        raise HTTPException(
            422, "The local data does not specify a cumulative payout type"
        )
    try:
        return calculate_fd(
            request.principal,
            rate["rate"],
            request.tenure_months,
            rate.get("compounding_frequency"),
        )
    except CalculationError as exc:
        raise HTTPException(422, str(exc))


@router.post("/api/compare")
def compare_endpoint(
    request: CompareRequest,
    # catalog: Annotated[LocalJsonCatalog, Depends(get_catalog)],
    catalog: Annotated[BigQueryRepository, Depends(get_catalog)],
):
    if (
        request.requirements.amount is None
        or request.requirements.duration_months is None
    ):
        raise HTTPException(
            422, "Amount and duration_months are required to compare products"
        )
    return compare_products(
        catalog,
        request.product_ids,
        request.requirements.amount,
        request.requirements.duration_months,
    )
