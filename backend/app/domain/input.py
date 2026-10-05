"""Focused service operations: input."""

import re

from app.config import GEMINI_MODEL
from app.schemas import Requirements


def redact_sensitive_input(query: str) -> str:
    """Remove common credential/identity values before sending free text to a model."""
    redacted = re.sub(
        r"(?i)\b(?:PAN|Aadhaar|account number|card number|CVV|UPI PIN|banking password)\b\s*(?:is|:|=)?\s*[A-Z0-9-]{4,}",
        "[REDACTED]",
        query,
    )
    redacted = re.sub(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", "[REDACTED]", redacted, flags=re.I)
    redacted = re.sub(r"(?<!\d)(?:\d[ -]?){11}\d(?!\d)", "[REDACTED]", redacted)
    redacted = re.sub(r"(?<!\d)(?:\d[ -]?){15}\d(?!\d)", "[REDACTED]", redacted)
    return redacted


def extract_requirements(query: str, use_gemini: bool = True) -> Requirements:
    """Use Gemini when configured; otherwise extract only values stated explicitly."""
    query = redact_sensitive_input(query)
    amount_match = re.search(
        r"(?:₹|rs\.?\s*|inr\s*)([\d,]+(?:\.\d+)?)\s*(lakh|lac| lakhs|crore)?",
        query,
        re.I,
    )
    amount = None
    if amount_match:
        amount = float(amount_match.group(1).replace(",", ""))
        scale = (amount_match.group(2) or "").strip().lower()
        amount *= (
            100000
            if scale.startswith(("lakh", "lac"))
            else 10000000 if scale == "crore" else 1
        )
    tenure = None
    years = re.search(r"(\d+(?:\.\d+)?)\s*years?", query, re.I)
    months = re.search(r"(\d+)\s*months?", query, re.I)
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
    except Exception:
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
