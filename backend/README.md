# Bankwise Python backend

FastAPI backend for source-grounded FD comparison. Financial calculations live in `app/calculators`, separate from Gemini and ADK. BigQuery is the catalogue and verification data store. Firestore stores redacted decision-session state; it does not store the raw user query.

## Code layout

- `app/main.py` creates the FastAPI application and registers route modules.
- `app/api/` contains routers grouped by assistant, catalog/calculation, decision/session, and operational endpoints. Shared repository providers are in `api/dependencies.py`.
- `app/domain/` contains requirement parsing, source verification, product shaping, comparison, and ID generation. It does not define HTTP routes.
- `app/calculators/` contains deterministic financial calculations.
- `app/ai/` contains Gemini extraction, the conversational pipeline, and AI tool operations.
- `app/repositories/` contains BigQuery and Firestore access.

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
- `GET /api/sessions/{session_id}` (retrieves the sanitized state saved in Firestore)

Gemini requirement extraction uses Vertex AI when `GOOGLE_CLOUD_PROJECT` is configured and explicit fallback parsing otherwise. The decision endpoint invokes a Google ADK `Runner`; its orchestrator has tools for requirement extraction, product search, source verification, and product-backed deterministic calculation. It also receives a request-scoped tool containing the API's verified comparison result before writing the explanation. If Google credentials/project configuration is missing, the API still returns its structured deterministic result and reports `ai.status` as `not_configured`. Check `/api/agent/health` for configuration status. For local Vertex AI calls, configure ADC credentials, set the project/location in `.env`, and enable Vertex AI in that project.

RAG, Cloud Storage ingestion, automated external source fetching, and a curated-data write/import pipeline are not enabled yet. BigQuery access requires permission to create query jobs and read the configured dataset (typically BigQuery Job User plus dataset Data Viewer). Firestore access requires permission to read/write documents (typically Firestore User).

## Data and trust rules

`everything.md` requires official source URLs, retrieval/verification timestamps, effective dates, confidence, and conflict visibility. No bank rate seed values are included because no official source records were supplied. Open conflicts block calculations. Generic compound interest is labeled with a warning and should be replaced with documented bank-specific conventions when those are known.

### Source metadata

Every source returned by the API (`/api/products/{id}` and `/api/products/{id}/sources`) and by the ADK verification tool includes its URL, type, title, reference, `retrieved_at`, `verified_at`, effective dates, `confidence`, and `verification_status`. Rules live in `app/domain/sources.py`:

- `confidence` is the authority of the source type alone: `HIGH` for official bank pages/PDFs, `MEDIUM` otherwise.
- `verification_status` (also returned as `freshness` for existing clients) is the confidence downgraded to `LOW` when the source is inactive, has no retrieval/verification date, or is older than `SOURCE_MAX_AGE_DAYS`.
- Rates and conditions carry a `source_id`. A rate is usable for calculation and a condition is `verified` only when its linked source is `HIGH`; conditions also return `unverified_reason`.

The local dataset records only `last_verified`, so `retrieved_at` is set to that same date (a source must be retrieved to be verified). Sources the dataset marks `verify_before_production` are inactive and therefore `LOW`.

## Container

```sh
docker build -t bankwise-api .
docker run -p 8080:8080 -e PORT=8080 --env-file .env bankwise-api
```
