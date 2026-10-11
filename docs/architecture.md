# Architecture

## System shape

```text
Browser (Next.js static export)
  ├─ Firebase Web Authentication
  └─ /api requests ──> FastAPI (local process or Cloud Run)
                         ├─ domain parsing / verification / comparison
                         ├─ deterministic FD calculator
                         ├─ local JSON catalogue OR BigQuery
                         └─ memory sessions OR Firestore
```

The frontend is a static-export Next.js application. It does not host server-side business logic. In production Firebase Hosting serves `frontend/out` and rewrites `/api/**` to Cloud Run. During local development the browser calls the API origin directly.

## Backend layers

- `app/main.py`: middleware, CORS, sanitized error handling and router registration.
- `app/api/`: HTTP contracts, auth/session checks and CSRF protection.
- `app/domain/`: input parsing/redaction, typed bank/product models, source verification, conflict logic, payload shaping and comparisons.
- `app/calculators/`: deterministic calculation functions, independent of Gemini.
- `app/repositories/`: storage adapters. `api/dependencies.py` chooses adapters by `ENVIRONMENT`.
- `app/ai/` and `app/tools.py`: optional model and ADK evaluation integrations. They are not used by the current `/api/ask` workflow.

## Request lifecycle

1. The frontend submits a query to authenticated `POST /api/ask` with a CSRF token.
2. The backend redacts sensitive strings before parsing or persistence, then deterministically extracts amount, duration and simple preferences.
3. Missing amount/duration creates a clarification response and a session with no raw query.
4. Otherwise the backend enumerates active FD products, matches amount/tenure bands, verifies source/freshness/conflict status, and calculates only usable rates.
5. Comparison derives gains and give-ups from calculator results and verified conditions. The API serializes the response and stores redacted decision state scoped to the authenticated user.
6. The frontend renders API-owned numbers, source links, warnings and explanations.

## Environment selection

`ENVIRONMENT=local` (also accepts `development`, normalized to `local`) selects `LocalJsonCatalog` and `MemorySessionRepository`. This is the default and works offline without Google Cloud. `ENVIRONMENT=production` selects BigQuery and Firestore and validates required cloud project/auth settings at startup. The container defaults to production. This switch is enforced in `app/api/dependencies.py`.

## Authentication and privacy

Firebase ID tokens are verified server-side and exchanged for a five-day HTTP-only session cookie. Business routes require the session; state-changing routes also require a signed CSRF token and allowed origin. Decision sessions include owner UID and are only returned to that owner. Raw queries are not included in persisted decision records or request logs. Sensitive input must pass through `redact_sensitive_input()`.

## Reliability boundary

`GET /api/health` is a liveness check and does not prove that BigQuery, Firestore, or Firebase are reachable. `/api/agent/health` reports configured optional integrations. Unexpected API errors return a generic message with a request ID; logs omit request bodies, query strings, credentials and exception messages.
