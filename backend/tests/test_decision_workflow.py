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
        lambda _query: Requirements(missing_information=["amount"]),
    )
    monkeypatch.setattr(
        decision_workflow,
        "run_decision_agent",
        lambda *_args: pytest.fail("ADK should not run before required inputs exist"),
    )
    sessions = FakeSessions()

    result = asyncio.run(
        decision_workflow.run_decision_workflow("an FD", FakeCatalog(), sessions, "user-1")
    )

    assert result["clarification_needed"] == ["amount"]
    assert result["ai"]["status"] == "clarification_required"
    assert len(sessions.saved) == 1
    assert sessions.saved[0][1] == "user-1"


def test_complete_request_uses_adk_on_deterministic_comparison(monkeypatch):
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
    agent_calls = []
    monkeypatch.setattr(
        decision_workflow, "extract_requirements", lambda _query: requirements
    )
    monkeypatch.setattr(
        "app.domain.comparison.compare_products",
        lambda *_args: comparison,
    )

    async def fake_agent(query, parsed_requirements, context):
        agent_calls.append((query, parsed_requirements, context))
        return "Grounded explanation"

    monkeypatch.setattr(decision_workflow, "run_decision_agent", fake_agent)
    sessions = FakeSessions()

    result = asyncio.run(
        decision_workflow.run_decision_workflow(
            "1 lakh for 1 year", FakeCatalog(), sessions, "test-user"
        )
    )

    assert result["explanation"] == "Grounded explanation"
    assert result["ai"]["agent"] == "bankwise_decision_agent"
    assert result["sources"] == [{"id": "src-1", "title": "Official rate card"}]
    assert agent_calls[0][2] is comparison
    assert len(sessions.saved) == 1
    assert sessions.saved[0][1] == "test-user"
