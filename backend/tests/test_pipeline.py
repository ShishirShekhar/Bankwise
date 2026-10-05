from app.ai import pipeline
from app.ai.extraction import Requirements


def fake(monkeypatch, **fields):
    monkeypatch.setattr(pipeline, "extract", lambda _text: Requirements(**fields))


def test_missing_info_asks_instead_of_calculating(monkeypatch):
    fake(monkeypatch, category="FD", missing=["amount", "duration_months"])
    r = pipeline.run("I want an FD")
    assert r.status == "NEEDS_CLARIFICATION" and r.options == []


def test_unsupported_category(monkeypatch):
    fake(monkeypatch, category="LOAN")
    assert pipeline.run("loan please").status == "UNSUPPORTED"


def test_two_year_options_sorted_by_maturity(monkeypatch):
    fake(monkeypatch, category="FD", amount=500000, duration_months=24)
    r = pipeline.run("5 lakh for 2 years")
    assert r.status == "OK"
    assert [o.bank for o in r.options] == ["alpha", "bravo", "charlie"][
        : len(r.options)
    ]
    assert r.options == sorted(r.options, key=lambda o: o.maturity_amount, reverse=True)


def test_missing_tenure_rate_is_skipped_not_invented(monkeypatch):
    fake(monkeypatch, category="FD", amount=100000, duration_months=12)
    r = pipeline.run("1 lakh for 1 year")
    assert {o.bank for o in r.options} == {"alpha", "bravo"}
    assert [(s.bank, s.reason) for s in r.skipped] == [
        ("charlie", "no_rate_for_tenure")
    ]


def test_no_rate_anywhere_for_tenure(monkeypatch):
    fake(monkeypatch, category="FD", amount=100000, duration_months=7)
    assert pipeline.run("1 lakh for 7 months").status == "NO_MATCH"


def test_best_early_exit_can_differ_from_best_maturity(monkeypatch):
    fake(monkeypatch, category="FD", amount=500000, duration_months=24)
    r = pipeline.run("5 lakh for 2 years, may need it early")
    assert r.options[0].bank == "alpha"            # highest maturity
    assert r.best_if_withdrawn_early == "bravo"    # lowest penalty