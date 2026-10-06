"""Focused service operations: input."""

import re

from google.genai.errors import APIError
from pydantic import ValidationError

from app.config import GEMINI_MODEL
from app.schemas import Requirements

_SENSITIVE_LABEL = re.compile(
    r"\b(?:PAN|Aadhaar|account number|card number|CVV|UPI PIN|banking password)\b",
    re.IGNORECASE,
)
_SENSITIVE_VALUE = re.compile(r"[A-Z0-9-]{4,}", re.IGNORECASE)
_PAN_VALUE = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.IGNORECASE)


def redact_sensitive_input(query: str) -> str:
    """Remove common credential/identity values before sending free text to a model."""
    # Match labels separately, then scan whitespace and the optional delimiter once.
    # This avoids ambiguous unbounded repetitions in a regex over user-controlled text.
    parts = []
    cursor = 0
    for label in _SENSITIVE_LABEL.finditer(query):
        value_start = label.end()
        while value_start < len(query) and query[value_start].isspace():
            value_start += 1
        if query[value_start : value_start + 2].lower() == "is" and (
            value_start + 2 == len(query) or not query[value_start + 2].isalnum()
        ):
            value_start += 2
        elif value_start < len(query) and query[value_start] in ":=":
            value_start += 1
        while value_start < len(query) and query[value_start].isspace():
            value_start += 1
        value = _SENSITIVE_VALUE.match(query, value_start)
        if value and value.end() - value.start() >= 4:
            parts.extend((query[cursor : label.start()], "[REDACTED]"))
            cursor = value.end()
    if parts:
        parts.append(query[cursor:])
        redacted = "".join(parts)
    else:
        redacted = query
    redacted = _PAN_VALUE.sub("[REDACTED]", redacted)
    return _redact_long_numbers(redacted)


def _redact_long_numbers(text: str) -> str:
    """Redact 12- or 16-digit values, scanning digits and separators linearly."""
    parts = []
    cursor = 0
    index = 0
    while index < len(text):
        if not text[index].isdigit() or (index > 0 and text[index - 1].isdigit()):
            index += 1
            continue
        start = index
        end = index
        digits = 0
        while end < len(text) and text[end].isdigit():
            digits += 1
            end += 1
            if (
                end < len(text)
                and text[end] in " -"
                and end + 1 < len(text)
                and text[end + 1].isdigit()
            ):
                end += 1
        if digits in (12, 16) and (end == len(text) or not text[end].isdigit()):
            parts.extend((text[cursor:start], "[REDACTED]"))
            cursor = end
            index = end
        else:
            index = max(end, index + 1)
    if not parts:
        return text
    parts.append(text[cursor:])
    return "".join(parts)


def extract_requirements(query: str, use_gemini: bool = True) -> Requirements:
    """Use Gemini when configured; otherwise extract only values stated explicitly."""
    query = redact_sensitive_input(query)
    amount_match = re.search(
        r"(?:(?:₹|rs\.?\s*|inr\s*)(?P<currency_amount>[\d,]{1,24}(?:\.\d{1,4})?)\s*(?P<currency_scale>lakhs?|lacs?|crores?)?"
        r"|(?<![\w.])(?P<bare_amount>[\d,]{1,24}(?:\.\d{1,4})?)\s*(?P<bare_scale>lakhs?|lacs?|crores?)\b)",
        query,
        re.IGNORECASE,
    )
    amount = None
    if amount_match:
        raw_amount = amount_match.group("currency_amount") or amount_match.group(
            "bare_amount"
        )
        scale = (
            amount_match.group("currency_scale")
            or amount_match.group("bare_scale")
            or ""
        ).lower()
        amount = float(raw_amount.replace(",", ""))
        amount *= (
            100000
            if scale.startswith(("lakh", "lac"))
            else 10000000 if scale.startswith("crore") else 1
        )
    tenure = None
    years = re.search(r"(\d{1,4}(?:\.\d{1,2})?)\s*years?", query, re.IGNORECASE)
    months = re.search(r"(\d{1,4})\s*months?", query, re.IGNORECASE)
    if years:
        tenure = int(float(years.group(1)) * 12)
    elif months:
        tenure = int(months.group(1))
    try:
        from google import genai
        from google.genai import types

        from app.config import GOOGLE_CLOUD_LOCATION, GOOGLE_CLOUD_PROJECT

        if use_gemini and GOOGLE_CLOUD_PROJECT:
            client = genai.Client(
                vertexai=True,
                project=GOOGLE_CLOUD_PROJECT,
                location=GOOGLE_CLOUD_LOCATION,
            )
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=(
                    "Extract stated FD requirements and preferences. Never infer an amount or duration that is not explicit. "
                    "Return the requested JSON fields. Do not request/store sensitive banking credentials. Query: "
                    + query
                ),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=Requirements,
                    temperature=0,
                ),
            )
            parsed = Requirements.model_validate_json(response.text or "{}")
            # Numeric facts must be found in the user text by deterministic parsing.
            parsed.amount = amount
            parsed.duration_months = tenure
            parsed.missing_information = (["amount"] if amount is None else []) + (
                ["duration_months"] if tenure is None else []
            )
            return parsed
    except (APIError, ImportError, RuntimeError, OSError, ValidationError, ValueError):
        # Keep local operation available when credentials or Vertex AI are unavailable.
        pass
    missing = []
    if amount is None:
        missing.append("amount")
    if tenure is None:
        missing.append("duration_months")
    lowered = query.lower()
    liquidity = (
        "HIGH"
        if any(x in lowered for x in ("early", "withdraw", "liquid", "flexib"))
        else None
    )
    return Requirements(
        amount=amount,
        duration_months=tenure,
        liquidity_preference=liquidity,
        premature_withdrawal_important=liquidity == "HIGH",
        missing_information=missing,
    )
