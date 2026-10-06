"""Read-only local FD catalogue backed by ``backend/data/fd-products.json``."""

import json
import re
from datetime import date, datetime, timezone
from pathlib import Path

from app.domain.conflicts import (
    RESOLVED,
    apply_resolutions,
    detect_conflicts,
    normalize_value,
)

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "fd-products.json"
_BANK_ALIASES = {"sbi": "State Bank of India"}


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _as_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _as_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.combine(date.fromisoformat(value), datetime.min.time(), timezone.utc)


def _rate_from_row(row: dict, rate_id: str, source_id: str, terms: dict) -> dict:
    return {
        "id": rate_id,
        "rate": row["interest_rate"],
        "min_amount": row.get("minimum_deposit"),
        "max_amount": None,
        "tenure_months": None,
        "tenure_min_months": row.get("tenure_min_months"),
        "tenure_max_months": row.get("tenure_max_months"),
        "tenure_min_inclusive": not row.get("calculation_note", "").lower().startswith("rate applies to above")
        and not (
            "2 years 1 day" in row.get("calculation_note", "").lower()
            and "21 months" not in row.get("calculation_note", "").lower()
        ),
        "tenure_max_inclusive": "less than" not in row.get("calculation_note", "").lower(),
        "compounding_frequency": terms.get("compounding_frequency"),
        "payout_type": terms.get("payout_type"),
        "calculation_source_url": terms.get("calculation_url"),
        "effective_from": _as_date(row.get("source_effective_date")),
        "effective_to": None,
        "verification_status": (
            "HIGH"
            if row.get("freshness_status") == "current_source"
            else "LOW"
        ),
        "source_id": source_id,
    }


