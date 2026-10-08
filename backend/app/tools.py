"""ADK tools for requirement extraction, product research, verification, and calculation."""

from datetime import date, datetime

from app.api.dependencies import get_catalog
from app.domain.catalog import conflict_payload, product_payload, source_payload
from app.domain.input import extract_requirements
from app.domain.rates import calculate_product_fd


def _isoformat(value):
    return value.isoformat() if isinstance(value, (date, datetime)) else value


def extract_requirements_tool(query: str) -> dict:
    """Extract stated FD requirements and explicitly report missing amount or duration."""
    return extract_requirements(query, use_gemini=False).model_dump()


def search_products_tool(amount: float, tenure_months: int) -> dict:
    """Find FD products for the requested amount and tenure, including source status."""
    catalog = get_catalog()
    products = catalog.list_products(category="FD", status="ACTIVE")
    return {
        "products": [
            product_payload(product, catalog, amount, tenure_months)
            for product in products
        ]
    }


def verify_product_tool(product_id: str) -> dict:
    """Check stored source freshness and return open conflicts for a product."""
    catalog = get_catalog()
    product = catalog.get_product(product_id)
    if not product:
        return {"product_id": product_id, "status": "MISSING"}
    conflicts = catalog.get_conflicts(product_id)
    return {
        "product_id": product_id,
        "status": "CONFLICT" if conflicts else "CHECKED",
        "conflicts": [conflict_payload(c) for c in conflicts],
        "sources": [source_payload(s) for s in product["sources"]],
    }


def calculate_fd_tool(product_id: str, principal: float, tenure_months: int) -> dict:
    """Calculate FD maturity with Bankwise's deterministic calculator.

    Always call this tool for maturity amounts or interest earned; never do the
    arithmetic yourself. It uses only the product's single eligible rate band
    backed by a current, conflict-free official source.

    Args:
        product_id: Bankwise FD product id from search_products_tool, for
            example "hdfc-bank-regular-fixed-deposit".
        principal: Deposit amount in Indian rupees, for example 500000.
        tenure_months: Deposit tenure in whole months, for example 24.

    Returns:
        A dict with ``status``. CALCULATED includes ``result`` exactly as the
        calculator returned it (maturity_amount, interest_earned,
        calculation_version, warnings). INVALID_INPUT, MISSING, UNAVAILABLE,
        BLOCKED, and UNSUPPORTED include a ``reason``; report it instead of a
        number.
    """
    return calculate_product_fd(
        get_catalog(), product_id, principal, tenure_months
    )
