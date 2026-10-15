from app.ai.ask_response import to_ask_response


def test_ask_response_matches_comparison_card_fields_and_does_not_guess_exit_date():
    product = {
        "id": "hdfc-fd",
        "bank": {"id": "hdfc", "name": "HDFC Bank", "website": "https://hdfcbank.com"},
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
            {"type": "premature_withdrawal_allowed", "value": True, "verified": True},
            {
                "type": "premature_withdrawal_policy",
                "value": "One percentage point is deducted.",
                "verified": True,
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
    assert option["bank"] == "HDFC Bank"
    assert "HDFC Bank has the highest calculated maturity" in result["explanation"]
    assert option["rate"] == "6.45%"
    assert option["maturity"] == "₹5,68,000"
    assert option["interest"] == "₹68,000"
    assert option["flexibility"] == "Available"
    assert option["early_exit_amount"] is None
    assert option["early_exit_months"] is None
    assert option["tradeoff"]["is_highest_calculated_maturity"] is True
    assert "Highest estimated return" in option["tradeoff"]["gains"]
    assert result["tradeoff_summary"] == "HDFC offers highest return."


def test_ask_response_does_not_surface_unverified_withdrawal_conditions():
    product = {
        "bank": "Bank A",
        "name": "FD",
        "rates": [{"annual_rate_percent": 7.0, "usable_for_calculation": True, "source_id": "s1"}],
        "sources": [{"id": "s1", "verified_at": "2026-10-04", "freshness": "HIGH"}],
        "conditions": [
            {"type": "premature_withdrawal_allowed", "value": True, "verified": False},
            {
                "type": "premature_withdrawal_policy",
                "value": "A 9% penalty applies.",
                "verified": False,
            },
            {
                "type": "premature_withdrawal_penalty_percentage_points",
                "value": 9,
                "verified": False,
            },
        ],
    }
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
                    "product": product,
                    "eligible": True,
                    "calculation": {"maturity_amount": 570000, "interest_earned": 70000},
                }
            ],
            "warnings": [],
        }
    )

    option = result["options"][0]
    assert option["flexibility"] == "Terms unavailable"
    assert option["penalty_pp"] is None
    assert "9%" not in option["early_exit_note"]


def test_ask_response_ignores_model_text_and_uses_source_grounded_layout():
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
            "explanation": "The rate is guaranteed to be 99%.",
            "sources": [],
            "warnings": [],
        }
    )
    assert "guaranteed to be 99%" not in result["explanation"]
    assert "1. Executive Decision Summary:" in result["explanation"]
    assert "2. The Key Trade-off" in result["explanation"]
    assert "3. Conditions & Transparency:" in result["explanation"]
    assert "4 times per year" not in result["explanation"]


def test_ask_response_structured_layout_when_calculation_terms_are_missing():
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
    assert "compounding terms are missing" in result["explanation"]


def _early_option(bank, penalty, source_url):
    return {
        "product": {
            "bank": bank,
            "name": "FD",
            "rates": [{"annual_rate_percent": 6.0, "usable_for_calculation": True, "source_id": "s1"}],
            "sources": [{"id": "s1", "verified_at": "2026-10-04", "freshness": "HIGH"}],
            "conditions": [
                {"type": "premature_withdrawal_allowed", "value": True, "verified": True},
                {
                    "type": "premature_withdrawal_penalty_percentage_points",
                    "value": penalty,
                    "verified": penalty is not None,
                    "verification_status": "CONFLICT" if penalty is None else "HIGH",
                    "source_url": source_url,
                },
                {
                    "type": "premature_withdrawal_policy",
                    "value": "Penalty applies to premature withdrawal.",
                    "verified": True,
                    "source_url": source_url,
                },
            ],
        },
        "eligible": True,
        "calculation": {"maturity_amount": 110000, "interest_earned": 10000},
    }


def _early_result(comparisons):
    return to_ask_response(
        {
            "requirements": {
                "product_category": "FD",
                "amount": 100000,
                "duration_months": 24,
                "liquidity_preference": "HIGH",
                "premature_withdrawal_important": True,
                "missing_information": [],
            },
            "comparisons": comparisons,
            "tradeoff_summary": "Compare verified withdrawal terms.",
            "warnings": [],
        }
    )


def test_early_withdrawal_rank_uses_only_complete_verified_penalties():
    result = _early_result(
        [
            _early_option("Bank A", 1.0, "https://bank.example/a"),
            _early_option("Bank B", 0.5, "https://bank.example/b"),
        ]
    )

    assert result["best_if_withdrawn_early"] == {
        "status": "RANKED",
        "bank": "Bank B",
        "penalty_pp": 0.5,
        "source_url": "https://bank.example/b",
        "ranking_basis": "lowest verified premature-withdrawal penalty",
        "payout_note": "A withdrawal date and actual holding-period rate are required to calculate an early-exit amount.",
    }
    assert "liquidity preference is high" in result["explanation"]


def test_early_withdrawal_ranking_discloses_missing_or_conflicted_terms():
    result = _early_result(
        [
            _early_option("Bank A", 0.5, "https://bank.example/a"),
            _early_option("Bank B", None, "https://bank.example/b"),
        ]
    )

    assert result["best_if_withdrawn_early"]["status"] == "INSUFFICIENT_DATA"
    assert result["best_if_withdrawn_early"]["unranked_banks"] == ["Bank B"]
