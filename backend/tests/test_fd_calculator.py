
import pytest

from app.calculators.fd import CalculationError, calculate_fd


def test_compound_calculation_is_deterministic_and_paise_rounded():
    result = calculate_fd(100000, 6.0, 12, 4)
    assert result["maturity_amount"] == 106136.36
    assert result["interest_earned"] == 6136.36
    assert result["calculation_version"] == "fd-v1"


@pytest.mark.parametrize(
    "principal,rate,tenure", [(0, 5, 12), (100, -1, 12), (100, 5, 0)]
)
def test_rejects_invalid_inputs(principal, rate, tenure):
    with pytest.raises(CalculationError):
        calculate_fd(principal, rate, tenure, 4)


def test_requires_explicit_compounding_frequency():
    with pytest.raises(CalculationError):
        calculate_fd(1000, 5, 12, None)
