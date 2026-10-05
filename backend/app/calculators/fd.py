from decimal import Decimal, ROUND_HALF_UP
from typing import Optional


class CalculationError(ValueError):
    pass


def calculate_fd(
    principal: float,
    annual_rate: float,
    tenure_months: int,
    compounding_frequency: Optional[int],
) -> dict:
    """Calculate cumulative FD maturity using the explicitly supplied compounding rule.

    Rate is an annual percentage (7.25 means 7.25%). The result is rounded to paise.
    This generic formula is not a substitute for bank-specific day-count or rounding rules.
    """
    if principal <= 0 or tenure_months <= 0 or annual_rate < 0:
        raise CalculationError(
            "Principal and tenure must be positive; rate cannot be negative"
        )
    if compounding_frequency is None or compounding_frequency <= 0:
        raise CalculationError(
            "A sourced compounding frequency is required for cumulative calculation"
        )
    p = Decimal(str(principal))
    rate = Decimal(str(annual_rate)) / Decimal("100")
    n = Decimal(compounding_frequency)
    years = Decimal(tenure_months) / Decimal("12")
    # Decimal power requires an integer exponent, so use a high precision local context.
    from decimal import localcontext

    with localcontext() as ctx:
        ctx.prec = 40
        maturity = p * (Decimal(1) + rate / n) ** (n * years)
        maturity = maturity.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    interest = (maturity - p).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {
        "principal": float(p.quantize(Decimal("0.01"))),
        "annual_rate_percent": float(Decimal(str(annual_rate))),
        "tenure_months": tenure_months,
        "compounding_frequency_per_year": compounding_frequency,
        "interest_earned": float(interest),
        "maturity_amount": float(maturity),
        "currency": "INR",
        "calculation_version": "fd-v1",
        "warnings": [
            "Uses generic compound interest; bank-specific day-count and rounding rules may differ."
        ],
    }
