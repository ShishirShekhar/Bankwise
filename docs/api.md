# API documentation

The API is FastAPI, mounted under `/api`. Interactive OpenAPI/Swagger endpoints are disabled. JSON errors use FastAPI's `detail` shape; unexpected errors return a sanitized message and `request_id`. Business routes require a valid Bankwise session. Mutating routes also require `X-CSRF-Token` from `GET /api/auth/csrf` and an allowed `Origin`.

## Authentication routes

| Method and path | Access | Behavior |
|---|---|---|
| `GET /api/health` | Public | Liveness only; `{ "status": "healthy" }` |
| `GET /api/auth/csrf` | Public | Issues signed CSRF token |
| `POST /api/auth/session` | Public bootstrap | Accepts Firebase ID token, verifies recent auth, sets HTTP-only session cookie |
| `GET /api/auth/me` | Session | Returns safe session identity |
| `POST /api/auth/logout` | Session + CSRF | Clears session cookie |

## Product and decision routes

| Method and path | Request | Behavior |
|---|---|---|
| `GET /api/products?category=FD&amount=500000&tenureMonths=24` | Query params | Returns active products with sourced rates, eligibility, conditions, conflicts and verification details. Amount/tenure are optional. |
| `GET /api/products/{product_id}` | Path | One product payload or 404 |
| `GET /api/products/{product_id}/sources` | Path | Source metadata for one product |
| `POST /api/ask` | `{ "query": "I have ₹5 lakh for 2 years and may need it early" }` | Redacts and parses, compares products, returns tradeoffs/explanation and persists owner-scoped session. Per-user process-local rate limit defaults to 10 per 60 seconds. |
| `POST /api/compare` | `{ "product_ids": ["..."], "requirements": {"amount":500000,"duration_months":24} }` | Deterministic comparison. Amount and duration are required. |
| `POST /api/calculations/fd` | `{ "product_id":"...", "principal":500000,"tenure_months":24 }` | Calculates only using the product's unique eligible, verified cumulative rate band. |
| `GET /api/sessions/{session_id}` | Path | Retrieves sanitized session for its owner; otherwise 404. |

Calculation route failures: 404 for missing product, 409 for blocked/unverified or conflicted rate, 422 for invalid or unsupported calculation. Success returns principal, rate, tenure, compounding frequency, interest, maturity, currency, `calculation_version`, and warnings.

## Verification routes

| Method and path | Behavior |
|---|---|
| `POST /api/verification/run` | Rechecks stored sources, rate/condition provenance, freshness, effective dates and conflicts; returns record statuses. It does not fetch the web. |
| `GET /api/conflicts?status=OPEN` | Lists conflicts and both observations; `status` can be `OPEN` or `RESOLVED`. |
| `GET /api/agent/health` | Reports environment and optional integration configuration. |

## Decision response

`POST /api/ask` returns `request_id`, `session_id`, parsed `requirements`, product payloads, per-product comparisons/calculations/tradeoffs, source list, warnings, `clarification_needed`, session persistence indicator and AI usage metadata. When amount or duration is absent it returns a clarification status and no fabricated comparison. If no verified rate is usable, products are excluded or blocked with reasons. The response's trade-off metrics and numbers are computed by the API; model prose does not replace them.

For exact fields, see Pydantic request models in [`backend/app/schemas.py`](../backend/app/schemas.py) and payload construction in `backend/app/ai/ask_response.py` and `backend/app/domain/catalog.py`.
