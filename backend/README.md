# Bankwise Python backend

FastAPI backend for source-grounded FD comparison. Financial calculations live in `app/calculators`, separate from Gemini and ADK. BigQuery is the catalogue and verification data store. Firestore stores redacted decision-session state; it does not store the raw user query.

## Code layout

- `app/main.py` creates the FastAPI application and registers route modules.
- `app/api/` contains routers grouped by assistant, catalog/calculation, decision/session, and operational endpoints. Shared repository providers are in `api/dependencies.py`.
- `app/domain/` contains requirement parsing, source verification, product shaping, comparison, ID generation, and the validated `Bank`/`Product` models in `domain/models.py` (they mirror the `banks` and `products` tables; `from_row`/`to_row` convert to and from table rows). It does not define HTTP routes.
- `app/calculators/` contains deterministic financial calculations.
- `app/ai/` contains Gemini extraction, the conversational pipeline, and AI tool operations.
- `app/repositories/` contains BigQuery and Firestore access plus the local JSON catalogue and in-memory sessions. Both catalogues expose `list_banks()` and `get_bank(id)` returning `Bank` models.

`app/services.py` re-exports domain functions for older imports. New code should import directly from the relevant `app.domain` module.

## Local setup

Requires Python 3.11 or newer, Google Cloud ADC credentials, and configured BigQuery/Firestore resources.

```sh
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open `/docs` for the API schema. Copy `.env.example` to `.env` and set `GOOGLE_CLOUD_PROJECT`, `BIGQUERY_PROJECT`, `BIGQUERY_DATASET`, `BIGQUERY_LOCATION`, and `FIRESTORE_PROJECT`. Authenticate locally with `gcloud auth application-default login`. Apply [the BigQuery schema](sql/bigquery_schema.sql) after replacing `YOUR_PROJECT` and the dataset location. The catalogue intentionally starts empty. Add bank/product/rate/source records only after manual verification against official bank sources; rates without current HIGH confidence source metadata cannot be used by decision or calculation APIs.

## Endpoints

- `GET /api/health`
- `GET /api/products?category=FD&amount=500000&tenureMonths=24`
- `GET /api/products/{id}` and `/api/products/{id}/sources`
- `POST /api/decision` with `{ "query": "I have ₹5 lakh for 2 years and may need it early" }`
- `POST /api/calculations/fd`
- `POST /api/compare`
- `POST /api/verification/run` (checks stored metadata; it does not crawl sources)
- `GET /api/conflicts?status=OPEN` (or `RESOLVED`) lists source conflicts with both values and sources
- `GET /api/sessions/{session_id}` (retrieves the sanitized state saved in Firestore)

Gemini requirement extraction uses Vertex AI when `GOOGLE_CLOUD_PROJECT` is configured and explicit fallback parsing otherwise. The decision endpoint invokes a Google ADK `Runner`; its orchestrator has tools for requirement extraction, product search, source verification, and product-backed deterministic calculation. It also receives a request-scoped tool containing the API's verified comparison result before writing the explanation. If Google credentials/project configuration is missing, the API still returns its structured deterministic result and reports `ai.status` as `not_configured`. Check `/api/agent/health` for configuration status. For local Vertex AI calls, configure ADC credentials, set the project/location in `.env`, and enable Vertex AI in that project.

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

`app/domain/rates.py` selects a product's single eligible rate band and runs the deterministic calculator. The ADK `calculate_fd_tool`, `POST /api/calculations/fd`, and the comparison all use it, so the agent can never show an amount the comparison would refuse. The tool returns `status` `CALCULATED` with the calculator `result` unchanged (including `calculation_version`), or `INVALID_INPUT`, `MISSING`, `UNAVAILABLE`, `BLOCKED`, or `UNSUPPORTED` with a `reason` and no amount.

`evals/fd_calculation/` is an ADK evaluation set for the production calculation agent: each case expects a `calculate_fd_tool` call with exact arguments and an answer whose numbers come from the calculator (one case asks the agent to "assume 9%", one is a blocked product). `tests/test_fd_calculation_tool.py` checks the eval file against the calculator in CI without calling Gemini. To run the eval against Gemini, configure Vertex AI credentials and run:

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
docker run -p 8080:8080 -e PORT=8080 --env-file .env bankwise-api
```
