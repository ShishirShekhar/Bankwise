"""Focused service operations: catalog."""

from typing import Optional

from app.domain.sources import freshness, rate_is_usable


def product_payload(
    product: dict, catalog, amount: Optional[float] = None, tenure: Optional[int] = None
) -> dict:
    rates = []
    for rate in product.get("rates", []):
        eligible = True
        if amount is not None and (
            (rate.get("min_amount") is not None and amount < rate["min_amount"])
            or (rate.get("max_amount") is not None and amount > rate["max_amount"])
        ):
            eligible = False
        min_tenure = rate.get("tenure_min_months") or rate.get("tenure_months")
        max_tenure = rate.get("tenure_max_months") or rate.get("tenure_months")
        if tenure is not None and (
            (min_tenure is not None and tenure < min_tenure)
            or (max_tenure is not None and tenure > max_tenure)
        ):
            eligible = False
        usable, reason = rate_is_usable(catalog, product["id"], rate)
        rates.append(
            {
                "id": rate["id"],
                "annual_rate_percent": rate["rate"],
                "min_amount": rate.get("min_amount"),
                "max_amount": rate.get("max_amount"),
                "tenure_months": rate.get("tenure_months"),
                "tenure_min_months": rate.get("tenure_min_months"),
                "tenure_max_months": rate.get("tenure_max_months"),
                "compounding_frequency": rate.get("compounding_frequency"),
                "payout_type": rate.get("payout_type"),
                "effective_from": rate.get("effective_from"),
                "effective_to": rate.get("effective_to"),
                "verification_status": (
                    "CONFLICT"
                    if not usable and reason and "conflict" in reason.lower()
                    else rate.get("verification_status")
                ),
                "usable_for_calculation": usable,
                "ineligibility_reason": (
                    None
                    if eligible
                    else "Amount or tenure is outside the sourced rate band"
                ),
            }
        )
    return {
        "id": product["id"],
        "bank": product["bank"],
        "category": product["category"],
        "name": product["name"],
        "description": product.get("description"),
        "status": product["status"],
        "rates": rates,
        "conditions": [
            {
                "type": c["condition_type"],
                "value": c["condition_value"],
                "verification_status": c.get("verification_status"),
            }
            for c in product.get("conditions", [])
        ],
        "sources": [
            {
                "id": s["id"],
                "type": s["source_type"],
                "url": s["url"],
                "title": s["title"],
                "retrieved_at": s.get("retrieved_at"),
                "verified_at": s.get("verified_at"),
                "freshness": freshness(s),
            }
            for s in product.get("sources", [])
        ],
    }
