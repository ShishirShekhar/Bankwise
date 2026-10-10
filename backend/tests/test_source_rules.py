from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.config import SOURCE_MAX_AGE_DAYS
from app.domain.catalog import product_payload
from app.domain.comparison import compare_products
from app.domain.sources import (
    VerificationStatus,
    condition_verification,
    freshness,
    rate_is_usable,
    rate_verification,
    source_confidence,
    source_is_stale,
    source_issues,
)
from app.main import app
from app.repositories.local_json import LocalJsonCatalog


def test_official_current_source_is_high_confidence():
    source = {
        "source_type": "OFFICIAL_BANK_PAGE",
        "url": "https://bank.example/fd",
        "title": "Rates",
        "retrieved_at": datetime.now(timezone.utc),
        "verified_at": datetime.now(timezone.utc),
        "status": "ACTIVE",
    }
    assert freshness(source) == "HIGH"


def test_stale_source_is_not_high_confidence():
    source = {
        "source_type": "OFFICIAL_BANK_PDF",
        "url": "https://bank.example/rates.pdf",
        "title": "Rates",
        "retrieved_at": datetime.now(timezone.utc) - timedelta(days=365),
        "status": "ACTIVE",
    }
    assert freshness(source) == "LOW"


def test_source_confidence_reflects_authority_not_age():
    official = {"source_type": "OFFICIAL_BANK_PDF", "status": "ACTIVE"}
    secondary = {"source_type": "LOCAL_REFERENCE", "status": "ACTIVE"}

    assert source_confidence(official) == "HIGH"
    assert source_confidence(secondary) == "MEDIUM"
    assert freshness(official) == "LOW"  # no retrieval or verification date


class _Catalog:
    def __init__(self, sources, conflicts=()):
        self.sources = sources
        self.conflicts = list(conflicts)

    def get_source(self, source_id):
        return self.sources.get(source_id) if source_id else None

    def get_conflicts(self, product_id, field_name=None, status="OPEN"):
        return [
            c
            for c in self.conflicts
            if c["status"] == status
            and (not field_name or c["field_name"] == field_name)
        ]


def _source(**changes):
    return {
        "id": "bank-rates",
        "source_type": "OFFICIAL_BANK_PAGE",
        "url": "https://bank.example/fd",
        "title": "Rates",
        "verified_at": datetime.now(timezone.utc),
        "status": "ACTIVE",
        **changes,
    }


def _rate(**changes):
    return {
        "id": "r1",
        "rate": 7.0,
        "source_id": "bank-rates",
        "verification_status": "HIGH",
        **changes,
    }


CONDITION = {
    "condition_type": "penalty",
    "condition_value": "1%",
    "source_id": "bank-rates",
}
TODAY = datetime.now(timezone.utc).date()
OLD = datetime.now(timezone.utc) - timedelta(days=365)


def test_source_issues_flag_stale_inactive_and_out_of_period_sources():
    assert source_issues(_source()) == []
    assert not source_is_stale(_source())

    assert source_is_stale(_source(verified_at=OLD))
    assert source_issues(_source(verified_at=OLD)) == [
        f"Source was last checked more than {SOURCE_MAX_AGE_DAYS} days ago"
    ]
    assert source_is_stale(_source(verified_at=None))
    assert source_issues(_source(status="VERIFY_REQUIRED")) == ["Source is not active"]
    assert source_issues(_source(effective_from=TODAY + timedelta(days=1))) == [
        "Source is not effective yet"
    ]
    assert source_issues(_source(effective_to=TODAY - timedelta(days=1))) == [
        "Source has expired"
    ]
    for issue_source in (
        _source(verified_at=OLD),
        _source(effective_to=TODAY - timedelta(days=1)),
    ):
        assert freshness(issue_source) == VerificationStatus.LOW


@pytest.mark.parametrize(
    ("sources", "conflicts", "rate", "expected"),
    [
        ({"bank-rates": _source()}, [], _rate(), ("HIGH", None)),
        (
            {"bank-rates": _source(source_type="LOCAL_REFERENCE")},
            [],
            _rate(),
            ("MEDIUM", "Rate does not have a current official source"),
        ),
        (
            {"bank-rates": _source(verified_at=OLD)},
            [],
            _rate(),
            ("LOW", "Rate does not have a current official source"),
        ),
        (
            {"bank-rates": _source()},
            [],
            _rate(verification_status="LOW"),
            ("LOW", "Rate is not verified at HIGH confidence"),
        ),
        (
            {"bank-rates": _source()},
            [],
            _rate(effective_to=TODAY - timedelta(days=1)),
            ("LOW", "Rate has expired"),
        ),
        ({}, [], _rate(), ("MISSING", "Linked source was not found")),
        ({}, [], _rate(source_id=None), ("MISSING", "Rate has no linked source")),
        (
            {"bank-rates": _source()},
            [{"field_name": "rate", "status": "OPEN"}],
            _rate(),
            ("CONFLICT", "Rate has an unresolved source conflict"),
        ),
        (
            {"bank-rates": _source()},
            [{"field_name": "rate", "status": "RESOLVED"}],
            _rate(),
            ("HIGH", None),
        ),
    ],
)
def test_rate_verification_assigns_each_status(sources, conflicts, rate, expected):
    catalog = _Catalog(sources, conflicts)

    assert rate_verification(catalog, "p1", rate) == expected
    assert rate_is_usable(catalog, "p1", rate) == (expected[0] == "HIGH", expected[1])


