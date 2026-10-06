"""Source verification: authority, freshness, effective dates, and conflicts.

Every financial fact gets one ``VerificationStatus``. Only HIGH facts may be
used as authoritative by decision logic.
"""

from datetime import datetime, timedelta, timezone
from enum import StrEnum

from app.config import SOURCE_MAX_AGE_DAYS


class VerificationStatus(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    CONFLICT = "CONFLICT"
    MISSING = "MISSING"


# Worst first; a fact takes the worst status found by any check.
_SEVERITY = [
    VerificationStatus.MISSING,
    VerificationStatus.CONFLICT,
    VerificationStatus.LOW,
    VerificationStatus.MEDIUM,
    VerificationStatus.HIGH,
]


def _worst(*statuses: str) -> VerificationStatus:
    return min((VerificationStatus(s) for s in statuses), key=_SEVERITY.index)


def _today():
    return datetime.now(timezone.utc).date()


def source_confidence(source: dict) -> str:
    """Authority of the source type alone: official bank sources are HIGH."""
    return (
        VerificationStatus.HIGH
        if (source.get("source_type") or "").upper().startswith("OFFICIAL_BANK")
        else VerificationStatus.MEDIUM
    )


def source_is_stale(source: dict) -> bool:
    """True when the source has no check date or was checked too long ago."""
    checked = source.get("verified_at") or source.get("retrieved_at")
    if not checked:
        return True
    if checked.tzinfo is None:
        checked = checked.replace(tzinfo=timezone.utc)
    return checked < datetime.now(timezone.utc) - timedelta(days=SOURCE_MAX_AGE_DAYS)


def source_issues(source: dict) -> list[str]:
    """Reasons a source cannot be relied on as current; empty when it can."""
    issues = []
    if source.get("status") != "ACTIVE":
        issues.append("Source is not active")
    if not (source.get("verified_at") or source.get("retrieved_at")):
        issues.append("Source has no retrieval or verification date")
    elif source_is_stale(source):
        issues.append(
            f"Source was last checked more than {SOURCE_MAX_AGE_DAYS} days ago"
        )
    if source.get("effective_from") and source["effective_from"] > _today():
        issues.append("Source is not effective yet")
    if source.get("effective_to") and source["effective_to"] < _today():
        issues.append("Source has expired")
    return issues


def freshness(source: dict) -> str:
    """Verification status of a source: its confidence, or LOW if it has issues."""
    return (
        VerificationStatus.LOW if source_issues(source) else source_confidence(source)
    )


def _verify_fact(catalog, product_id: str, field_name: str, fact: dict, label: str):
    """Shared checks for a sourced fact. Returns (status, reason or None)."""
    if catalog.get_conflicts(product_id, field_name=field_name):
        return VerificationStatus.CONFLICT, f"{label} has an unresolved source conflict"
    source_id = fact.get("source_id")
    source = catalog.get_source(source_id) if source_id else None
    if not source_id:
        return VerificationStatus.MISSING, f"{label} has no linked source"
    if not source:
        return VerificationStatus.MISSING, "Linked source was not found"
    status = freshness(source)
    if status != VerificationStatus.HIGH:
        return status, f"{label} does not have a current official source"
    return VerificationStatus.HIGH, None


def rate_verification(catalog, product_id: str, rate: dict) -> tuple:
    """Verification status of one rate band, with the reason it is not HIGH."""
    status, reason = _verify_fact(catalog, product_id, "rate", rate, "Rate")
    if status in (VerificationStatus.CONFLICT, VerificationStatus.MISSING):
        return status, reason
    stored = rate.get("verification_status")
    if stored not in VerificationStatus.__members__:
        stored = VerificationStatus.LOW
    if stored != VerificationStatus.HIGH:
        return _worst(stored, status), "Rate is not verified at HIGH confidence"
    if rate.get("effective_from") and rate["effective_from"] > _today():
        return VerificationStatus.LOW, "Rate is not effective yet"
    if rate.get("effective_to") and rate["effective_to"] < _today():
        return VerificationStatus.LOW, "Rate has expired"
    return status, reason


def rate_is_usable(catalog, product_id: str, rate: dict) -> tuple:
    """Only HIGH rates may be used for authoritative calculations."""
    status, reason = rate_verification(catalog, product_id, rate)
    return status == VerificationStatus.HIGH, reason


def condition_verification(catalog, product_id: str, condition: dict) -> tuple:
    """Verification status of one product condition (penalty, limit, ...)."""
    return _verify_fact(
        catalog, product_id, condition["condition_type"], condition, "Condition"
    )
