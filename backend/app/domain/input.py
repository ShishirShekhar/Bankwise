"""Focused service operations: input."""

import re

from google.genai.errors import APIError
from pydantic import ValidationError

from app.config import GEMINI_MODEL
from app.schemas import Requirements

_SENSITIVE_LABEL = re.compile(
    r"\b(?:PAN|Aadhaa?r|account|acct|a/c|card|CVV|CVC|UPI|MPIN|PIN|OTP"
    r"|(?:net\s?)?banking\s+password|password|passcode)(?!\w)",
    re.IGNORECASE,
)
# Words that may sit between a label and its value, e.g. "account no. is: 1234".
_LABEL_FILLERS = {"number", "no", "no.", "num", "id", "is", "pin", ":", "=", "-", "#"}
_FREE_TEXT_LABELS = ("password", "passcode")
_PAN_VALUE = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.IGNORECASE)
# UPI IDs (name@bank) and email addresses; bounded to keep matching linear.
_HANDLE_VALUE = re.compile(r"\b[\w.-]{1,64}@[A-Za-z][\w.-]{1,63}")
_REDACTED = "[REDACTED]"


def _skip_spaces(text: str, index: int) -> int:
    while index < len(text) and text[index].isspace():
        index += 1
    return index


def _scan_grouped_digits(text: str, index: int) -> tuple[int, int]:
    """Return (end, digit_count) for digits joined by single spaces or hyphens."""
    end, digits = index, 0
    while end < len(text) and text[end].isdigit():
        digits += 1
        end += 1
        if end + 1 < len(text) and text[end] in " -" and text[end + 1].isdigit():
            end += 1
    return end, digits


def _labelled_value_end(text: str, label_end: int, free_text: bool) -> int | None:
    """End index of the secret that follows a label, or None if none follows."""
    index = _skip_spaces(text, label_end)
    for _ in range(4):
        word_end = index
        while word_end < len(text) and not text[word_end].isspace():
            word_end += 1
        word = text[index:word_end].lower()
        if word in _LABEL_FILLERS or word.rstrip(":=#-") in _LABEL_FILLERS:
            index = _skip_spaces(text, word_end)
        elif word[:1] in (":", "=", "-", "#") and len(word) > 1:
            index += 1
        else:
            break
    if index < len(text) and text[index].isdigit():
        end, _ = _scan_grouped_digits(text, index)
    else:
        end = index
        while end < len(text) and not text[end].isspace():
            end += 1
        while end > index and text[end - 1] in ".,;)":
            end -= 1
        token = text[index:end]
        if not free_text and not any(ch.isdigit() or ch == "@" for ch in token):
            return None
    return end if end - index >= 3 else None


def redact_sensitive_input(query: str) -> str:
    """Remove identity, account, card, and credential values before any model call.

    Labelled values (``PAN``, ``Aadhaar``, ``account no.``, ``card``, ``CVV``,
    ``UPI ID/PIN``, ``MPIN``, ``OTP``, ``PIN``, ``password``) are redacted with
    their label. PAN-shaped codes, 12-19 digit numbers (Aadhaar and card
    numbers), and UPI IDs or email addresses are redacted anywhere. All scans
    are linear in the input length.
    """
    parts = []
    cursor = 0
    for label in _SENSITIVE_LABEL.finditer(query):
        if label.start() < cursor:
            continue
        free_text = label.group().lower().endswith(_FREE_TEXT_LABELS)
        value_end = _labelled_value_end(query, label.end(), free_text)
        if value_end is not None:
            parts.extend((query[cursor : label.start()], _REDACTED))
            cursor = value_end
    if parts:
        parts.append(query[cursor:])
        redacted = "".join(parts)
    else:
        redacted = query
    redacted = _PAN_VALUE.sub(_REDACTED, redacted)
    redacted = _HANDLE_VALUE.sub(_REDACTED, redacted)
    return _redact_long_numbers(redacted)


def _redact_long_numbers(text: str) -> str:
    """Redact 12-19 digit values (Aadhaar, card numbers), scanning linearly."""
    parts = []
    cursor = 0
    index = 0
    while index < len(text):
        if not text[index].isdigit() or (index > 0 and text[index - 1].isdigit()):
            index += 1
            continue
        start = index
        end, digits = _scan_grouped_digits(text, index)
        if 12 <= digits <= 19:
            parts.extend((text[cursor:start], _REDACTED))
            cursor = end
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
            else 10000000
            if scale.startswith("crore")
            else 1
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
