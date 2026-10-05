from decimal import ROUND_HALF_UP, Decimal, localcontext

# bank -> {tenure_months: annual rate percent}. FICTIONAL demo values.
DEMO_RATES: dict[str, dict[int, float]] = {
    "alpha": {12: 6.90, 24: 7.25},
    "bravo": {12: 6.80, 24: 7.00},
    "charlie": {24: 6.90},  # no 12-month rate on purpose: tests the "no rate" path
}
CENT = Decimal("0.01")

DEMO_TERMS = {
    "alpha": {"penalty_pp": 1.5, "lock_in_months": 6},
    "bravo": {"penalty_pp": 0.5, "lock_in_months": 0},
    "charlie": {"penalty_pp": 1.0, "lock_in_months": 0},
}


def calculate_early_withdrawal(
    bank: str, principal: float, tenure_months: int, months_held: int
) -> dict:
    """Calculate the amount received if a fixed deposit is broken early.

    Method (demo assumption): interest accrues for the months held at the contract rate
    minus the bank's penalty. Real banks differ, so state this method when reporting.

    Args:
        bank: Bank name, e.g. "alpha".
        principal: Deposit amount in rupees.
        tenure_months: Original deposit length in months.
        months_held: Months the money stayed invested before withdrawal.
    """
    terms = DEMO_TERMS.get(bank.lower())
    rate = lookup_rate(bank, tenure_months)
    if terms is None or rate is None:
        return {"error": "no_terms"}
    if months_held >= tenure_months:
        return {"error": "not_early"}
    if months_held < terms["lock_in_months"]:
        return {"error": "locked_in", "lock_in_months": terms["lock_in_months"]}
    try:
        amount = fd_maturity(principal, max(rate - terms["penalty_pp"], 0), months_held)
    except ValueError as e:
        return {"error": str(e)}
    return {
        "bank": bank,
        "months_held": months_held,
        "penalty_pp": terms["penalty_pp"],
        "lock_in_months": terms["lock_in_months"],
        "method": "contract rate minus penalty, for months held",
        "amount_received": float(amount),
    }


def lookup_rate(bank: str, tenure_months: int) -> float | None:
    return DEMO_RATES.get(bank.lower(), {}).get(tenure_months)


def fd_maturity(
    principal: float, rate_percent: float, tenure_months: int, n: int = 4
) -> Decimal:
    """Plain calculator: A = P * (1 + r/n) ** (n * t). Not a tool; the agent never calls it directly."""
    if principal <= 0 or tenure_months <= 0 or rate_percent < 0:
        raise ValueError(
            "principal and tenure must be positive, rate cannot be negative"
        )
    p = Decimal(str(principal))
    r = Decimal(str(rate_percent)) / 100
    years = Decimal(tenure_months) / 12
    with localcontext() as ctx:
        ctx.prec = 40
        return (p * (1 + r / n) ** (n * years)).quantize(CENT, rounding=ROUND_HALF_UP)


def get_fd_rate(bank: str, tenure_months: int = 24) -> dict:
    """Return a bank's stored FD interest rate for a tenure.

    Args:
        bank: Bank name, e.g. "alpha".
        tenure_months: Deposit length in months. Defaults to 24.
    """
    if bank.lower() not in DEMO_RATES:
        return {"error": "unknown_bank"}
    rate = lookup_rate(bank, tenure_months)
    if rate is None:
        return {"error": "no_rate_for_tenure"}
    return {"bank": bank, "tenure_months": tenure_months, "rate_percent": rate}


def calculate_fd_maturity(bank: str, principal: float, tenure_months: int) -> dict:
    """Calculate what a fixed deposit grows to, using the bank's stored rate for that tenure.

    Args:
        bank: Bank name, e.g. "alpha".
        principal: Deposit amount in rupees.
        tenure_months: Deposit length in months.
    """
    if bank.lower() not in DEMO_RATES:
        return {"error": "unknown_bank"}
    rate = lookup_rate(bank, tenure_months)
    if rate is None:
        return {"error": "no_rate_for_tenure"}
    try:
        maturity = fd_maturity(principal, rate, tenure_months)
    except ValueError as e:
        return {"error": str(e)}
    return {
        "bank": bank,
        "rate_percent": rate,
        "compounding": "quarterly",
        "maturity_amount": float(maturity),
        "interest_earned": float(maturity - Decimal(str(principal))),
    }
