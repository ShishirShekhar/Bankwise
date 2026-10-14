import pytest

from app.domain.input import extract_requirements


@pytest.mark.parametrize(
    ("query", "amount", "months"),
    [
        # Issue #119 reproduction: age must not become the deposit duration.
        ("I am 65 years old, 3 lakh for 3 years", 300000, 36),
        ("I'm 70 years old and have 5 lakh for 18 months", 500000, 18),
        ("65-year-old with 2 lakh for 2 years", 200000, 24),
        ("My age is 60 years and I have 4 lakh for 2 years", 400000, 24),
        ("I am 62 years of age, 1 lakh for 1 year", 100000, 12),
        # Durations without an age keep working.
        ("5 lakh for 2 years", 500000, 24),
        ("5 lakh for 1.5 years", 500000, 18),
        ("1 lakh for 18 months", 100000, 18),
        ("2 lakh for 1 year 6 months", 200000, 18),
        ("2 lakh for 1 year and 6 months", 200000, 18),
        ("2 lakh for 2 years and 2 years is fine", 200000, 24),
    ],
)
def test_extracts_deposit_duration_and_ignores_age(query, amount, months):
    requirements = extract_requirements(query, use_gemini=False)
    assert requirements.amount == amount
    assert requirements.duration_months == months
    assert requirements.missing_information == []


def test_age_alone_is_not_a_duration():
    requirements = extract_requirements(
        "I am 65 years old and have 3 lakh", use_gemini=False
    )
    assert requirements.amount == 300000
    assert requirements.duration_months is None
    assert requirements.missing_information == ["duration_months"]


def test_conflicting_durations_ask_for_clarification():
    requirements = extract_requirements(
        "5 lakh for 2 years or 3 years", use_gemini=False
    )
    assert requirements.duration_months is None
    assert "duration_months" in requirements.missing_information
