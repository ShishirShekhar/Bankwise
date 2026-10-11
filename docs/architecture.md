# Architecture

## System shape

```text
Browser (Next.js static export)
  ├─ Firebase Web Authentication
  └─ /api requests ──> FastAPI (local process or Cloud Run)
                         ├─ domain parsing / verification / comparison
                         ├─ deterministic FD calculator
                         ├─ local JSON catalogue OR BigQuery
                         ├─ BigQuery RAG corpus + Vertex AI Search grounding
                         └─ memory sessions OR Firestore
```

The frontend is a static-export Next.js application. It does not host server-side business logic. In production Firebase Hosting serves `frontend/out` and rewrites `/api/**` to Cloud Run. During local development the browser calls the API origin directly.

## Backend layers

- `app/main.py`: middleware, CORS, sanitized error handling and router registration.
- `app/api/`: HTTP contracts, auth/session checks and CSRF protection.
- `app/domain/`: input parsing/redaction, typed bank/product models, source verification, conflict logic, payload shaping and comparisons.
- `app/calculators/`: deterministic calculation functions, independent of Gemini.
- `app/repositories/`: storage adapters. `api/dependencies.py` chooses adapters by `ENVIRONMENT`.
- `app/ai/` and `app/tools.py`: six-stage request workflow, Google Search grounding, optional ADK explanation, and deterministic tools.

## Request lifecycle

1. The frontend submits a query to authenticated `POST /api/ask` with a CSRF token.
2. The backend redacts sensitive strings before parsing, retrieval, Search grounding, or persistence, then deterministically extracts amount, duration and simple preferences.
3. Missing amount/duration creates a clarification response and a session with no raw query.
4. Otherwise it checks canonical products, searches current verified BigQuery RAG chunks, and uses Vertex AI Google Search grounding only when internal evidence is insufficient.
5. The backend verifies canonical source/freshness/conflict status and calculates only usable catalogue rates. Retrieved evidence cannot enter calculation inputs.
6. Comparison derives gains and give-ups from calculator results and verified conditions. The API serializes the response and stores redacted decision state scoped to the authenticated user.
7. The frontend renders deterministic numbers, source links, warnings, and a research-evidence panel that labels retrieved sources as non-calculation evidence.

## Environment selection

`ENVIRONMENT=local` (also accepts `development`, normalized to `local`) selects `LocalJsonCatalog` and `MemorySessionRepository`. This is the default and works offline without Google Cloud. `ENVIRONMENT=production` selects BigQuery and Firestore and validates required cloud project/auth settings at startup. The container defaults to production. This switch is enforced in `app/api/dependencies.py`.

Production adds a separately configured `RAG_DATASET` (default `bankwise_rag`) alongside the canonical `bankwise` catalogue. Google embeddings and Search grounding require Vertex AI access; Search uses the global location. See [AI and agent architecture](ai-agent-architecture.md) for setup and promotion constraints.

## Authentication and privacy

Firebase ID tokens are verified server-side and exchanged for a five-day HTTP-only session cookie. Business routes require the session; state-changing routes also require a signed CSRF token and allowed origin. Decision sessions include owner UID and are only returned to that owner. Raw queries are not included in persisted decision records or request logs. Sensitive input must pass through `redact_sensitive_input()`.

## Reliability boundary

`GET /api/health` is a liveness check and does not prove that BigQuery, Firestore, or Firebase are reachable. `/api/agent/health` reports configured optional integrations. Unexpected API errors return a generic message with a request ID; logs omit request bodies, query strings, credentials and exception messages.
