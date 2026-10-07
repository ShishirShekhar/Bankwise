from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.domain.catalog import product_payload
from app.domain.sources import condition_is_verified, freshness, source_confidence
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
    def __init__(self, sources):
        self.sources = sources

    def get_source(self, source_id):
        return self.sources.get(source_id) if source_id else None


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


def test_condition_is_verified_only_with_current_official_source():
    condition = {
        "condition_type": "penalty",
        "condition_value": "1%",
        "source_id": "bank-rates",
    }

    assert condition_is_verified(_Catalog({"bank-rates": _source()}), condition) == (
        True,
        None,
    )
    stale = _source(verified_at=datetime.now(timezone.utc) - timedelta(days=365))
    assert not condition_is_verified(_Catalog({"bank-rates": stale}), condition)[0]
    secondary = _source(source_type="LOCAL_REFERENCE")
    assert not condition_is_verified(_Catalog({"bank-rates": secondary}), condition)[0]
    assert not condition_is_verified(_Catalog({}), condition)[0]
    assert condition_is_verified(_Catalog({}), {**condition, "source_id": None}) == (
        False,
        "Condition has no linked source",
    )


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
