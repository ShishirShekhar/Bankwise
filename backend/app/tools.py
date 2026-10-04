"""ADK tools for requirement extraction, product research, verification, and calculation."""

from app.calculators.fd import CalculationError, calculate_fd
from app.repositories.bigquery import BigQueryRepository
from app.services import extract_requirements, freshness, product_payload, rate_is_usable


def extract_requirements_tool(query: str) -> dict:
    """Extract stated FD requirements and explicitly report missing amount or duration."""
    return extract_requirements(query, use_gemini=False).model_dump()


def search_products_tool(amount: float, tenure_months: int) -> dict:
    """Find FD products for the requested amount and tenure, including source status."""
    catalog = BigQueryRepository()
    products = catalog.list_products(category="FD", status="ACTIVE")
    return {"products": [product_payload(product, catalog, amount, tenure_months) for product in products]}


def verify_product_tool(product_id: str) -> dict:
    """Check stored source freshness and return open conflicts for a product."""
    catalog = BigQueryRepository()
    product = catalog.get_product(product_id)
    if not product:
        return {"product_id": product_id, "status": "MISSING"}
    conflicts = catalog.get_conflicts(product_id)
    return {"product_id": product_id, "status": "CONFLICT" if conflicts else "CHECKED",
            "conflicts": [{"field": c["field_name"], "value_a": c["value_a"], "value_b": c["value_b"],
                           "source_a": c["source_a"], "source_b": c["source_b"]} for c in conflicts],
            "sources": [{"id": s["id"], "title": s["title"], "url": s["url"], "freshness": freshness(s)} for s in product["sources"]]}


def calculate_fd_tool(product_id: str, principal: float, tenure_months: int) -> dict:
    """Calculate only from one eligible rate backed by a current, conflict-free official source."""
    catalog = BigQueryRepository()
    product = catalog.get_product(product_id, category="FD", status="ACTIVE")
    if not product:
        return {"status": "MISSING", "product_id": product_id}
    matches = [rate for rate in product["rates"]
               if (rate.get("tenure_months") == tenure_months or (rate.get("tenure_months") is None
                   and (rate.get("tenure_min_months") is None or tenure_months >= rate["tenure_min_months"])
                   and (rate.get("tenure_max_months") is None or tenure_months <= rate["tenure_max_months"])))
               and (rate.get("min_amount") is None or principal >= rate["min_amount"])
               and (rate.get("max_amount") is None or principal <= rate["max_amount"])]
    if len(matches) != 1:
        return {"status": "UNAVAILABLE", "reason": "No unique eligible rate band"}
    rate = matches[0]
    usable, reason = rate_is_usable(catalog, product["id"], rate)
    if not usable:
        return {"status": "BLOCKED", "reason": reason}
    if rate.get("payout_type", "").upper() != "CUMULATIVE":
        return {"status": "UNSUPPORTED", "reason": "Only cumulative payout is currently supported"}
    try:
        return {"status": "CALCULATED", "product_id": product["id"],
                "result": calculate_fd(principal, rate["rate"], tenure_months, rate.get("compounding_frequency"))}
    except CalculationError as exc:
        return {"status": "BLOCKED", "reason": str(exc)}
