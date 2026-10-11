"""Offline acceptance suite for Bankwise's trust-critical agent behavior."""

import json
from pathlib import Path

import pytest

from app.domain.comparison import compare_products
from app.domain.input import redact_sensitive_input
from app.repositories.local_json import LocalJsonCatalog
from app.tools import calculate_fd_tool

EVAL_FILE = Path(__file__).parents[1] / "evals" / "bankwise_agent" / "bankwise_agent.eval.json"
EVAL_CASES = json.loads(EVAL_FILE.read_text(encoding="utf-8"))["cases"]


@pytest.mark.parametrize("case", EVAL_CASES, ids=lambda case: case["id"])
def test_bankwise_agent_acceptance_cases(case):
    if case["operation"] == "calculation":
        outcome = calculate_fd_tool(
            case["product_id"], case["principal"], case["tenure_months"]
        )
        assert outcome["status"] == case["expected_status"]
        if outcome["status"] == "CALCULATED":
            assert outcome["result"]["calculation_version"] == case[
                "expected_calculation_version"
            ]
        else:
            assert "result" not in outcome
            assert case["expected_reason_contains"] in outcome["reason"]
    elif case["operation"] == "comparison":
        result = compare_products(
            LocalJsonCatalog(),
            case["product_ids"],
            case["principal"],
            case["tenure_months"],
        )
        assert len(result["products"]) == len(case["product_ids"])
        assert all(item.get("tradeoff") for item in result["products"])
        assert result["tradeoff_summary"]
    elif case["operation"] == "redaction":
        redacted = redact_sensitive_input(case["query"])
        assert case["must_not_contain"] not in redacted
        assert "[REDACTED]" in redacted
    else:
        pytest.fail(f"Unknown evaluation operation: {case['operation']}")
