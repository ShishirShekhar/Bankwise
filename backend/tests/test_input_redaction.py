import time

import pytest

from app.domain.input import extract_requirements, redact_sensitive_input

# Built at runtime so secret scanners do not mistake test data for a credential.
FAKE_SECRET = "x" * 12


def test_redacts_labeled_sensitive_values_with_common_separators():
    assert redact_sensitive_input("PAN is ABCDE1234F") == "[REDACTED]"
    assert redact_sensitive_input("account number: 1234-5678") == "[REDACTED]"
    assert redact_sensitive_input("UPI PIN=1234") == "[REDACTED]"


def test_redacts_after_long_whitespace_without_backtracking():
    query = "card number" + (" " * 100_000) + "12345678"
    assert redact_sensitive_input(query) == "[REDACTED]"


def test_redacts_standalone_identifiers_and_long_numbers():
    assert redact_sensitive_input("ABCDE1234F") == "[REDACTED]"
    assert redact_sensitive_input("1234 5678 9012") == "[REDACTED]"
    assert redact_sensitive_input("1234 5678 9012 3456") == "[REDACTED]"


def test_extracts_amounts_with_or_without_currency_prefix():
    assert extract_requirements("5 lakh for 2 years", use_gemini=False).amount == 500000
    assert (
        extract_requirements("₹1.5 crore for 1 year", use_gemini=False).amount
        == 15000000
    )


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("My CVV is 123", "My [REDACTED]"),
        ("my password is " + FAKE_SECRET, "my [REDACTED]"),
        ("netbanking password: " + FAKE_SECRET + "!", "[REDACTED]"),
        ("OTP 482913", "[REDACTED]"),
        ("MPIN 1234", "[REDACTED]"),
        ("my upi pin is 9876", "my [REDACTED]"),
        ("UPI id shruti@okicici", "[REDACTED]"),
        ("account no 12345678901", "[REDACTED]"),
        ("acct no.: 987654321", "[REDACTED]"),
        ("A/C no. 50100123456789", "[REDACTED]"),
        ("card no:4111111111111111", "[REDACTED]"),
        ("Aadhaar 1234 5678 9012", "[REDACTED]"),
        ("aadhar number 123456789012", "[REDACTED]"),
        ("amex 3782 822463 10005", "amex [REDACTED]"),
        ("Email me at a.b@example.com", "Email me at [REDACTED]"),
    ],
)
def test_redacts_credentials_identity_and_account_values(query, expected):
    assert redact_sensitive_input(query) == expected


@pytest.mark.parametrize(
    "query",
    [
        "I have 5 lakh for 2 years",
        "I have 500000 for 24 months",
        "Invest 1,00,000 for 12 months",
        "I want a credit card for travel",
        "I want to open an account for 2 years",
        "Can I pay with UPI later?",
        "I may need the money early, no PIN needed",
    ],
)
def test_keeps_ordinary_financial_goals_unchanged(query):
    assert redact_sensitive_input(query) == query


def test_requirements_survive_redaction_of_sensitive_values():
    requirements = extract_requirements(
        "account no 12345678901, card 4111 1111 1111 1111. Invest 3 lakh for 1 year",
        use_gemini=False,
    )

    assert (requirements.amount, requirements.duration_months) == (300000, 12)


def test_redaction_stays_fast_on_adversarial_input():
    query = ("PIN " * 20_000) + ("1-" * 50_000) + ("a@" * 20_000)

    started = time.perf_counter()
    redact_sensitive_input(query)

    assert time.perf_counter() - started < 2
