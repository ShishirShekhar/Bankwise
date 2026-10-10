"""Production-friendly JSON logging for Cloud Run's structured log ingestion."""

import json
import logging
import os
from contextvars import ContextVar
from datetime import UTC, datetime

request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, object] = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "timestamp": datetime.now(UTC).isoformat(),
            "logger": record.name,
        }
        request_id = getattr(record, "request_id", None) or request_id_context.get()
        if request_id:
            entry["request_id"] = request_id
        for key in (
            "request_id",
            "method",
            "route",
            "status_code",
            "duration_ms",
            "event",
            "error_type",
            "integration",
            "operation",
        ):
            value = getattr(record, key, None)
            if value is not None:
                entry[key] = value
        return json.dumps(entry, ensure_ascii=False, separators=(",", ":"))


def configure_logging() -> None:
    """Emit one JSON object per line; Cloud Run captures stdout/stderr automatically."""
    level_name = os.getenv("LOG_LEVEL", "INFO")
    level = getattr(logging, level_name.upper(), None)
    if not isinstance(level, int):
        raise TypeError("LOG_LEVEL must be a valid Python logging level")
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    # Keep framework access logs off: they can contain raw URLs and query strings.
    logging.getLogger("uvicorn.access").disabled = True
