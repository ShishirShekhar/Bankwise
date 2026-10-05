import os
from typing import Literal

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.config import GEMINI_MODEL, GOOGLE_CLOUD_LOCATION, GOOGLE_CLOUD_PROJECT

SYSTEM_PROMPT = """You extract requirements for a fixed deposit (FD) tool used in India.
Return JSON only.
- category: "FD" for fixed deposits or investing a lump sum; "LOAN", "CREDIT_CARD", "SAVINGS" for those products; "OTHER" for anything else. null if unclear.
- amount: the USER'S OWN money in rupees, as a number. 1 lakh = 100000, 1 crore = 10000000, 5k = 5000, "five lakh" = 500000. Ignore other people's money. null if not stated.
- duration_months: how long the money stays invested, in months. 1 year = 12 months, "two years" = 24. null if not stated.
- A remark like "may withdraw after 1 year" is NOT the duration.
- If the user gives a range or several options (e.g. "5 or 6 lakh", "2-3 years"), use null for that field.
- liquidity_need: HIGH if the user may need the money early or wants flexibility, otherwise null.
- NEVER guess amount or duration. Use null when the user did not say it."""


class LLMRequirements(BaseModel):
    """The fields Gemini is allowed to fill."""

    category: Literal["FD", "LOAN", "CREDIT_CARD", "SAVINGS", "OTHER"] | None = None
    amount: float | None = None
    duration_months: int | None = None
    liquidity_need: Literal["HIGH", "MEDIUM", "LOW"] | None = None


class Requirements(LLMRequirements):
    missing: list[str] = Field(default_factory=list)


def validate(req: Requirements) -> Requirements:
    """Plain-Python safety net. Never trust the model's own idea of what is missing."""
    if req.amount is not None and req.amount <= 0:
        req.amount = None
    if req.duration_months is not None and req.duration_months <= 0:
        req.duration_months = None
    if req.category in (None, "FD"):
        req.missing = [
            f for f in ("amount", "duration_months") if getattr(req, f) is None
        ]
    else:
        req.missing = []  # only FDs need amount and duration in this MVP
    return req


_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "").upper() == "TRUE":
            _client = genai.Client(
                vertexai=True,
                project=GOOGLE_CLOUD_PROJECT,
                location=GOOGLE_CLOUD_LOCATION,
            )
        elif os.getenv("GOOGLE_API_KEY"):
            _client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
        else:
            raise RuntimeError(
                "No Gemini credentials: set Vertex env vars or GOOGLE_API_KEY."
            )
    return _client


def extract(text: str) -> Requirements:
    response = _get_client().models.generate_content(
        model=GEMINI_MODEL,
        contents=text,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=LLMRequirements,
            temperature=0,
        ),
    )
    parsed = LLMRequirements.model_validate_json(response.text)
    return validate(Requirements(**parsed.model_dump()))


if __name__ == "__main__":
    import sys

    print(
        extract(
            " ".join(sys.argv[1:]) or "I have 5 lakh for 2 years, may need it early"
        )
    )
