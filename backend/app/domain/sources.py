"""Focused service operations: sources."""

from datetime import datetime, timedelta, timezone

from app.config import SOURCE_MAX_AGE_DAYS


def source_confidence(source: dict) -> str:
    """Authority of the source type alone: official bank sources are HIGH."""
    return (
        "HIGH"
        if (source.get("source_type") or "").upper().startswith("OFFICIAL_BANK")
        else "MEDIUM"
    )


def freshness(source: dict) -> str:
    """Verification status: source confidence, downgraded to LOW if inactive or stale."""
    if source.get("status") != "ACTIVE":
        return "LOW"
    checked = source.get("verified_at") or source.get("retrieved_at")
    if not checked:
        return "LOW"
    if checked.tzinfo is None:
        checked = checked.replace(tzinfo=timezone.utc)
    if checked < datetime.now(timezone.utc) - timedelta(days=SOURCE_MAX_AGE_DAYS):
        return "LOW"
    return source_confidence(source)


def condition_is_verified(catalog, condition: dict) -> tuple:
    """A condition is verified only when it links to a current official source."""
    source_id = condition.get("source_id")
    if not source_id:
        return False, "Condition has no linked source"
    source = catalog.get_source(source_id)
    if not source:
        return False, "Linked source was not found"
    if freshness(source) != "HIGH":
        return False, "Condition does not have a current official source"
    return True, None


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
