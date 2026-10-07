"""Static checks for sql/bigquery_schema.sql (relationships and provenance)."""

import re
from pathlib import Path

SCHEMA_FILE = Path(__file__).parents[1] / "sql" / "bigquery_schema.sql"
TABLE_PATTERN = re.compile(
    r"CREATE TABLE IF NOT EXISTS `[^`]+\.(\w+)` \((.*?)\n\);", re.DOTALL
)
FOREIGN_KEY_PATTERN = re.compile(
    r"FOREIGN KEY \((\w+)\) REFERENCES `[^`]+\.(\w+)`\((\w+)\) NOT ENFORCED"
)


def _tables() -> dict[str, dict]:
    tables = {}
    for name, body in TABLE_PATTERN.findall(SCHEMA_FILE.read_text(encoding="utf-8")):
        lines = [line.strip().rstrip(",") for line in body.strip().splitlines()]
        columns = {
            line.split()[0]: "NOT NULL" in line
            for line in lines
            if line and not line.startswith(("PRIMARY KEY", "FOREIGN KEY", "--"))
        }
        tables[name] = {
            "columns": columns,
            "primary_key": "PRIMARY KEY (id) NOT ENFORCED" in body,
            "foreign_keys": FOREIGN_KEY_PATTERN.findall(body),
        }
    return tables


def test_schema_defines_all_financial_entities_with_primary_keys():
    tables = _tables()

    assert list(tables) == [
        "banks",
        "products",
        "sources",
        "product_rates",
        "product_conditions",
        "verification_records",
        "source_conflicts",
    ]
    for name, table in tables.items():
        assert table["primary_key"], name
        assert table["columns"]["id"], name


def test_foreign_keys_reference_existing_columns_in_tables_created_earlier():
    tables = _tables()
    order = list(tables)

    for name, table in tables.items():
        for column, target_table, target_column in table["foreign_keys"]:
            assert column in table["columns"], (name, column)
            assert target_column in tables[target_table]["columns"]
            assert order.index(target_table) < order.index(name), (name, target_table)

    assert ("bank_id", "banks", "id") in tables["products"]["foreign_keys"]
    for child in ("product_rates", "product_conditions", "verification_records"):
        assert ("source_id", "sources", "id") in tables[child]["foreign_keys"]


def test_financial_fields_support_provenance_and_verification():
    tables = _tables()
    sources = tables["sources"]["columns"]

    for column in ("url", "source_type", "title", "retrieved_at", "status"):
        assert sources[column], column
    for column in ("verified_at", "effective_from", "effective_to", "reference"):
        assert column in sources
    for table in ("product_rates", "product_conditions"):
        assert "source_id" in tables[table]["columns"]
        assert tables[table]["columns"]["verification_status"]
    assert tables["verification_records"]["columns"]["confidence"]


def test_conflicting_source_values_and_resolution_can_be_stored():
    conflicts = _tables()["source_conflicts"]["columns"]

    for column in ("source_a", "value_a", "source_b", "value_b", "status"):
        assert conflicts[column], column
    for column in ("note", "detected_at", "resolved_value", "resolved_at"):
        assert column in conflicts