def test_condition_verification_uses_source_and_matching_conflicts():
    assert condition_verification(
        _Catalog({"bank-rates": _source()}), "p1", CONDITION
    ) == ("HIGH", None)
    assert (
        condition_verification(
            _Catalog({"bank-rates": _source(verified_at=OLD)}), "p1", CONDITION
        )[0]
        == "LOW"
    )
    assert condition_verification(_Catalog({}), "p1", CONDITION)[0] == "MISSING"
    assert condition_verification(
        _Catalog({}), "p1", {**CONDITION, "source_id": None}
    ) == (
        "MISSING",
        "Condition has no linked source",
    )
    penalty_conflict = [{"field_name": "penalty", "status": "OPEN"}]
    rate_conflict = [{"field_name": "rate", "status": "OPEN"}]
    assert (
        condition_verification(
            _Catalog({"bank-rates": _source()}, penalty_conflict), "p1", CONDITION
        )[0]
        == "CONFLICT"
    )
    assert (
        condition_verification(
            _Catalog({"bank-rates": _source()}, rate_conflict), "p1", CONDITION
        )[0]
        == "HIGH"
    )


def test_low_confidence_rates_never_reach_calculations():
    catalog = LocalJsonCatalog()
    result = compare_products(
        catalog,
        [product["id"] for product in catalog.list_products()],
        amount=500000,
        tenure=24,
    )

    for item in result["products"]:
        statuses = {rate["verification_status"] for rate in item["product"]["rates"]}
        assert statuses <= set(VerificationStatus)
        if item["calculation"] is not None:
            assert "HIGH" in statuses
        else:
            assert item["calculation_blocked_reason"]
    pnb = next(
        i for i in result["products"] if i["product"]["bank"] == "Punjab National Bank"
    )
    assert {r["verification_status"] for r in pnb["product"]["rates"]} == {"CONFLICT"}
    assert pnb["calculation"] is None


def test_verification_run_reports_status_for_rates_conditions_and_sources():
    client = TestClient(app)
    csrf = client.get("/api/auth/csrf").json()["csrfToken"]
    records = client.post(
        "/api/verification/run",
        headers={"Origin": "http://localhost:3000", "X-CSRF-Token": csrf},
    ).json()["records"]

    fields = {record["field"] for record in records}
    assert {"rate", "source", "premature_withdrawal_policy"} <= fields
    assert {record["status"] for record in records} <= set(VerificationStatus)
    sbi_source = next(
        r
        for r in records
        if r["field"] == "source" and r["product_id"].startswith("state-bank")
    )
    assert sbi_source["status"] == "LOW"
    assert sbi_source["notes"] == "Source is not active"


def test_every_local_financial_fact_traces_to_a_source_with_full_metadata():
    catalog = LocalJsonCatalog()

    for product in catalog.list_products(category="FD", status="ACTIVE"):
        payload = product_payload(product, catalog)
        sources = {source["id"]: source for source in payload["sources"]}
        for source in payload["sources"]:
            for field in ("url", "type", "title", "retrieved_at", "verified_at"):
                assert source[field], (product["id"], field)
            assert "effective_from" in source
            assert source["confidence"] in {"HIGH", "MEDIUM"}
            assert source["verification_status"] in {"HIGH", "MEDIUM", "LOW"}
        for rate in payload["rates"]:
            assert rate["source_id"] in sources
        for condition in payload["conditions"]:
            source = sources[condition["source_id"]]
            assert condition["source_url"]
            assert condition["verified"] is (source["verification_status"] == "HIGH")


def test_sources_endpoint_returns_provenance_and_verification_state():
    client = TestClient(app)

    response = client.get("/api/products/hdfc-bank-regular-fixed-deposit/sources")

    assert response.status_code == 200
    source = response.json()["sources"][0]
    assert source["url"].startswith("https://www.hdfcbank.com/")
    assert source["retrieved_at"] and source["verified_at"]
    assert source["confidence"] == "HIGH"
    assert source["verification_status"] == "HIGH"
