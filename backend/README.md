# Bankwise Python backend

FastAPI backend for source-grounded FD comparison. Financial calculations and user-facing explanations are deterministic and separate from optional AI evaluation tools. BigQuery is the production catalogue and verification data store. Firestore stores redacted decision-session state; it does not store the raw user query.

## Code layout

- `app/main.py` creates the FastAPI application and registers route modules.
- `app/api/` contains routers grouped by assistant, catalog/calculation, session, and operational endpoints. Shared repository providers are in `api/dependencies.py`.
- `app/domain/` contains requirement parsing, source verification, product shaping, comparison, ID generation, and the validated `Bank`/`Product` models in `domain/models.py` (they mirror the `banks` and `products` tables; `from_row`/`to_row` convert to and from table rows). It does not define HTTP routes.
- `app/calculators/` contains deterministic financial calculations.
- `app/ai/` contains optional Gemini requirement extraction and evaluation tools. The user request path currently uses deterministic parsing and does not call Gemini.
- `app/repositories/` contains BigQuery and Firestore access plus the local JSON catalogue and in-memory sessions. Both catalogues expose `list_banks()` and `get_bank(id)` returning `Bank` models.

`app/services.py` re-exports domain functions for older imports. New code should import directly from the relevant `app.domain` module.

## Local setup

Requires Python 3.11 or newer. Offline local development uses the checked-in JSON catalogue and in-memory sessions without Google Cloud credentials. Firebase and Google Cloud credentials are needed only when exercising those integrations.

