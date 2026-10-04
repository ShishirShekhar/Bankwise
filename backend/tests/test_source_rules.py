from datetime import datetime, timedelta

from app.services import freshness


def test_official_current_source_is_high_confidence():
    source = {"source_type": "OFFICIAL_BANK_PAGE", "url": "https://bank.example/fd", "title": "Rates",
              "retrieved_at": datetime.utcnow(), "verified_at": datetime.utcnow(), "status": "ACTIVE"}
    assert freshness(source) == "HIGH"


def test_stale_source_is_not_high_confidence():
    source = {"source_type": "OFFICIAL_BANK_PDF", "url": "https://bank.example/rates.pdf", "title": "Rates",
              "retrieved_at": datetime.utcnow() - timedelta(days=365), "status": "ACTIVE"}
    assert freshness(source) == "LOW"
