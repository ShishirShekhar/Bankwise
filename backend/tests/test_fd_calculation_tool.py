import asyncio
import json
import os
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.calculators.fd import calculate_fd
from app.domain.comparison import compare_products
from app.main import app
from app.repositories.local_json import LocalJsonCatalog
from app.tools import calculate_fd_tool

EVAL_DIR = Path(__file__).parents[1] / "evals" / "fd_calculation"
EVAL_FILE = EVAL_DIR / "fd_calculation.test.json"
HDFC = "hdfc-bank-regular-fixed-deposit"


def test_adk_tool_schema_exposes_typed_required_inputs():
    from google.adk.tools import FunctionTool

    declaration = FunctionTool(calculate_fd_tool)._get_declaration()
    schema = declaration.parameters

    assert declaration.name == "calculate_fd_tool"
    assert "never do the" in declaration.description
    assert {name: prop.type.value for name, prop in schema.properties.items()} == {
        "product_id": "STRING",
        "principal": "NUMBER",
        "tenure_months": "INTEGER",
    }
    assert sorted(schema.required) == ["principal", "product_id", "tenure_months"]


def test_tool_returns_calculator_output_unchanged_with_version():
    outcome = calculate_fd_tool(HDFC, 500000, 24)
    rate = next(
        r
        for r in LocalJsonCatalog().get_product(HDFC)["rates"]
        if r["id"] == outcome["rate_id"]
    )

    assert outcome["status"] == "CALCULATED"
    assert outcome["result"] == calculate_fd(
        500000, rate["rate"], 24, rate["compounding_frequency"]
    )
    assert outcome["result"]["calculation_version"] == "fd-v1"
    assert outcome["source_id"] == rate["source_id"]


@pytest.mark.parametrize(
    ("args", "status", "reason"),
    [
        ((HDFC, 0, 24), "INVALID_INPUT", "Principal and tenure must be positive"),
        ((HDFC, 500000, -1), "INVALID_INPUT", "Principal and tenure must be positive"),
        (("no-such-product", 500000, 24), "MISSING", "FD product not found"),
        (
            (HDFC, 500000, 200),
            "UNAVAILABLE",
            "No unique rate matches the supplied amount and tenure",
        ),
        (
            ("state-bank-of-india-retail-domestic-term-deposit", 500000, 24),
            "BLOCKED",
            "Rate is not verified at HIGH confidence",
        ),
        (
            ("punjab-national-bank-domestic-fixed-deposit", 500000, 24),
            "BLOCKED",
            "Rate has an unresolved source conflict",
        ),
    ],
)
def test_tool_errors_return_a_reason_and_no_amount(args, status, reason):
    outcome = calculate_fd_tool(*args)

    assert outcome["status"] == status
    assert outcome["reason"] == reason
    assert "result" not in outcome


def test_tool_never_calculates_where_the_comparison_refuses():
    catalog = LocalJsonCatalog()
    for product in catalog.list_products():
        for tenure in range(1, 61):
            tool = calculate_fd_tool(product["id"], 500000, tenure).get("result")
            comparison = compare_products(catalog, [product["id"]], 500000, tenure)
            assert tool == comparison["products"][0]["calculation"], (
                product["id"],
                tenure,
            )


def test_calculation_endpoint_uses_the_same_outcomes():
    client = TestClient(app)
    body = {"product_id": HDFC, "principal": 500000, "tenure_months": 24}

    assert (
        client.post("/api/calculations/fd", json=body).json()
        == (calculate_fd_tool(HDFC, 500000, 24)["result"])
    )
    missing = client.post("/api/calculations/fd", json={**body, "product_id": "x"})
    assert missing.status_code == 404
    blocked = client.post(
        "/api/calculations/fd",
        json={**body, "product_id": "punjab-national-bank-domestic-fixed-deposit"},
    )
    assert blocked.status_code == 409
    assert (
        client.post(
            "/api/calculations/fd", json={**body, "tenure_months": 200}
        ).status_code
        == 422
    )


def test_calculation_agent_only_has_the_deterministic_tool():
    from app.ai.orchestrator import build_calculation_agent

    agent = build_calculation_agent()

    assert agent.tools == [calculate_fd_tool]
    assert "Never perform arithmetic yourself" in agent.instruction


def _eval_cases():
    return json.loads(EVAL_FILE.read_text(encoding="ascii"))["eval_cases"]


def test_eval_set_is_valid_adk_schema():
    from google.adk.evaluation.agent_evaluator import AgentEvaluator

    eval_set = AgentEvaluator._load_eval_set_from_file(str(EVAL_FILE), {}, {})

    assert len(eval_set.eval_cases) == len(_eval_cases()) >= 4
    assert AgentEvaluator.find_config_for_test_file(str(EVAL_FILE)) == {
        "tool_trajectory_avg_score": 1.0,
        "response_match_score": 0.5,
    }


@pytest.mark.parametrize("case", _eval_cases(), ids=lambda case: case["eval_id"])
def test_eval_references_match_the_deterministic_calculator(case):
    """Each expected answer must come from the tool, so the eval rewards tool use."""
    invocation = case["conversation"][0]
    (tool_use,) = invocation["intermediate_data"]["tool_uses"]
    expected = invocation["final_response"]["parts"][0]["text"]

    assert tool_use["name"] == "calculate_fd_tool"
    outcome = calculate_fd_tool(**tool_use["args"])
    amounts = set(re.findall(r"\d+\.\d{2}", expected))
    if outcome["status"] == "CALCULATED":
        result = outcome["result"]
        assert f"{result['maturity_amount']:.2f}" in amounts
        assert f"{result['interest_earned']:.2f}" in amounts
        assert result["calculation_version"] in expected
        assert f"{result['annual_rate_percent']}%" in expected
    else:
        assert not amounts
        assert outcome["reason"].lower().removeprefix("rate ") in expected.lower()


@pytest.mark.skipif(
    not (os.getenv("RUN_AGENT_EVALS") and os.getenv("GOOGLE_CLOUD_PROJECT")),
    reason="Set RUN_AGENT_EVALS=1 and GOOGLE_CLOUD_PROJECT to call Gemini",
)
def test_calculation_agent_eval_with_gemini():
    from google.adk.evaluation.agent_evaluator import AgentEvaluator

    asyncio.run(
        AgentEvaluator.evaluate("evals.fd_calculation", str(EVAL_DIR), num_runs=1)
    )
