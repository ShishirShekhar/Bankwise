"""Focused service operations: sources."""

from datetime import datetime, timedelta, timezone

from app.config import SOURCE_MAX_AGE_DAYS


def freshness(source: dict) -> str:
    if source.get("status") != "ACTIVE":
        return "LOW"
    checked = source.get("verified_at") or source.get("retrieved_at")
    if not checked:
        return "LOW"
    if checked.tzinfo is None:
        checked = checked.replace(tzinfo=timezone.utc)
    if checked < datetime.now(timezone.utc) - timedelta(days=SOURCE_MAX_AGE_DAYS):
        return "LOW"
    return (
        "HIGH"
        if source.get("source_type", "").upper().startswith("OFFICIAL_BANK")
        else "MEDIUM"
    )


def rate_is_usable(catalog, product_id: str, rate: dict) -> tuple:
    if catalog.get_conflicts(product_id, field_name="rate"):
        return False, "Rate has an unresolved source conflict"
    if rate.get("verification_status") != "HIGH":
        return False, "Rate is not verified at HIGH confidence"
    today = datetime.now(timezone.utc).date()
    if rate.get("effective_from") and rate["effective_from"] > today:
        return False, "Rate is not effective yet"
    if rate.get("effective_to") and rate["effective_to"] < today:
        return False, "Rate has expired"
    source = (
        catalog.get_source(rate.get("source_id")) if rate.get("source_id") else None
    )
    if not source or freshness(source) != "HIGH":
        return False, "Rate does not have a current official source"
    return True, None
