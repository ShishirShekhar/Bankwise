from decimal import Decimal, ROUND_HALF_UP


def calculate_fd(
    principal: float,
    annual_rate: float,
    tenure_months: int,
    compounding_frequency: int = 4,
):
    """
    Calculate FD maturity using compound interest.

    This is an MVP calculation engine.
    Bank-specific calculation rules can be added later.
    """

    if principal <= 0:
        raise ValueError("Principal must be greater than 0.")

    if annual_rate < 0:
        raise ValueError("Interest rate cannot be negative.")

    if tenure_months <= 0:
        raise ValueError("Tenure must be greater than 0 months.")

    if compounding_frequency <= 0:
        raise ValueError("Compounding frequency must be greater than 0.")

    principal_decimal = Decimal(str(principal))
    rate_decimal = Decimal(str(annual_rate)) / Decimal("100")

    tenure_years = Decimal(str(tenure_months)) / Decimal("12")

    n = Decimal(str(compounding_frequency))

    maturity = principal_decimal * (
        Decimal("1") + rate_decimal / n
    ) ** (n * tenure_years)

    maturity = maturity.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )

    interest = maturity - principal_decimal

    return {
        "principal": float(principal_decimal),
        "interest_rate": annual_rate,
        "tenure_months": tenure_months,
        "compounding_frequency": compounding_frequency,
        "interest_earned": float(interest),
        "maturity_amount": float(maturity),
        "currency": "INR",
        "calculation_version": "fd-v1",
        "warnings": []
    }