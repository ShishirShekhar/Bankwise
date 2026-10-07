"""Detect and resolve disagreements between sources for the same financial fact.

An observation is one source's value for one fact:
``{"product_id", "field_name", "key", "value", "source_id"}``. ``key`` tells
facts of the same field apart (for example a rate band ``"12-23"``). Values are
never chosen silently: any disagreement becomes an OPEN conflict that keeps
both values and both sources until a person resolves it.
"""

import re
from datetime import datetime, timezone

OPEN = "OPEN"
RESOLVED = "RESOLVED"


class ConflictResolutionError(ValueError):
    pass


def normalize_value(value):
    """Comparable form of a value: rounded numbers, trimmed case-folded text."""
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, (int, float)):
        return round(float(value), 4)
    return re.sub(r"\s+", " ", str(value)).strip().casefold()


def _conflict_id(product_id: str, field_name: str, key: str, source_b: str) -> str:
    parts = [product_id, field_name, key, source_b]
    return re.sub(r"[^a-z0-9]+", "-", "-".join(p for p in parts if p).lower()).strip(
        "-"
    )


def detect_conflicts(observations: list[dict], detected_at: datetime | None = None):
    """Return one OPEN conflict per observation that disagrees with the first one."""
    detected_at = detected_at or datetime.now(timezone.utc)
    groups: dict[tuple, list[dict]] = {}
    for observation in observations:
        group = (
            observation["product_id"],
            observation["field_name"],
            observation.get("key") or "",
        )
        groups.setdefault(group, []).append(observation)

    conflicts = []
    for (product_id, field_name, key), group in groups.items():
        first = group[0]
        seen = {normalize_value(first["value"])}
        for other in group[1:]:
            normalized = normalize_value(other["value"])
            if normalized in seen:
                continue
            seen.add(normalized)
            conflicts.append(
                {
                    "id": _conflict_id(product_id, field_name, key, other["source_id"]),
                    "product_id": product_id,
                    "field_name": field_name,
                    "key": key or None,
                    "source_a": first["source_id"],
                    "value_a": first["value"],
                    "source_b": other["source_id"],
                    "value_b": other["value"],
                    "status": OPEN,
                    "detected_at": detected_at,
                    "note": f"Sources disagree on {field_name}"
                    + (f" for {key}" if key else ""),
                    "resolved_value": None,
                    "resolved_at": None,
                    "resolution_notes": None,
                }
            )
    return conflicts


def resolve_conflict(
    conflict: dict,
    resolved_value,
    notes: str,
    resolved_at: datetime | None = None,
) -> dict:
    """Mark a conflict RESOLVED with one of the two observed values.

    A resolution must name a value that a source actually reported and explain
    why; it cannot introduce a new, unsourced value.
    """
    if not notes or not notes.strip():
        raise ConflictResolutionError(
            "A resolution must explain which source is correct"
        )
    observed = {
        normalize_value(conflict["value_a"]): conflict["value_a"],
        normalize_value(conflict["value_b"]): conflict["value_b"],
    }
    if normalize_value(resolved_value) not in observed:
        raise ConflictResolutionError(
            "The resolved value must be one of the values reported by the sources"
        )
    return {
        **conflict,
        "status": RESOLVED,
        "resolved_value": observed[normalize_value(resolved_value)],
        "resolved_at": resolved_at or datetime.now(timezone.utc),
        "resolution_notes": notes.strip(),
    }


def apply_resolutions(conflicts: list[dict], resolutions: list[dict]) -> list[dict]:
    """Apply recorded resolutions, matched by product, field, and key.

    Each resolution is ``{"product_id", "field_name", "key", "resolved_value",
    "resolution_notes", "resolved_at"?}``. Conflicts without a valid matching
    resolution stay OPEN.
    """
    by_group = {
        (r["product_id"], r["field_name"], r.get("key") or None): r for r in resolutions
    }
    result = []
    for conflict in conflicts:
        resolution = by_group.get(
            (conflict["product_id"], conflict["field_name"], conflict.get("key"))
        )
        if resolution is not None:
            try:
                conflict = resolve_conflict(
                    conflict,
                    resolution.get("resolved_value"),
                    resolution.get("resolution_notes") or "",
                    resolution.get("resolved_at"),
                )
            except ConflictResolutionError:
                pass
        result.append(conflict)
    return result