```sh
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Copy `.env.example` to `.env` for local development. For Google Cloud integration work, set `GOOGLE_CLOUD_PROJECT`, `BIGQUERY_PROJECT`, `BIGQUERY_DATASET`, `BIGQUERY_LOCATION`, and `FIRESTORE_PROJECT`, then authenticate with `gcloud auth application-default login`. Apply [the BigQuery schema](sql/bigquery_schema.sql) after replacing `YOUR_PROJECT` and the dataset location. The production catalogue should contain only manually reviewed bank/product/rate/source records; rates without current HIGH confidence source metadata cannot be used by decision or calculation APIs.

### Firebase Authentication

The frontend uses the Firebase Web SDK for email/password and Google popup sign-in with in-memory persistence. It sends the resulting Firebase ID token once to `POST /api/auth/session`; the backend verifies the token and recent `auth_time`, then sets a five-day HTTP-only session cookie. The cookie is named `bankwise_session` locally and `__session` in production so Firebase Hosting forwards it to Cloud Run. The frontend immediately signs out of the Web SDK. `GET /api/auth/me` reports the cookie-backed session. Business API routes require a verified cookie. `GET /api/health` is public liveness only; API docs are disabled. `GET /api/auth/csrf` and `POST /api/auth/session` are public so the browser can establish a session. Mutating requests require a signed, one-hour CSRF token from `GET /api/auth/csrf` in `X-CSRF-Token` and an allowed `Origin`; CSRF validation does not depend on a separate cookie because Firebase Hosting strips all cookies except `__session` on Cloud Run rewrites.

Set `ENVIRONMENT=local` for offline local JSON catalog and in-memory sessions. The container defaults to `ENVIRONMENT=production`; production startup requires Google Cloud, BigQuery, Firebase project IDs, a strong `CSRF_SECRET`, and deployed-only `CORS_ORIGINS`. Supply secrets through Secret Manager. Configure the frontend Firebase variables and keep `NEXT_PUBLIC_BANKWISE_API_URL` unset when `/api/**` is rewritten through Firebase Hosting. Firebase Hosting forwards only the `__session` cookie to Cloud Run. For a directly addressed cross-site API instead of a Hosting rewrite, set `AUTH_COOKIE_SAMESITE=none` and keep `AUTH_COOKIE_SECURE=true`.

Decision sessions include their Firebase UID as `user_id`; `/api/sessions/{session_id}` only returns a session to its owner.

Create the configured BigQuery dataset and its tables with `python -m scripts.create_bigquery_dataset` from `backend/`. The script reads project, dataset, and location from `.env`, then applies the idempotent DDL in `sql/bigquery_schema.sql`. It requires Google Cloud ADC credentials and permission to create datasets and tables.

## Endpoints

- `GET /api/health` (public liveness probe; does not verify dependencies)
- `GET /api/auth/csrf`, `POST /api/auth/session`, `GET /api/auth/me`, and `POST /api/auth/logout` manage the browser session.
- `GET /api/products?category=FD&amount=500000&tenureMonths=24`
- `GET /api/products/{id}` and `/api/products/{id}/sources`
- `POST /api/ask` with `{ "query": "I have ₹5 lakh for 2 years and may need it early" }`
- `POST /api/calculations/fd`
- `POST /api/compare`
- `POST /api/verification/run` (checks stored metadata; it does not crawl sources)
- `GET /api/conflicts?status=OPEN` (or `RESOLVED`) lists source conflicts with both values and sources
- `GET /api/sessions/{session_id}` (retrieves the sanitized state saved in Firestore)

`POST /api/ask` uses deterministic requirement parsing, source verification, calculation, comparison, and three-part explanation generation. It does not call Gemini on the user request path. The endpoint has a per-user, per-process request limit (`ASK_RATE_LIMIT`, default 10 per `ASK_RATE_WINDOW_SECONDS`, default 60 seconds); production must also apply a shared ingress rate limit such as Cloud Armor because Cloud Run can run multiple instances. `/api/agent/health` reports optional evaluation-tool configuration.

RAG, Cloud Storage ingestion, automated external source fetching, and a curated-data write/import pipeline are not enabled yet. BigQuery access requires permission to create query jobs and read the configured dataset (typically BigQuery Job User plus dataset Data Viewer). Firestore access requires permission to read/write documents (typically Firestore User).

## Data model

[`sql/bigquery_schema.sql`](sql/bigquery_schema.sql) defines the catalogue tables. Each table has an `id` primary key; relationships are declared as BigQuery `NOT ENFORCED` foreign keys, so application code must still validate references.

- `banks` → `products` (`bank_id`)
- `products` → `sources`, `product_rates`, `product_conditions`, `verification_records`, `source_conflicts` (`product_id`)
- `sources` → `product_rates`, `product_conditions`, `verification_records` (`source_id`) and `source_conflicts` (`source_a`, `source_b`)

Sources carry the URL, type, title, retrieval/verification timestamps, and effective dates for every financial fact. Rates and conditions carry a `verification_status`. Conflicts keep both observed values and their sources, with an `OPEN`/resolved status and resolution fields. `tests/test_bigquery_schema.py` checks these relationships and provenance columns.

## Data and trust rules

`everything.md` requires official source URLs, retrieval/verification timestamps, effective dates, confidence, and conflict visibility. No bank rate seed values are included because no official source records were supplied. Open conflicts block calculations. Generic compound interest is labeled with a warning and should be replaced with documented bank-specific conventions when those are known.

## FD calculation tool and agent evaluations

`app/domain/rates.py` selects a product's single eligible rate band and runs the deterministic calculator. The ADK `calculate_fd_tool`, `POST /api/calculations/fd`, and the comparison share it, so an evaluation agent cannot show an amount the comparison would refuse. The tool returns `status` `CALCULATED` with the calculator `result` unchanged (including `calculation_version`), or `INVALID_INPUT`, `MISSING`, `UNAVAILABLE`, `BLOCKED`, or `UNSUPPORTED` with a `reason` and no amount. The current user request path does not invoke ADK.

`evals/fd_calculation/` is an ADK evaluation set for the calculation tool: each case expects a `calculate_fd_tool` call with exact arguments and an answer whose numbers come from the calculator (one case asks the agent to "assume 9%", one is a blocked product). `tests/test_fd_calculation_tool.py` checks the eval file against the calculator in CI without calling Gemini. To run the eval against Gemini, configure Vertex AI credentials and run:

```sh
RUN_AGENT_EVALS=1 GOOGLE_CLOUD_PROJECT=your-project python -m pytest tests/test_fd_calculation_tool.py -k eval_with_gemini
```
### Source metadata

Every source returned by the API (`/api/products/{id}` and `/api/products/{id}/sources`) and by the ADK verification tool includes its URL, type, title, reference, `retrieved_at`, `verified_at`, effective dates, `confidence`, and `verification_status`. Rules live in `app/domain/sources.py`:

- `confidence` is the authority of the source type alone: `HIGH` for official bank pages/PDFs, `MEDIUM` otherwise.
- `verification_status` (also returned as `freshness` for existing clients) is the confidence downgraded to `LOW` when the source is inactive, has no retrieval/verification date, is older than `SOURCE_MAX_AGE_DAYS` (`stale: true`), or is outside its effective dates. The reasons are listed in `verification_issues`.
- Rates and conditions carry a `source_id` and get one verification status each, taking the worst result of every check:

| Status | Meaning |
|---|---|
| `HIGH` | Linked to a current official bank source with no open conflict; the only status usable as authoritative. |
| `MEDIUM` | Current source that is not an official bank source. |
| `LOW` | Stale, inactive, not-yet-effective or expired source or rate, or stored as unverified. |
| `CONFLICT` | An `OPEN` source conflict exists for the field (`rate`, or the condition type). |
| `MISSING` | No linked source, or the linked source does not exist. |

Rates return `verification_reason` and `usable_for_calculation`; conditions return `verified` and `unverified_reason`. Comparison and calculation only use `HIGH` rates. `POST /api/verification/run` reports the status of every rate, condition, and source.

### Source conflicts

`app/domain/conflicts.py` compares every source's value for the same fact and never picks one silently. The local catalogue records each data row's rate (keyed by tenure band) and conditions as observations; if two observations for the same product, field, and band disagree after normalization (numbers rounded, text trimmed and case-folded), an `OPEN` conflict stores both values, both sources, and `detected_at`.

- An open rate conflict makes that band `CONFLICT` and blocks it from calculations; other bands stay usable. Conflicts recorded by hand in `source_conflicts` (without a band) block every rate of the field. An open condition conflict makes conditions of that type `CONFLICT`.
- Conflicts appear in product payloads, the ADK verification tool, and `GET /api/conflicts`.
- A person resolves a conflict by adding an entry to `conflict_resolutions` in the data file with `bank_name`, `product_name`, `field_name`, `key` (the band, e.g. `"24-35"`, or omitted for product-wide terms), `resolved_value`, `resolution_notes`, and optionally `resolved_at`. The resolved value must be one of the two observed values and notes are required; otherwise the conflict stays `OPEN`. A resolved conflict is kept with status `RESOLVED`, and the confirmed value is used.

The local dataset records only `last_verified`, so `retrieved_at` is set to that same date (a source must be retrieved to be verified). Sources the dataset marks `verify_before_production` are inactive and therefore `LOW`.

## Container

```sh
docker build -t bankwise-api .
docker run -p 8080:8080 -e PORT=8080 -e ENVIRONMENT=local --env-file .env bankwise-api
```
