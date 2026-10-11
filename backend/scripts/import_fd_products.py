"""Upsert the local FD catalogue into the configured BigQuery tables.

Preview with ``python -m scripts.import_fd_products``. Pass ``--apply`` to write.
Rows are upserted by stable IDs, so rerunning the import does not duplicate data.
"""

import argparse
import json
from datetime import UTC, datetime
from typing import Any

from app.config import BIGQUERY_DATASET, BIGQUERY_LOCATION, BIGQUERY_PROJECT
from app.repositories.local_json import LocalJsonCatalog


def _params(row: dict[str, Any], types: dict[str, str]):
    from google.cloud import bigquery

    return [
        bigquery.ScalarQueryParameter(name, types[name], value)
        for name, value in row.items()
    ]


def _upsert(client, table: str, row: dict[str, Any], types: dict[str, str]) -> None:
    from google.cloud import bigquery

    columns = list(row)
    names = ", ".join(columns)
    values = ", ".join(f"@{column} AS {column}" for column in columns)
    updates = ", ".join(f"T.{column}=S.{column}" for column in columns if column != "id")
    sql = f"""
      MERGE `{BIGQUERY_PROJECT}.{BIGQUERY_DATASET}.{table}` T
      USING (SELECT {values}) S ON T.id = S.id
      WHEN MATCHED THEN UPDATE SET {updates}
      WHEN NOT MATCHED THEN INSERT ({names}) VALUES ({', '.join(f'S.{c}' for c in columns)})
    """
    client.query(
        sql,
        job_config=bigquery.QueryJobConfig(query_parameters=_params(row, types)),
        location=BIGQUERY_LOCATION,
    ).result()


def _resolve_conflict_sources(
    conflict: dict[str, Any], product: dict[str, Any], source_by_id: dict[str, dict]
) -> tuple[str, str] | None:
    source_a = conflict.get("source_a")
    source_b = conflict.get("source_b")
    if source_a in source_by_id and source_b in source_by_id:
        return source_a, source_b

    conflict_min = conflict.get("tenure_min_months")
    conflict_max = conflict.get("tenure_max_months")
    matching_rate_sources = {
        rate.get("source_id")
        for rate in product["rates"]
        if conflict_min is not None
        and conflict_max is not None
        and rate.get("tenure_min_months") is not None
        and rate.get("tenure_max_months") is not None
        and rate["tenure_min_months"] <= conflict_max
        and rate["tenure_max_months"] >= conflict_min
    }
    matching_sources = [
        item for item in product["sources"] if item["id"] in matching_rate_sources
    ]
    if len(matching_sources) == 1 and matching_sources[0]["id"] in source_by_id:
        source_id = matching_sources[0]["id"]
        return source_id, source_id
    return None


