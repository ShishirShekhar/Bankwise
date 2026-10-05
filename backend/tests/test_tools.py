from app.ai.tools import calculate_fd_maturity
from app.ai.tools import calculate_early_withdrawal

import pytest


def test_alpha_two_years():
    out = calculate_fd_maturity("alpha", 100000, 24)
    assert out["maturity_amount"] == 115453.95


def test_unknown_bank_returns_error():
    assert calculate_fd_maturity("zeta", 100000, 24) == {"error": "unknown_bank"}


def test_early_withdrawal_uses_rate_minus_penalty():
    out = calculate_early_withdrawal("alpha", 500000, 24, 12)
    expected = 500000 * (1 + 0.0575 / 4) ** 4  # 7.25% - 1.5 pp
    assert out["amount_received"] == pytest.approx(expected, abs=0.01)


def test_lock_in_blocks_early_exit():
    assert calculate_early_withdrawal("alpha", 500000, 24, 3) == {"error": "locked_in", "lock_in_months": 6}


def test_withdrawing_at_maturity_is_not_early():
    assert calculate_early_withdrawal("bravo", 500000, 24, 24) == {"error": "not_early"}