"""Focused service operations: catalog."""

from datetime import date, datetime

from app.domain.sources import freshness, rate_is_usable


def _isoformat(value):
    return value.isoformat() if isinstance(value, (date, datetime)) else value


def product_payload(
    product: dict, catalog, amount: float | None = None, tenure: int | None = None
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
                "calculation_source_url": rate.get("calculation_source_url"),
                "source_id": rate.get("source_id"),
                "effective_from": _isoformat(rate.get("effective_from")),
                "effective_to": _isoformat(rate.get("effective_to")),
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
                "source_url": c.get("source_url"),
            }
            for c in product.get("conditions", [])
        ],
        "sources": [
            {
                "id": s["id"],
                "type": s["source_type"],
                "url": s["url"],
                "title": s["title"],
                "reference": s.get("reference"),
                "retrieved_at": _isoformat(s.get("retrieved_at")),
                "verified_at": _isoformat(s.get("verified_at")),
                "effective_from": _isoformat(s.get("effective_from")),
                "freshness": freshness(s),
            }
            for s in product.get("sources", [])
        ],
        "conflicts": [
            {
                "id": conflict["id"],
                "field": conflict["field_name"],
                "value_a": conflict.get("value_a"),
                "source_a": conflict.get("source_a"),
                "value_b": conflict.get("value_b"),
                "source_b": conflict.get("source_b"),
                "source_b_url": conflict.get("source_b_url"),
                "note": conflict.get("note"),
            }
            for conflict in catalog.get_conflicts(product["id"])
        ],
    }
