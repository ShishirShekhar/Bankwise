from scripts.import_fd_products import _resolve_conflict_sources


def test_resolves_legacy_conflict_labels_to_rate_source():
    conflict = {
        "source_a": "Local catalogue row effective 2026-06-01",
        "source_b": "Official rate table effective 2025-06-18",
        "tenure_min_months": 24,
        "tenure_max_months": 24,
    }
    source = {"id": "pnb-rate-card", "url": "https://example.bank/rates"}
    product = {
        "sources": [source],
        "rates": [{
            "source_id": "pnb-rate-card",
            "tenure_min_months": 12,
            "tenure_max_months": 24,
        }],
    }

    assert _resolve_conflict_sources(conflict, product, {"pnb-rate-card": source}) == (
        "pnb-rate-card",
        "pnb-rate-card",
    )


def test_keeps_existing_source_ids_on_conflict():
    conflict = {"source_a": "source-a", "source_b": "source-b"}

    assert _resolve_conflict_sources(
        conflict,
        {"sources": [], "rates": []},
        {"source-a": {}, "source-b": {}},
    ) == ("source-a", "source-b")


def test_unmapped_conflict_does_not_guess_between_sources():
    conflict = {
        "source_a": "legacy-a",
        "source_b": "legacy-b",
        "tenure_min_months": 12,
        "tenure_max_months": 24,
    }
    source_a = {"id": "source-a"}
    source_b = {"id": "source-b"}
    product = {
        "sources": [source_a, source_b],
        "rates": [{
            "source_id": "source-a",
            "tenure_min_months": 12,
            "tenure_max_months": 24,
        }, {
            "source_id": "source-b",
            "tenure_min_months": 12,
            "tenure_max_months": 24,
        }],
    }

    assert _resolve_conflict_sources(
        conflict, product, {"source-a": source_a, "source-b": source_b}
    ) is None
