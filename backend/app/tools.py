"""Deterministic financial tools used by ADK evaluations and workflows."""

from app.api.dependencies import get_catalog
from app.domain.rates import calculate_product_fd


def calculate_fd_tool(product_id: str, principal: float, tenure_months: int) -> dict:
    """Calculate FD maturity with Bankwise's deterministic calculator.

    Always call this tool for maturity amounts or interest earned; never do the
    arithmetic yourself. It uses only the product's single eligible rate band
    backed by a current, conflict-free official source.

    Args:
        product_id: Bankwise FD product id from the product catalogue, for
            example "hdfc-bank-regular-fixed-deposit".
        principal: Deposit amount in Indian rupees, for example 500000.
        tenure_months: Deposit tenure in whole months, for example 24.

    Returns:
        A dict with ``status``. CALCULATED includes ``result`` exactly as the
        calculator returned it (maturity_amount, interest_earned,
        calculation_version, warnings). INVALID_INPUT, MISSING, UNAVAILABLE,
        BLOCKED, and UNSUPPORTED include a ``reason``; report it instead of a
        number.
    """
    return calculate_product_fd(
        get_catalog(), product_id, principal, tenure_months
    )
