from app.ai.ask_response import to_ask_response


def test_ask_response_matches_comparison_card_fields_and_does_not_guess_exit_date():
    product = {
        "id": "hdfc-fd",
        "bank": "HDFC Bank",
        "name": "Regular Fixed Deposit",
        "rates": [
            {
                "annual_rate_percent": 6.45,
                "ineligibility_reason": None,
                "usable_for_calculation": True,
                "verification_status": "HIGH",
                "source_id": "src",
                "calculation_source_url": "https://bank.example/calc",
            }
        ],
        "conditions": [
            {"type": "premature_withdrawal_allowed", "value": True},
            {
                "type": "premature_withdrawal_policy",
                "value": "One percentage point is deducted.",
                "source_url": "https://bank.example/withdrawal",
            },
        ],
        "sources": [
            {
                "id": "src",
                "verified_at": "2026-10-04T00:00:00+00:00",
                "freshness": "HIGH",
            }
        ],
        "conflicts": [],
    }
    result = to_ask_response(
        {
            "requirements": {
                "product_category": "FD",
                "amount": 500000,
                "duration_months": 24,
                "liquidity_preference": "HIGH",
                "missing_information": [],
            },
            "comparisons": [
                {
                    "product": product,
                    "eligible": True,
                    "calculation": {
                        "maturity_amount": 568000,
                        "interest_earned": 68000,
                        "warnings": ["Estimate."],
                    },
                }
            ],
            "sources": [],
            "warnings": [],
        }
    )

    option = result["options"][0]
    assert result["status"] == "OK"
    assert option["rate"] == "6.45%"
    assert option["maturity"] == "₹5,68,000"
    assert option["interest"] == "₹68,000"
    assert option["flexibility"] == "Available"
    assert option["early_exit_amount"] is None
    assert option["early_exit_months"] is None
    assert option["calculation"] == {
        "maturity_amount": 568000,
        "interest_earned": 68000,
        "warnings": ["Estimate."],
    }


def test_ask_endpoint_returns_unchanged_calculator_output_for_each_option():
    from fastapi.testclient import TestClient

    from app.calculators.fd import calculate_fd
    from app.main import app

    response = (
        TestClient(app)
        .post("/api/ask", json={"query": "I have 5 lakh to invest for 2 years"})
        .json()
    )

    assert response["status"] == "OK"
    for option in response["options"]:
        calculation = option["calculation"]
        if calculation is None:
            continue
        assert calculation == calculate_fd(
            calculation["principal"],
            calculation["annual_rate_percent"],
            calculation["tenure_months"],
            calculation["compounding_frequency_per_year"],
        )
        assert calculation["annual_rate_percent"] == option["rate_percent"]
        assert calculation["maturity_amount"] == option["maturity_amount"]
        assert calculation["calculation_version"] == "fd-v1"
