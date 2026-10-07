"""The production calculation agent, exposed as ``root_agent`` for ADK evaluation."""

from app.ai.orchestrator import build_calculation_agent

root_agent = build_calculation_agent()
