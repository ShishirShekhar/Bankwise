from app.domain.input import redact_sensitive_input


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
