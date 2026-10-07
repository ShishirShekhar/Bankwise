"""Focused service operations: catalog."""

from datetime import date, datetime

from app.domain.sources import (
    VerificationStatus,
    condition_verification,
    freshness,
    rate_verification,
    source_confidence,
    source_is_stale,
    source_issues,
)


def _isoformat(value):
    return value.isoformat() if isinstance(value, (date, datetime)) else value


def source_payload(source: dict) -> dict:
    """Provenance shown for a source wherever it is returned by the API or tools."""
    return {
        "id": source["id"],
        "type": source["source_type"],
        "url": source["url"],
        "title": source["title"],
        "reference": source.get("reference"),
        "retrieved_at": _isoformat(source.get("retrieved_at")),
        "verified_at": _isoformat(source.get("verified_at")),
        "effective_from": _isoformat(source.get("effective_from")),
        "effective_to": _isoformat(source.get("effective_to")),
        "confidence": source_confidence(source),
        "verification_status": freshness(source),
        "freshness": freshness(source),
        "stale": source_is_stale(source),
        "verification_issues": source_issues(source),
    }


def conflict_payload(conflict: dict) -> dict:
    """Both observed values and sources, so a conflict can be shown, not hidden."""
    return {
        "id": conflict["id"],
        "product_id": conflict.get("product_id"),
        "field": conflict["field_name"],
        "key": conflict.get("key"),
        "rate_id": conflict.get("rate_id"),
        "value_a": conflict.get("value_a"),
        "source_a": conflict.get("source_a"),
        "value_b": conflict.get("value_b"),
        "source_b": conflict.get("source_b"),
        "source_b_url": conflict.get("source_b_url"),
        "note": conflict.get("note"),
        "status": conflict.get("status"),
        "detected_at": _isoformat(conflict.get("detected_at")),
        "resolved_value": conflict.get("resolved_value"),
        "resolved_at": _isoformat(conflict.get("resolved_at")),
        "resolution_notes": conflict.get("resolution_notes"),
    }


def condition_payload(condition: dict, catalog, product_id: str) -> dict:
    status, reason = condition_verification(catalog, product_id, condition)
    source = catalog.get_source(condition.get("source_id"))
    return {
        "type": condition["condition_type"],
        "value": condition["condition_value"],
        "verification_status": status,
        "source_id": condition.get("source_id"),
        "source_url": condition.get("source_url") or (source or {}).get("url"),
        "verified": status == VerificationStatus.HIGH,
        "unverified_reason": reason,
    }


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
        status, reason = rate_verification(catalog, product["id"], rate)
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
                "verification_status": status,
                "verification_reason": reason,
                "usable_for_calculation": status == VerificationStatus.HIGH,
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
            condition_payload(c, catalog, product["id"])
            for c in product.get("conditions", [])
        ],
        "sources": [source_payload(s) for s in product.get("sources", [])],
        "conflicts": [
            conflict_payload(conflict)
            for conflict in catalog.get_conflicts(product["id"])
        ],
    }
