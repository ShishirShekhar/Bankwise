# Deployment instructions

## Local development

Use Python 3.11+ and Node.js 20+ (the project pins frontend dependencies in `package-lock.json`). Backend offline mode uses the bundled JSON catalogue and memory sessions.

```sh
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8080
```

In another terminal:

```sh
cd frontend
npm ci
cp .env.example .env.local
# Set Firebase web app values in .env.local
npm run dev
```

The frontend `.env.example` points API calls to `http://localhost:8080`. A working Firebase project is needed for browser sign-in. For Google Cloud integrations locally, configure the cloud values in `backend/.env` and use Application Default Credentials (`gcloud auth application-default login`).

## Local data and BigQuery setup

Inspect or preview local catalogue content in `backend/data/fd-products.json`. To configure production storage, set `ENVIRONMENT=production`, `GOOGLE_CLOUD_PROJECT`, BigQuery dataset/location, Firestore project/database, Firebase project, a 32+ character `CSRF_SECRET`, and deployed-only `CORS_ORIGINS`. Authenticate with ADC for manual setup. From `backend/`:

```sh
python -m scripts.create_bigquery_dataset
```

This creates canonical `bankwise` and separate `bankwise_rag` datasets and applies the idempotent schema from `sql/bigquery_schema.sql`. Preview catalogue import with `ENVIRONMENT=local python -m scripts.import_fd_products`; apply with `ENVIRONMENT=local python -m scripts.import_fd_products --apply`. The importer upserts and does not delete. Review source conflicts and data before production use. See [AI and agent architecture](ai-agent-architecture.md) for corpus ingestion and promotion boundaries.

## Production platform

- Frontend: Next.js static export (`frontend/out`) hosted by Firebase Hosting.
- API: Docker image from `backend/Dockerfile` deployed to Cloud Run.
- Catalogue: BigQuery dataset `bankwise`.
- Decision sessions: Firestore.
- Identity: Firebase Authentication; Firebase Hosting rewrites `/api/**` to the `bankwise-api` Cloud Run service.
- Secrets: `CSRF_SECRET` is supplied through Google Secret Manager by the release workflow.

`.github/config/production.yaml` contains non-secret project, region, service and runtime settings. The workflow also needs GitHub Actions variable `GCP_WORKLOAD_IDENTITY_PROVIDER`; Firebase web API key and app ID are configured as GitHub variables/environment values. Configure Firebase Email/Password and Google providers and authorized domains. Enable BigQuery and Vertex AI APIs. Cloud Run runtime identity needs BigQuery Job User, BigQuery Data Viewer on `bankwise` and `bankwise_rag`, Vertex AI User for embeddings/Search grounding, and Firestore access. The explicit ingestion script additionally needs BigQuery Data Editor on `bankwise_rag`; grant that to a separate operator identity where possible. BigQuery query/storage and Vertex AI/Search grounding are billed services. No vector index is required at initial scale.

## Release deployment

`.github/workflows/deploy-production.yaml` runs on a **published GitHub release**. It loads production config, runs backend and frontend CI, builds/pushes the API image, deploys Cloud Run, builds the static frontend with the API URL, then deploys Firebase Hosting. Before publishing, check workflow status and production data/config. The workflow is the supported production deployment path; do not substitute a Vercel deployment without updating the architecture and auth/API configuration.

## CI and local checks

Backend CI runs Ruff and pytest. Frontend CI runs ESLint and TypeScript checks; production deployment performs the static build. Run the commands in the root README before a release. GitHub branch protection must require the CI status checks if they are expected to block merges.

## Troubleshooting

- `ENVIRONMENT=production` startup fails: verify project IDs, secure CSRF secret, deployed CORS origins and required cloud configuration.
- Login succeeds but requests return 401: verify Firebase project alignment, backend Firebase Admin credentials, cookie forwarding, and frontend/API origin settings.
- Mutations return 403: fetch a fresh `/api/auth/csrf` token and send it with the allowed `Origin`.
- Products show unavailable or blocked: inspect `/api/verification/run`, `/api/conflicts`, source effective dates and the exact matching rate band.
- Health is green but API calls fail: `/api/health` checks process liveness only; inspect Cloud Run logs using the response `X-Request-ID`.
