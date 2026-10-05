from app.ai.extraction import Requirements, validate


def test_missing_is_recomputed_not_trusted():
    req = validate(Requirements(amount=500000, duration_months=None, missing=[]))
    assert req.missing == ["duration_months"]


def test_invalid_values_are_dropped():
    req = validate(Requirements(amount=-5, duration_months=0))
    assert req.amount is None and req.duration_months is None
    assert req.missing == ["amount", "duration_months"]


def test_complete_request():
    assert validate(Requirements(amount=500000, duration_months=24)).missing == []


def test_non_fd_category_does_not_demand_amount_and_duration():
    assert validate(Requirements(category="LOAN")).missing == []
    