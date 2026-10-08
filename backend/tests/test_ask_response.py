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
                    "tradeoff": {
                        "is_highest_calculated_maturity": True,
                        "gains": ["Highest estimated return"],
                        "give_ups": ["Standard exit terms apply"],
                    },
                }
            ],
            "tradeoff_summary": "HDFC offers highest return.",
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
    assert option["tradeoff"]["is_highest_calculated_maturity"] is True
    assert "Highest estimated return" in option["tradeoff"]["gains"]
    assert result["tradeoff_summary"] == "HDFC offers highest return."


def test_ask_response_preserves_gemini_explanation_when_present():
    result = to_ask_response(
        {
            "requirements": {
                "product_category": "FD",
                "amount": 500000,
                "duration_months": 24,
                "missing_information": [],
            },
            "comparisons": [
                {
                    "product": {
                        "bank": "Bank A",
                        "name": "FD",
                        "rates": [{"annual_rate_percent": 7.0, "usable_for_calculation": True, "source_id": "s1"}],
                        "sources": [{"id": "s1", "verified_at": "2026-10-04", "freshness": "HIGH"}],
                        "conditions": [],
                    },
                    "eligible": True,
                    "calculation": {"maturity_amount": 570000, "interest_earned": 70000},
                }
            ],
            "explanation": "Custom Gemini 3-part explanation text",
            "sources": [],
            "warnings": [],
        }
    )
    assert result["explanation"] == "Custom Gemini 3-part explanation text"


def test_ask_response_structured_fallback_layout_when_no_ai_explanation():
    result = to_ask_response(
        {
            "requirements": {
                "product_category": "FD",
                "amount": 500000,
                "duration_months": 24,
                "missing_information": [],
            },
            "comparisons": [
                {
                    "product": {
                        "bank": "Bank A",
                        "name": "FD",
                        "rates": [{"annual_rate_percent": 7.0, "usable_for_calculation": True, "source_id": "s1"}],
                        "sources": [{"id": "s1", "verified_at": "2026-10-04", "freshness": "HIGH"}],
                        "conditions": [],
                    },
                    "eligible": True,
                    "calculation": {"maturity_amount": 570000, "interest_earned": 70000},
                }
            ],
            "tradeoff_summary": "Bank A yields more than Bank B.",
            "sources": [],
            "warnings": [],
        }
    )
    assert "1. Executive Decision Summary:" in result["explanation"]
    assert "2. The Key Trade-off ('What Am I Giving Up?'): Bank A yields more than Bank B." in result["explanation"]
    assert "3. Conditions & Transparency:" in result["explanation"]
