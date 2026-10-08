"""Product discovery, comparison, and deterministic calculation routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_catalog
from app.domain.catalog import product_payload
from app.domain.comparison import compare_products
from app.domain.rates import calculate_product_fd
from app.schemas import CompareRequest, FDCalculationRequest

router = APIRouter()


@router.get("/api/products")
def list_products(
    catalog: Annotated[Any, Depends(get_catalog)],
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
    product_id: str,
    catalog: Annotated[Any, Depends(get_catalog)],
):
    product = catalog.get_product(product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    return product_payload(product, catalog)


@router.get("/api/products/{product_id}/sources")
def get_product_sources(
    product_id: str,
    catalog: Annotated[Any, Depends(get_catalog)],
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
    catalog: Annotated[Any, Depends(get_catalog)],
):
    if not request.product_id:
        raise HTTPException(
            422,
            "Calculations require a product_id so the rate and source can be verified",
        )
    outcome = calculate_product_fd(
        catalog, request.product_id, request.principal, request.tenure_months
    )
    status = outcome["status"]
    if status == "CALCULATED":
        return outcome["result"]
    if status == "MISSING":
        raise HTTPException(404, outcome["reason"])
    if status == "BLOCKED":
        raise HTTPException(409, "Calculation blocked: " + outcome["reason"])
    raise HTTPException(422, outcome["reason"])


@router.post("/api/compare")
def compare_endpoint(
    request: CompareRequest,
    catalog: Annotated[Any, Depends(get_catalog)],
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
