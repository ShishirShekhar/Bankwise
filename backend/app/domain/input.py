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
_DURATION = re.compile(
    r"(?<![\w.])(?P<value>\d{1,4}(?:\.\d{1,2})?)"
)


def _duration_unit_end(text: str, index: int) -> tuple[str, int] | None:
    """Read a duration unit after a number with linear whitespace scanning."""
    index = _skip_spaces(text, index)
    if index < len(text) and text[index] == "-":
        index = _skip_spaces(text, index + 1)
    for unit in ("years", "year", "months", "month"):
        if text[index : index + len(unit)].casefold() != unit:
            continue
        end = index + len(unit)
        if end == len(text) or not (text[end].isalnum() or text[end] == "_"):
            return unit, end
    return None


def _is_age_expression(query: str, start: int, end: int) -> bool:
    """Recognize age wording using bounded string operations."""
    suffix = query[end:].lstrip()
    if suffix.startswith("-"):
        suffix = suffix[1:].lstrip()
    suffix_lower = suffix.casefold()
    if suffix_lower.startswith("old") and (
        len(suffix_lower) == 3
        or not (suffix_lower[3].isalnum() or suffix_lower[3] == "_")
    ):
        return True
    if suffix_lower.startswith("of age") and (
        len(suffix_lower) == 6
        or not (suffix_lower[6].isalnum() or suffix_lower[6] == "_")
    ):
        return True

    prefix = query[:start].casefold().rstrip()
    for phrase in ("aged", "age", "age is", "i am", "i'm", "im"):
        if prefix.endswith(phrase):
            preceding = prefix[: -len(phrase)]
            if not preceding or not (preceding[-1].isalnum() or preceding[-1] == "_"):
                return True
    return False


def _is_compound_join(separator: str) -> bool:
    """Allow only simple separators between year and month durations."""
    return separator.strip().casefold() in ("", ",", "and", "&")


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


def _extract_tenure_months(query: str) -> int | None:
    """Deposit tenure in months, ignoring ages; None when absent or ambiguous.

    Every year/month expression is considered, not only the first, so an age
    such as "65 years old" is skipped rather than read as the deposit period.
    "1 year 6 months" is combined into 18. Two different remaining durations
    are ambiguous and return None so the user is asked instead of guessed for.
    """
    durations: list[int] = []
    previous_year_end = None
    for match in _DURATION.finditer(query):
        unit_match = _duration_unit_end(query, match.end())
        if unit_match is None:
            continue
        unit, duration_end = unit_match
        if _is_age_expression(query, match.start(), duration_end):
            previous_year_end = None
            continue
        value = float(match.group("value"))
        if unit.startswith("year"):
            durations.append(int(value * 12))
            previous_year_end = duration_end
            continue
        if previous_year_end is not None and _is_compound_join(
            query[previous_year_end : match.start()]
        ):
            durations[-1] += int(value)
        else:
            durations.append(int(value))
        previous_year_end = None
    distinct = set(durations)
    return distinct.pop() if len(distinct) == 1 else None


_AMOUNT_NUMBER = r"(?:\d{1,2}(?:,\d{2})*,\d{3}|\d+)(?:\.\d{1,4})?"
_AMOUNT_SCALE = r"lakhs?|lacs?|crores?|l"
_AMOUNT_CURRENCY = re.compile(r"(?:₹|rs\.?\s*|inr\s*)", re.IGNORECASE)
_AMOUNT_TOKEN = re.compile(
    rf"(?<![\w.,])(?P<number>{_AMOUNT_NUMBER})(?![\d,])\s*(?P<scale>{_AMOUNT_SCALE})?\b",
    re.IGNORECASE,
)
_UNITLESS_AMOUNT_CONTEXT = re.compile(
    r"\b(?:invest(?:ing|ment)?|deposit|put|save|amount|principal|rupees?|inr|rs\.?)\b",
    re.IGNORECASE,
)
def _extract_amount_inr(query: str) -> float | None:
    """Read an explicit INR amount, including Indian grouping and lakh shorthand."""
    for match in _AMOUNT_TOKEN.finditer(query):
        start = match.start()
        prefix = query[:start]
        currency_matches = list(_AMOUNT_CURRENCY.finditer(prefix))
        has_currency = bool(currency_matches and not prefix[currency_matches[-1].end():].strip())
        scale = (match.group("scale") or "").casefold()
        if not scale and not has_currency and "," not in match.group("number"):
            prior = query[max(0, start - 48):start]
            if not _UNITLESS_AMOUNT_CONTEXT.search(prior):
                continue
        numeric = float(match.group("number").replace(",", ""))
        if scale == "l" or scale.startswith(("lakh", "lac")):
            numeric *= 100000
        elif scale.startswith("crore"):
            numeric *= 10000000
        return numeric
    return None


def extract_requirements(query: str, use_gemini: bool = True) -> Requirements:
    """Redact user input, then extract only requirements stated explicitly."""
    return extract_requirements_from_safe_query(
        redact_sensitive_input(query), use_gemini=use_gemini
    )


def extract_requirements_from_safe_query(
    query: str, use_gemini: bool = True
) -> Requirements:
    """Extract requirements from input already passed through redaction."""
    amount = _extract_amount_inr(query)
    tenure = _extract_tenure_months(query)
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
        product_category=_product_category(lowered),
        amount=amount,
        duration_months=tenure,
        liquidity_preference=liquidity,
        premature_withdrawal_important=liquidity == "HIGH",
        missing_information=missing,
    )


def _product_category(query: str) -> str:
    """Recognize unsupported categories without asking a model to guess."""
    if "credit card" in query or "credit-card" in query:
        return "CREDIT_CARD"
    if "savings account" in query or "saving account" in query:
        return "SAVINGS"
    if any(term in query for term in ("loan", "emi", "mortgage")):
        return "LOAN"
    return "FD"
