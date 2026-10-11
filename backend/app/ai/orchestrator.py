"""Request-scoped Google ADK explanation agent over verified decision context."""

import json
import re
from decimal import Decimal, InvalidOperation

from google.api_core.exceptions import GoogleAPIError
from google.auth.exceptions import GoogleAuthError
from google.genai.errors import APIError

from app.config import GEMINI_MODEL, GOOGLE_CLOUD_PROJECT

BASE_RULES = """Never invent rates, fees, penalties, eligibility rules, source dates, or financial outcomes.
Use only the request's verified decision context for product facts and calculations.
Only cite URLs listed under verified_sources. Never treat pending research citations as verification.
Explicitly surface CONFLICT and stale sources. Never request PAN, Aadhaar, account/card numbers, CVV,
UPI credentials, or banking passwords."""

CALCULATION_INSTRUCTION = (
    "Calculate FD outcomes only by calling calculate_fd_tool with the product_id, principal in rupees, "
    "and tenure in months. Never perform arithmetic yourself. Report maturity_amount, interest_earned, "
    "and calculation_version exactly as the tool returns them. If the tool status is not CALCULATED, "
    "explain its reason and give no amount. "
)


def _agent_class():
    try:
        from google.adk.agents import Agent
    except ImportError as exc:
        raise RuntimeError("Install backend requirements to use Google ADK") from exc
    return Agent


def build_calculation_agent():
    """Calculation specialist: every amount comes from the deterministic FD tool."""
    from app.tools import calculate_fd_tool

    return _agent_class()(
        name="calculation_agent",
        model=GEMINI_MODEL,
        instruction=CALCULATION_INSTRUCTION + BASE_RULES,
        tools=[calculate_fd_tool],
    )


def build_root_agent(decision_context: dict):
    """Build an explanation agent over the API's checked, deterministic result."""
    Agent = _agent_class()

    def get_verified_decision_context() -> dict:
        """Retrieve the verified products, deterministic calculations, and source statuses for this request."""
        return decision_context

    return Agent(
        name="bankwise_decision_agent",
        model=GEMINI_MODEL,
        instruction=(
            "Explain the API's completed deterministic comparison. Do not re-extract requirements, search products, "
            "verify sources, recalculate values, or alter trade-off metrics. Structure the explanation in three sections: "
            "Executive Decision Summary; The Key Trade-off ('What Am I Giving Up?'); Conditions & Transparency, "
            "covering compounding, premature withdrawal terms, and source verification dates. "
            + BASE_RULES
        ),
        tools=[get_verified_decision_context],
    )


async def run_decision_agent(query: str, requirements: dict, decision_context: dict):
    """Run the ADK agent. Returns grounded explanation text, or None when not configured."""
    if not GOOGLE_CLOUD_PROJECT:
        return None
    try:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types

        app_name = "bankwise"
        user_id = "decision-api"
        session_service = InMemorySessionService()
        runner = Runner(
            agent=build_root_agent(decision_context),
            app_name=app_name,
            session_service=session_service,
        )
        session = await session_service.create_session(
            app_name=app_name, user_id=user_id
        )
        prompt = (
            f"User request: {query}\n"
            f"Requirements parsed by the API: {requirements}\n"
            "The API's deterministic comparison is available through the verified decision context tool.\n"
            "Produce a structured 3-part explanation with:\n"
            "1. Executive Decision Summary\n"
            "2. The Key Trade-off ('What Am I Giving Up?')\n"
            "3. Conditions & Transparency\n"
            "Never invent numbers or dates. Rely solely on the verified tool context."
        )
        message = types.Content(role="user", parts=[types.Part(text=prompt)])
        response_text = []
        async for event in runner.run_async(
            user_id=user_id, session_id=session.id, new_message=message
        ):
            if event.is_final_response() and event.content and event.content.parts:
                response_text.extend(
                    part.text for part in event.content.parts if part.text
                )
        explanation = "".join(response_text).strip()
        return explanation if _is_grounded_explanation(explanation, decision_context) else None
    except (ImportError, RuntimeError, OSError, ValueError, GoogleAPIError, GoogleAuthError, APIError):
        # The structured API result remains usable if ADK/model access is unavailable.
        return None


def _is_grounded_explanation(explanation: str, context: dict) -> bool:
    """Reject model prose that drops required sections, adds numbers, or invents URLs."""
    required = ("Executive Decision Summary", "The Key Trade-off", "Conditions & Transparency")
    if not explanation or not all(item.lower() in explanation.lower() for item in required):
        return False
    context_text = json.dumps(context, default=str)
    number_pattern = re.compile(r"(?<![\w])(?:\d{1,3}(?:,\d{2,3})+|\d+(?:\.\d+)?)(?![\w])")
    allowed = set()
    for match in number_pattern.finditer(context_text):
        try:
            allowed.add(Decimal(match.group().replace(",", "")))
        except InvalidOperation:
            continue
    for match in number_pattern.finditer(explanation):
        try:
            value = Decimal(match.group().replace(",", ""))
        except InvalidOperation:
            return False
        if value not in allowed and value not in {Decimal(1), Decimal(2), Decimal(3)}:
            return False
    clean_url = lambda url: url.rstrip(".,;]'\"}")
    allowed_urls = {clean_url(url) for url in re.findall(r"https?://[^\s)]+", context_text)}
    cited_urls = {clean_url(url) for url in re.findall(r"https?://[^\s)]+", explanation)}
    return cited_urls.issubset(allowed_urls)
