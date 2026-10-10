import asyncio

import pytest

from app.ai import decision_workflow
from app.schemas import Requirements


class FakeCatalog:
    def list_products(self, category):
        assert category == "FD"
        return [{"id": "fd-1"}]


class FakeSessions:
    def __init__(self):
        self.saved = []

    def save_decision(self, *args):
        self.saved.append(args)


def test_missing_requirements_return_clarification_without_running_adk(monkeypatch):
    monkeypatch.setattr(
        decision_workflow,
        "extract_requirements",
        lambda _query, use_gemini: Requirements(missing_information=["amount"])
        if not use_gemini
        else pytest.fail("request parsing must not call Gemini"),
    )
    sessions = FakeSessions()

    result = asyncio.run(
        decision_workflow.run_decision_workflow("an FD", FakeCatalog(), sessions, "user-1")
    )

    assert result["clarification_needed"] == ["amount"]
    assert result["ai"]["status"] == "not_used"
    assert len(sessions.saved) == 1
    assert sessions.saved[0][1] == "user-1"


def test_complete_request_persists_deterministic_comparison_without_model_explanation(monkeypatch):
    requirements = Requirements(amount=100000, duration_months=12)
    comparison = {
        "products": [
            {
                "product": {
                    "id": "fd-1",
                    "sources": [{"id": "src-1", "title": "Official rate card"}],
                },
                "calculation": {"maturity_amount": 106000},
                "tradeoff": {"is_highest_calculated_maturity": True},
            }
        ],
        "warnings": [],
    }
    monkeypatch.setattr(
        decision_workflow,
        "extract_requirements",
        lambda _query, use_gemini: requirements
        if not use_gemini
        else pytest.fail("request parsing must not call Gemini"),
    )
    monkeypatch.setattr(
        "app.domain.comparison.compare_products",
        lambda *_args: comparison,
    )

    sessions = FakeSessions()

    result = asyncio.run(
        decision_workflow.run_decision_workflow(
            "1 lakh for 1 year", FakeCatalog(), sessions, "test-user"
        )
    )

    assert result["explanation"] is None
    assert result["ai"]["status"] == "not_used"
    assert result["sources"] == [{"id": "src-1", "title": "Official rate card"}]
    assert len(sessions.saved) == 1
    assert sessions.saved[0][1] == "test-user"
