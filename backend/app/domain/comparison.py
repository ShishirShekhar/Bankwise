"""Focused service operations: comparison."""

from app.calculators.fd import calculate_fd
from app.domain.catalog import product_payload
from app.domain.sources import rate_is_usable


def compare_products(catalog, product_ids: list, amount: float, tenure: int) -> dict:
    results = []
    for product_id in dict.fromkeys(product_ids):
        product = catalog.get_product(product_id, status="ACTIVE")
        if product is None:
            continue
        payload = product_payload(product, catalog, amount, tenure)
        eligible_rates = [
            r
            for r in product.get("rates", [])
            if (
                r.get("tenure_months") == tenure
                or (
                    r.get("tenure_months") is None
                    and (
                        r.get("tenure_min_months") is None
                        or tenure >= r["tenure_min_months"]
                    )
                    and (
                        r.get("tenure_max_months") is None
                        or tenure <= r["tenure_max_months"]
                    )
                )
            )
            and (r.get("min_amount") is None or amount >= r["min_amount"])
            and (r.get("max_amount") is None or amount <= r["max_amount"])
        ]
        rate = eligible_rates[0] if len(eligible_rates) == 1 else None
        if rate:
            ok, reason = rate_is_usable(catalog, product["id"], rate)
        else:
            ok, reason = False, "No single eligible rate band is available"
        calculation = None
        if ok and rate.get("payout_type", "").upper() == "CUMULATIVE":
            try:
                calculation = calculate_fd(
                    amount, rate["rate"], tenure, rate.get("compounding_frequency")
                )
            except ValueError:
                reason = "Calculation is unavailable for the selected inputs"
                    "Calculation could not be completed for the selected rate configuration."
                )
        if ok and calculation is None:
            reason = "Only cumulative payout calculation is currently supported"
        results.append(
            {
                "product": payload,
                "eligible": bool(rate),
                "calculation": calculation,
                "calculation_blocked_reason": reason if calculation is None else None,
            }
        )
    amounts = [
        (x["product"]["id"], x["calculation"]["maturity_amount"])
        for x in results
        if x["calculation"]
    ]
    if amounts:
        best_id, best = max(amounts, key=lambda item: item[1])
        for item in results:
            calc = item["calculation"]
            item["tradeoff"] = (
                {
                    "maturity_difference_vs_highest": round(
                        best - calc["maturity_amount"], 2
                    ),
                    "is_highest_calculated_maturity": item["product"]["id"] == best_id,
                }
                if calc
                else None
            )
    return {
        "products": results,
        "warnings": (
            []
            if amounts
            else [
                "No products have a current, conflict-free, authoritative rate for this request."
            ]
        ),
    }
