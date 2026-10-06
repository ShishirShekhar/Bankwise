from app.domain.input import extract_requirements, redact_sensitive_input


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
    assert extract_requirements("₹1.5 crore for 1 year", use_gemini=False).amount == 15000000