def import_catalog(apply: bool) -> dict[str, int]:
    catalog = LocalJsonCatalog()
    counts: dict[str, int] = {}
    writes: list[tuple[str, dict[str, Any], dict[str, str]]] = []
    source_by_id: dict[str, dict] = {}
    unmapped_conflicts: list[dict[str, str]] = []

    for bank in catalog.list_banks():
        writes.append(("banks", bank.model_dump(mode="json"), {
            "id": "STRING", "name": "STRING", "website": "STRING",
            "country": "STRING", "status": "STRING",
        }))

    products = catalog.list_products()
    for product in products:
        bank = catalog.get_bank(product["bank_id"])
        if bank is None:
            raise ValueError(f"Product {product['id']} refers to an unknown bank")
        writes.append(("products", {
            "id": product["id"], "bank_id": bank.id,
            "category": product["category"], "name": product["name"],
            "description": product.get("description"), "status": product["status"],
        }, {
            "id": "STRING", "bank_id": "STRING", "category": "STRING",
            "name": "STRING", "description": "STRING", "status": "STRING",
        }))

        for source in product["sources"]:
            source_by_id[source["id"]] = source
            if not source.get("url") or not source.get("retrieved_at"):
                raise ValueError(f"Source {source['id']} lacks URL or retrieval date; refusing import")
            writes.append(("sources", {
                "id": source["id"], "product_id": product["id"],
                "source_type": source["source_type"], "url": source["url"],
                "title": source["title"] or source["id"], "document_uri": None,
                "retrieved_at": source["retrieved_at"], "verified_at": source.get("verified_at"),
                "effective_from": source.get("effective_from"), "effective_to": None,
                "content_hash": None, "status": source["status"],
            }, {
                "id": "STRING", "product_id": "STRING", "source_type": "STRING",
                "url": "STRING", "title": "STRING", "document_uri": "STRING",
                "retrieved_at": "TIMESTAMP", "verified_at": "TIMESTAMP",
                "effective_from": "DATE", "effective_to": "DATE",
                "content_hash": "STRING", "status": "STRING",
            }))

        for rate in product["rates"]:
            writes.append(("product_rates", {
                "id": rate["id"], "product_id": product["id"], "rate": rate["rate"],
                "rate_type": "ANNUAL", "min_amount": rate.get("min_amount"),
                "max_amount": rate.get("max_amount"), "tenure_months": rate.get("tenure_months"),
                "tenure_min_months": rate.get("tenure_min_months"),
                "tenure_max_months": rate.get("tenure_max_months"),
                "compounding_frequency": rate.get("compounding_frequency"),
                "payout_type": rate.get("payout_type") or "CUMULATIVE",
                "effective_from": rate.get("effective_from"), "effective_to": rate.get("effective_to"),
                "source_id": rate.get("source_id"), "verification_status": rate["verification_status"],
            }, {
                "id": "STRING", "product_id": "STRING", "rate": "FLOAT64",
                "rate_type": "STRING", "min_amount": "FLOAT64", "max_amount": "FLOAT64",
                "tenure_months": "INT64", "tenure_min_months": "INT64",
                "tenure_max_months": "INT64", "compounding_frequency": "INT64",
                "payout_type": "STRING", "effective_from": "DATE", "effective_to": "DATE",
                "source_id": "STRING", "verification_status": "STRING",
            }))
            source = source_by_id.get(rate.get("source_id"), {})
            writes.append(("verification_records", {
                "id": f"{rate['id']}-rate-verification", "product_id": product["id"],
                "field_name": "rate", "observed_value": str(rate["rate"]),
                "normalized_value": str(rate["rate"]), "source_id": rate.get("source_id"),
                "confidence": "HIGH" if source.get("status") == "ACTIVE" and rate["verification_status"] == "HIGH" else "LOW",
                "status": rate["verification_status"],
                "checked_at": source.get("verified_at") or datetime.now(UTC),
                "notes": "Imported from local FD catalogue; verify against the official source before production use.",
            }, {
                "id": "STRING", "product_id": "STRING", "field_name": "STRING",
                "observed_value": "STRING", "normalized_value": "STRING", "source_id": "STRING",
                "confidence": "STRING", "status": "STRING", "checked_at": "TIMESTAMP", "notes": "STRING",
            }))

        for index, condition in enumerate(product["conditions"]):
            source = source_by_id.get(condition.get("source_id"), {})
            condition_status = "HIGH" if source.get("status") == "ACTIVE" else "LOW"
            condition_id = f"{product['id']}-{condition['condition_type']}-{index}"
            writes.append(("product_conditions", {
                "id": condition_id, "product_id": product["id"],
                "condition_type": condition["condition_type"],
                "condition_value": str(condition["condition_value"]),
                "source_id": condition.get("source_id"), "verification_status": condition_status,
            }, {
                "id": "STRING", "product_id": "STRING", "condition_type": "STRING",
                "condition_value": "STRING", "source_id": "STRING", "verification_status": "STRING",
            }))
            writes.append(("verification_records", {
                "id": f"{condition_id}-verification", "product_id": product["id"],
                "field_name": condition["condition_type"],
                "observed_value": str(condition["condition_value"]),
                "normalized_value": str(condition["condition_value"]).strip().casefold(),
                "source_id": condition.get("source_id"), "confidence": condition_status,
                "status": condition_status,
                "checked_at": source.get("verified_at") or datetime.now(UTC),
                "notes": "Imported from local FD catalogue; verify against the official source before production use.",
            }, {
                "id": "STRING", "product_id": "STRING", "field_name": "STRING",
                "observed_value": "STRING", "normalized_value": "STRING", "source_id": "STRING",
                "confidence": "STRING", "status": "STRING", "checked_at": "TIMESTAMP", "notes": "STRING",
            }))

        for conflict in catalog.get_conflicts(product["id"], status="OPEN"):
            source_ids = _resolve_conflict_sources(conflict, product, source_by_id)
            # Hand-authored conflict records can refer to source labels that do
            # not have a corresponding source row. Never fabricate those IDs.
            if source_ids is None:
                unmapped_conflicts.append({
                    "id": conflict["id"],
                    "product_id": product["id"],
                    "reason": "conflict source labels do not map to source IDs",
                })
                continue
            source_a, source_b = source_ids
            writes.append(("source_conflicts", {
                "id": conflict["id"], "product_id": product["id"],
                "field_name": conflict["field_name"], "source_a": source_a,
                "value_a": str(conflict["value_a"]), "source_b": source_b,
                "value_b": str(conflict["value_b"]), "status": conflict["status"],
                "resolved_value": None, "resolved_at": None, "resolution_notes": conflict.get("note"),
            }, {
                "id": "STRING", "product_id": "STRING", "field_name": "STRING",
                "source_a": "STRING", "value_a": "STRING", "source_b": "STRING",
                "value_b": "STRING", "status": "STRING", "resolved_value": "STRING",
                "resolved_at": "TIMESTAMP", "resolution_notes": "STRING",
            }))

    for table, _, _ in writes:
        counts[table] = counts.get(table, 0) + 1
    print(json.dumps({"project": BIGQUERY_PROJECT, "dataset": BIGQUERY_DATASET,
                      "mode": "apply" if apply else "dry-run", "rows": counts,
                      "unmapped_conflicts": unmapped_conflicts}, indent=2))
    if not apply:
        return counts

    if not BIGQUERY_PROJECT:
        raise SystemExit("Set BIGQUERY_PROJECT or GOOGLE_CLOUD_PROJECT in backend/.env")
    if unmapped_conflicts:
        raise SystemExit("Resolve the listed conflict source references before importing; no rows were written")

    from google.cloud import bigquery

    client = bigquery.Client(project=BIGQUERY_PROJECT, location=BIGQUERY_LOCATION)
    for table, row, types in writes:
        _upsert(client, table, row, types)
    print("BigQuery upsert complete")
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write rows to BigQuery (default is preview)")
    args = parser.parse_args()
    import_catalog(args.apply)


if __name__ == "__main__":
    main()
