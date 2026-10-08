"""Request-scoped Google ADK orchestration for grounded decision explanations."""

from app.config import GEMINI_MODEL, GOOGLE_CLOUD_PROJECT

BASE_RULES = """Never invent rates, fees, penalties, eligibility rules, source dates, or financial outcomes.
Use tools for product facts and calculations. If amount or tenure is missing, ask a concise clarification.
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
    """Build the ADK orchestrator with a tool exposing only this request's checked data."""
    Agent = _agent_class()

    def get_verified_decision_context() -> dict:
        """Retrieve the verified products, deterministic calculations, and source statuses for this request."""
        return decision_context

    from app.tools import (
        extract_requirements_tool,
        search_products_tool,
        verify_product_tool,
    )

    requirement_agent = Agent(
        name="requirement_agent",
        model=GEMINI_MODEL,
        instruction="Extract the user's stated FD amount, duration, and preferences. Do not fill missing values. "
        + BASE_RULES,
        tools=[extract_requirements_tool],
    )
    research_agent = Agent(
        name="research_agent",
        model=GEMINI_MODEL,
        instruction="Search the structured FD catalogue for amount/tenure eligible options. Return product and source evidence; do not recommend. "
        + BASE_RULES,
        tools=[search_products_tool],
    )
    verification_agent = Agent(
        name="verification_agent",
        model=GEMINI_MODEL,
        instruction="Check source freshness and open conflicts for products found by research. Surface disagreements without resolving them. "
        + BASE_RULES,
        tools=[verify_product_tool],
    )
    calculation_agent = build_calculation_agent()
    explanation_agent = Agent(
        name="explanation_agent",
        model=GEMINI_MODEL,
        instruction=(
            "Explain outcomes and trade-offs using only the verified decision context. Do not add facts or make a black-box ranking. "
            "Structure your explanation into three clear sections:\n"
            "1. Executive Decision Summary: Tailored directly to the user's stated amount, tenure, and liquidity preference.\n"
            "2. The Key Trade-off ('What Am I Giving Up?'): Explicit comparison of the top alternatives showing what is gained vs sacrificed (e.g. maturity vs penalty/flexibility).\n"
            "3. Conditions & Transparency: Explicit notes on compounding frequency, premature withdrawal rules, and official verification dates.\n"
            + BASE_RULES
        ),
        tools=[get_verified_decision_context],
    )
    return Agent(
        name="bankwise_decision_agent",
        model=GEMINI_MODEL,
        instruction=(
            "Coordinate the requirement, research, verification, calculation, and explanation agents in that order. "
            "Do not skip verification before calculation. If critical requirements are missing, ask a clarification. "
            + BASE_RULES
        ),
        sub_agents=[
            requirement_agent,
            research_agent,
            verification_agent,
            calculation_agent,
            explanation_agent,
        ],
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
            "The API's deterministic comparison is available through the explanation agent context tool.\n"
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
        return "".join(response_text).strip() or None
    except (ImportError, RuntimeError, OSError, ValueError):
        # The structured API result remains usable if ADK/model access is unavailable.
        return None