class LocalJsonCatalog:
    """Implement the catalogue interface used by comparison and ADK tools."""

    def __init__(self, data_file: Path = DATA_FILE):
        with data_file.open(encoding="utf-8") as file:
            data = json.load(file)
        rows = data.get("products", [])
        source_metadata = data.get("source_metadata", {})
        self._products: dict[str, dict] = {}
        self._sources: dict[str, dict] = {}
        self._conflicts: dict[str, list] = {}
        observations = []

        for row in rows:
            raw_bank = row["bank_name"].strip()
            bank = _BANK_ALIASES.get(raw_bank.lower(), raw_bank)
            product_id = _slug(f"{bank}-{row['product_name']}")
            source_id = _slug(row["source_name"])
            source_reference = row.get("source_reference")
            terms = source_metadata.get(row["source_name"], {})
            source = {
                "id": source_id,
                "source_type": (
                    "OFFICIAL_BANK_PAGE"
                    if source_reference and "official" in source_reference.lower()
                    else "LOCAL_REFERENCE"
                ),
                "url": terms.get("rate_url"),
                "title": row.get("source_name"),
                "reference": source_reference,
                # The dataset records only when a source was last verified; it
                # must have been retrieved to be verified, so use that date.
                "retrieved_at": _as_datetime(row.get("last_verified")),
                "verified_at": _as_datetime(row.get("last_verified")),
                "status": (
                    "ACTIVE"
                    if row.get("freshness_status") == "current_source"
                    else "VERIFY_REQUIRED"
                ),
                "effective_from": _as_date(row.get("source_effective_date")),
            }
            self._sources[source_id] = source

            product = self._products.setdefault(
                product_id,
                {
                    "id": product_id,
                    "bank": bank,
                    "category": row.get("product_type", "FD").upper(),
                    "name": row["product_name"],
                    "description": row.get("calculation_note"),
                    "status": "ACTIVE",
                    "rates": [],
                    "conditions": [],
                    "sources": [],
                },
            )
            if source_id not in {item["id"] for item in product["sources"]}:
                product["sources"].append(source)

            band = f"{row['tenure_min_months']}-{row['tenure_max_months']}"
            rate_id = f"{product_id}-{band}"
            observations.append(
                {
                    "product_id": product_id,
                    "field_name": "rate",
                    "key": band,
                    "value": row["interest_rate"],
                    "source_id": source_id,
                }
            )
            if not any(rate["id"] == rate_id for rate in product["rates"]):
                # A duplicate band is not dropped silently: its value is an
                # observation, and disagreements become conflicts below.
                product["rates"].append(
                    _rate_from_row(row, rate_id, source_id, terms)
                )
            conditions = [
                ("deposit_limit", row.get("deposit_limit"), terms.get("rate_url")),
                (
                    "premature_withdrawal_allowed",
                    row.get("premature_withdrawal_allowed"),
                    terms.get("withdrawal_url"),
                ),
                (
                    "premature_withdrawal_penalty_percentage_points",
                    row.get("premature_withdrawal_penalty"),
                    terms.get("withdrawal_url"),
                ),
                (
                    "premature_withdrawal_policy",
                    terms.get("early_withdrawal_policy"),
                    terms.get("withdrawal_url"),
                ),
            ]
            if row.get("minimum_deposit") is not None:
                conditions.append(
                    ("minimum_deposit_inr", row["minimum_deposit"], terms.get("rate_url"))
                )
            if row.get("senior_citizen_rate") is not None:
                conditions.append(
                    (
                        "senior_citizen_rate_percent",
                        row["senior_citizen_rate"],
                        terms.get("rate_url"),
                    )
                )

            for condition_type, value, source_url in conditions:
                if value is not None:
                    observations.append(
                        {
                            "product_id": product_id,
                            "field_name": condition_type,
                            # Source-level terms apply to the whole product;
                            # row values may legitimately differ between bands.
                            "key": None
                            if condition_type == "premature_withdrawal_policy"
                            else band,
                            "value": value,
                            "source_id": source_id,
                        }
                    )
                if value is not None and not any(
                    c["condition_type"] == condition_type and c["condition_value"] == value
                    for c in product["conditions"]
                ):
                    product["conditions"].append(
                        {
                            "condition_type": condition_type,
                            "condition_value": value,
                            "verification_status": "SOURCE_METADATA",
                            "source_id": source_id,
                            "source_url": source_url,
                        }
                    )

        resolutions = [
            {
                **record,
                "product_id": self._product_id(record),
                "resolved_at": _as_datetime(record.get("resolved_at")),
            }
            for record in data.get("conflict_resolutions", [])
        ]
        for conflict in apply_resolutions(detect_conflicts(observations), resolutions):
            if conflict["field_name"] == "rate":
                conflict["rate_id"] = f"{conflict['product_id']}-{conflict['key']}"
            if conflict["status"] == RESOLVED:
                self._apply_resolved_value(conflict)
            self._conflicts.setdefault(conflict["product_id"], []).append(conflict)

        # Conflicts recorded by hand in the dataset (for example overlapping
        # tenure bands) apply to every rate of the field for that product.
        for record in data.get("source_conflicts", []):
            product_id = self._product_id(record)
            conflict = {
                "id": _slug(
                    f"{product_id}-{record['field_name']}-{record['tenure_min_months']}"
                ),
                "product_id": product_id,
                **record,
            }
            self._conflicts.setdefault(product_id, []).append(conflict)

    @staticmethod
    def _product_id(record: dict) -> str:
        bank = _BANK_ALIASES.get(record["bank_name"].strip().lower(), record["bank_name"].strip())
        return _slug(f"{bank}-{record['product_name']}")

    def _apply_resolved_value(self, conflict: dict) -> None:
        """Use the value a person confirmed when resolving a conflict."""
        product = self._products[conflict["product_id"]]
        if conflict["field_name"] == "rate":
            for rate in product["rates"]:
                if rate["id"] == conflict["rate_id"]:
                    rate["rate"] = conflict["resolved_value"]
            return
        resolved = normalize_value(conflict["resolved_value"])
        rejected = {
            normalize_value(conflict[side])
            for side in ("value_a", "value_b")
            if normalize_value(conflict[side]) != resolved
        }
        product["conditions"] = [
            c
            for c in product["conditions"]
            if c["condition_type"] != conflict["field_name"]
            or normalize_value(c["condition_value"]) not in rejected
        ]

    def list_products(self, category: str = "FD", status: str = "ACTIVE") -> list[dict]:
        return [
            product
            for product in self._products.values()
            if product["category"] == category.upper() and product["status"] == status
        ]

    def get_product(
        self,
        product_id: str,
        category: str | None = None,
        status: str | None = None,
    ) -> dict | None:
        product = self._products.get(product_id)
        if not product:
            return None
        if category and product["category"] != category.upper():
            return None
        if status and product["status"] != status:
            return None
        return product

    def get_source(self, source_id: str | None) -> dict | None:
        return self._sources.get(source_id) if source_id else None

    def get_conflicts(
        self,
        product_id: str,
        field_name: str | None = None,
        status: str = "OPEN",
    ) -> list[dict]:
        conflicts = self._conflicts.get(product_id, [])
        return [
            conflict
            for conflict in conflicts
            if conflict.get("status") == status
            and (not field_name or conflict.get("field_name") == field_name)
        ]

    def list_conflicts(self, status: str = "OPEN") -> list[dict]:
        return [
            conflict
            for conflicts in self._conflicts.values()
            for conflict in conflicts
            if conflict.get("status") == status
        ]
