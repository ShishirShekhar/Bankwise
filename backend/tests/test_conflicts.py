import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.domain.catalog import product_payload
from app.domain.comparison import compare_products
from app.domain.conflicts import (
    ConflictResolutionError,
    apply_resolutions,
    detect_conflicts,
    resolve_conflict,
)
from app.domain.sources import condition_verification, rate_verification
from app.main import app
from app.repositories.local_json import LocalJsonCatalog

DATA_FILE = Path(__file__).parents[1] / "data" / "fd-products.json"
HDFC = "hdfc-bank-regular-fixed-deposit"


def _obs(value, source_id, key="24-35", field_name="rate", product_id="p1"):
    return {
        "product_id": product_id,
        "field_name": field_name,
        "key": key,
        "value": value,
        "source_id": source_id,
    }


def test_disagreeing_sources_produce_an_open_conflict_keeping_both_values():
    conflicts = detect_conflicts([_obs(7.25, "bank-website"), _obs(7.00, "bank-pdf")])

    assert len(conflicts) == 1
    conflict = conflicts[0]
    assert conflict["status"] == "OPEN"
    assert (conflict["source_a"], conflict["value_a"]) == ("bank-website", 7.25)
    assert (conflict["source_b"], conflict["value_b"]) == ("bank-pdf", 7.00)
    assert conflict["field_name"] == "rate" and conflict["key"] == "24-35"
    assert conflict["detected_at"] is not None


@pytest.mark.parametrize(
    "observations",
    [
        [_obs(6.3, "a"), _obs(6.30, "b")],
        [_obs("Below ₹3 crore", "a"), _obs("  below ₹3   CRORE ", "b")],
        [_obs(7.25, "a", key="12-23"), _obs(7.00, "b", key="24-35")],
        [_obs(7.25, "a", product_id="p1"), _obs(7.00, "b", product_id="p2")],
        [_obs(True, "a"), _obs(True, "b")],
    ],
)
def test_matching_or_unrelated_observations_are_not_conflicts(observations):
    assert detect_conflicts(observations) == []


def test_each_distinct_disagreeing_value_is_recorded():
    conflicts = detect_conflicts(
        [_obs(7.25, "a"), _obs(7.00, "b"), _obs(7.00, "c"), _obs(6.9, "d")]
    )

    assert [(c["value_a"], c["value_b"]) for c in conflicts] == [
        (7.25, 7.0),
        (7.25, 6.9),
    ]


def test_resolution_must_use_an_observed_value_and_explain_why():
    conflict = detect_conflicts([_obs(7.25, "a"), _obs(7.00, "b")])[0]

    resolved = resolve_conflict(conflict, 7.0, "Rate card PDF is newer")
    assert resolved["status"] == "RESOLVED"
    assert resolved["resolved_value"] == 7.0
    assert resolved["resolved_at"] is not None
    assert (resolved["value_a"], resolved["value_b"]) == (7.25, 7.0)
    assert conflict["status"] == "OPEN"
    with pytest.raises(ConflictResolutionError):
        resolve_conflict(conflict, 7.1, "Averaged the two")
    with pytest.raises(ConflictResolutionError):
        resolve_conflict(conflict, 7.0, "  ")


def test_apply_resolutions_matches_by_product_field_and_key():
    conflicts = detect_conflicts(
        [
            _obs(7.25, "a"),
            _obs(7.0, "b"),
            _obs(6.5, "a", key="12-23"),
            _obs(6.4, "b", key="12-23"),
        ]
    )
    resolutions = [
        {
            "product_id": "p1",
            "field_name": "rate",
            "key": "24-35",
            "resolved_value": 7.0,
            "resolution_notes": "PDF",
        },
        {
            "product_id": "p1",
            "field_name": "rate",
            "key": "12-23",
            "resolved_value": 9.9,
            "resolution_notes": "bad",
        },
    ]

    result = {c["key"]: c["status"] for c in apply_resolutions(conflicts, resolutions)}

    assert result == {"24-35": "RESOLVED", "12-23": "OPEN"}


