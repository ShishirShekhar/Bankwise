# AI and agent architecture

## What runs for users today

The current `/api/ask` path is deterministic. It calls `redact_sensitive_input()`, then invokes requirement parsing with `use_gemini=False`; amount and duration are extracted from the sanitized text using code. It reads the catalogue, verifies facts, calculates results, derives trade-offs, shapes a structured explanation and persists sanitized state. The response reports `ai.provider = "deterministic API"` and `status = "not_used"`.

There is no live agent selecting tools or generating decision prose in this path. This is a deliberate trust boundary: the data and financial outcomes are controlled by application code.

## Optional model and ADK code

- `app/domain/input.py` has an optional Vertex AI Gemini requirement-extraction branch. Numeric values are still overwritten by deterministic parsing, and the live workflow disables this branch.
- `app/ai/orchestrator.py` defines a root explanation agent over a completed decision context and a calculation agent restricted to `calculate_fd_tool`.
- `app/tools.py` exposes deterministic source verification and calculation functions for agent/evaluation integrations.
- `backend/evals/fd_calculation/` contains optional Gemini evaluation cases; CI validates fixtures against deterministic tools without requiring Gemini.

These modules are not equivalent to an enabled production agent. `/api/agent/health` only reports configuration and installed packages; it does not mean user requests are being sent to a model.

## If model generation is enabled later

Keep parsing constrained to explicit user statements. Redact sensitive content before any provider call. Supply only verified decision context to an explanation model. Require the three sections: (1) Executive Decision Summary, (2) The Key Trade-off (“What Am I Giving Up?”), and (3) Conditions & Transparency. Preserve API-generated gains/give-ups and amounts unchanged. A model may explain these values, but cannot supply financial facts, hide conflicts, or perform arithmetic. Add evaluation cases for missing, stale and conflicting data before rollout.
