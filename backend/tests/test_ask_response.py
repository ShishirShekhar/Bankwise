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


def _ok_result(liquidity_preference, frequencies=(4,), **extra_requirements):
    comparisons = []
    for index, frequency in enumerate(frequencies):
        comparisons.append(
            {
                "product": {
                    "id": f"fd-{index}",
                    "bank": f"Bank {index}",
                    "name": "Regular Fixed Deposit",
                    "rates": [
                        {
                            "annual_rate_percent": 6.45,
                            "ineligibility_reason": None,
                            "usable_for_calculation": True,
                            "source_id": "src",
                        }
                    ],
                    "conditions": [],
                    "sources": [{"id": "src", "freshness": "HIGH"}],
                    "conflicts": [],
                },
                "eligible": True,
                "calculation": {
                    "maturity_amount": 568000 + index,
                    "interest_earned": 68000 + index,
                    "compounding_frequency_per_year": frequency,
                    "warnings": ["Estimate."],
                },
            }
        )
    return to_ask_response(
        {
            "requirements": {
                "product_category": "FD",
                "amount": 500000,
                "duration_months": 24,
                "liquidity_preference": liquidity_preference,
                "missing_information": [],
                **extra_requirements,
            },
            "comparisons": comparisons,
        }
    )


def test_explanation_mentions_early_withdrawal_only_for_high_liquidity():
    high = _ok_result("HIGH")["explanation"]
    assert "You mentioned possible early withdrawal" in high
    assert "Review each option's sourced withdrawal terms." in high

    for preference in ("LOW", None):
        explanation = _ok_result(preference)["explanation"]
        assert "early withdrawal" not in explanation
        assert "withdrawal date" not in explanation


def test_explanation_mentions_early_withdrawal_when_flagged_important():
    result = _ok_result(None, premature_withdrawal_important=True)
    assert result["status"] == "OK"
    assert "You mentioned possible early withdrawal" in result["explanation"]


def test_explanation_describes_compounding_from_calculation():
    quarterly = _ok_result("LOW", frequencies=(4, 4))["explanation"]
    assert "cumulative FD with quarterly reinvestment" in quarterly

    monthly = _ok_result("LOW", frequencies=(12,))["explanation"]
    assert "cumulative FD with monthly reinvestment" in monthly
    assert "quarterly" not in monthly

    mixed = _ok_result("LOW", frequencies=(4, 12))["explanation"]
    assert "Estimates assume a cumulative FD and may differ" in mixed
    assert "quarterly" not in mixed
    assert "monthly" not in mixed