def _catalog_with(tmp_path, extra_rows=(), resolutions=()):
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    hdfc_row = next(
        r
        for r in data["products"]
        if r["bank_name"] == "HDFC Bank" and r["tenure_min_months"] == 24
    )
    for changes in extra_rows:
        data["products"].append(
            {
                **hdfc_row,
                "source_name": "HDFC Bank FD Rate Card PDF",
                "source_reference": "HDFC Bank official FD rate card PDF",
                **changes,
            }
        )
    data["conflict_resolutions"] = list(resolutions)
    data_file = tmp_path / "fd-products.json"
    data_file.write_text(json.dumps(data), encoding="utf-8")
    return LocalJsonCatalog(data_file)


def test_catalog_detects_rate_disagreement_and_blocks_only_that_band(tmp_path):
    catalog = _catalog_with(tmp_path, [{"interest_rate": 7.0}])
    product = catalog.get_product(HDFC)
    rates = {rate["id"]: rate for rate in product["rates"]}

    conflicts = catalog.get_conflicts(HDFC, field_name="rate")
    assert len(conflicts) == 1
    assert conflicts[0]["rate_id"] == f"{HDFC}-24-35"
    assert {conflicts[0]["value_a"], conflicts[0]["value_b"]} == {6.45, 7.0}
    assert rate_verification(catalog, HDFC, rates[f"{HDFC}-24-35"])[0] == "CONFLICT"
    assert rate_verification(catalog, HDFC, rates[f"{HDFC}-12-14"]) == ("HIGH", None)

    result = compare_products(catalog, [HDFC], amount=500000, tenure=24)["products"][0]
    assert result["calculation"] is None
    assert (
        result["calculation_blocked_reason"] == "Rate has an unresolved source conflict"
    )
    payload = product_payload(product, catalog)
    assert payload["conflicts"][0]["status"] == "OPEN"
    assert payload["conflicts"][0]["source_b"] == "hdfc-bank-fd-rate-card-pdf"


def test_catalog_detects_condition_disagreement(tmp_path):
    catalog = _catalog_with(tmp_path, [{"premature_withdrawal_penalty": 0.5}])
    penalty = next(
        c
        for c in catalog.get_product(HDFC)["conditions"]
        if c["condition_type"] == "premature_withdrawal_penalty_percentage_points"
    )

    assert condition_verification(catalog, HDFC, penalty)[0] == "CONFLICT"
    assert not catalog.get_conflicts(HDFC, field_name="rate")


def test_recorded_resolution_unblocks_the_band_with_the_confirmed_value(tmp_path):
    resolution = {
        "bank_name": "HDFC Bank",
        "product_name": "Regular Fixed Deposit",
        "field_name": "rate",
        "key": "24-35",
        "resolved_value": 7.0,
        "resolution_notes": "Rate card PDF supersedes the web page",
        "resolved_at": "2026-10-05",
    }
    catalog = _catalog_with(tmp_path, [{"interest_rate": 7.0}], [resolution])
    rate = next(
        r for r in catalog.get_product(HDFC)["rates"] if r["id"] == f"{HDFC}-24-35"
    )

    assert not catalog.get_conflicts(HDFC)
    assert rate["rate"] == 7.0
    assert rate_verification(catalog, HDFC, rate) == ("HIGH", None)
    resolved = catalog.list_conflicts("RESOLVED")
    assert len(resolved) == 1 and resolved[0]["resolved_value"] == 7.0
    result = compare_products(catalog, [HDFC], amount=500000, tenure=24)["products"][0]
    assert result["calculation"]["annual_rate_percent"] == 7.0


def test_conflicts_endpoint_lists_open_and_resolved_conflicts():
    client = TestClient(app)

    open_conflicts = client.get("/api/conflicts").json()
    assert open_conflicts["status"] == "OPEN"
    pnb = next(
        c for c in open_conflicts["conflicts"] if c["product_id"].startswith("punjab")
    )
    assert pnb["value_a"] is not None and pnb["source_b"]
    assert client.get("/api/conflicts?status=resolved").json()["conflicts"] == []
    assert client.get("/api/conflicts?status=IGNORED").status_code == 422
