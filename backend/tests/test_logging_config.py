import json
import logging

from app.logging_config import JsonFormatter


def test_json_formatter_emits_safe_structured_fields_only():
    record = logging.LogRecord(
        name="bankwise.integrations.bigquery",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="BigQuery operation failed",
        args=(),
        exc_info=(ValueError, ValueError("sensitive exception detail"), None),
    )
    record.request_id = "a" * 32
    record.event = "integration_error"
    record.integration = "bigquery"
    record.operation = "query"
    record.error_type = "TimeoutError"

    formatted = json.loads(JsonFormatter().format(record))

    assert formatted["severity"] == "ERROR"
    assert formatted["request_id"] == "a" * 32
    assert formatted["integration"] == "bigquery"
    assert formatted["operation"] == "query"
    assert formatted["error_type"] == "TimeoutError"
    assert "exception" not in formatted
    assert "sensitive exception detail" not in json.dumps(formatted)
