"""Rate-band selection and product-backed FD calculation shared by API and ADK tools."""

from app.calculators.fd import CalculationError, calculate_fd
from app.domain.sources import rate_is_usable


def _within_tenure(rate: dict, tenure: int) -> bool:
    if rate.get("tenure_months") is not None:
        return rate["tenure_months"] == tenure
    low, high = rate.get("tenure_min_months"), rate.get("tenure_max_months")
    above_low = (
        low is None
        or tenure > low
        or (rate.get("tenure_min_inclusive", True) and tenure == low)
    )
    below_high = (
        high is None
        or tenure < high
        or (rate.get("tenure_max_inclusive", True) and tenure == high)
    )
    return above_low and below_high


def _within_amount(rate: dict, amount: float) -> bool:
    return (rate.get("min_amount") is None or amount >= rate["min_amount"]) and (
        rate.get("max_amount") is None or amount <= rate["max_amount"]
    )


def matching_rates(rates: list[dict], amount: float, tenure: int) -> list[dict]:
    """Rate bands whose tenure (respecting boundary inclusivity) and amount match."""
    return [
        rate
        for rate in rates
        if _within_tenure(rate, tenure) and _within_amount(rate, amount)
    ]


def calculate_product_fd(
    catalog, product_id: str, principal: float, tenure_months: int
):
    """Calculate maturity for one product from its single eligible, verified rate.

    Returns a dict with ``status`` CALCULATED (and the calculator ``result``
    unchanged), or INVALID_INPUT, MISSING, UNAVAILABLE, BLOCKED, or UNSUPPORTED
    with a ``reason``. No value is ever estimated outside the calculator.
    """
    base = {"product_id": product_id}
    if principal <= 0 or tenure_months <= 0:
        return {
            **base,
            "status": "INVALID_INPUT",
            "reason": "Principal and tenure must be positive",
        }
    product = catalog.get_product(product_id, category="FD", status="ACTIVE")
    if not product:
        return {**base, "status": "MISSING", "reason": "FD product not found"}
    matches = matching_rates(product["rates"], principal, tenure_months)
    if len(matches) != 1:
        return {
            **base,
            "status": "UNAVAILABLE",
            "reason": "No unique rate matches the supplied amount and tenure",
        }
    rate = matches[0]
    usable, reason = rate_is_usable(catalog, product["id"], rate)
    if not usable:
        return {**base, "status": "BLOCKED", "rate_id": rate["id"], "reason": reason}
    if (rate.get("payout_type") or "").upper() != "CUMULATIVE":
        return {
            **base,
            "status": "UNSUPPORTED",
            "rate_id": rate["id"],
            "reason": "The local data does not specify a cumulative payout type",
        }
    try:
        result = calculate_fd(
            principal, rate["rate"], tenure_months, rate.get("compounding_frequency")
        )
    except CalculationError as exc:
        # The sourced terms are incomplete for the calculator (for example no
        # compounding frequency), so no amount can be produced.
        return {
            **base,
            "status": "UNSUPPORTED",
            "rate_id": rate["id"],
            "reason": str(exc),
        }
    return {
        **base,
        "status": "CALCULATED",
        "rate_id": rate["id"],
        "source_id": rate.get("source_id"),
        "result": result,
    }
