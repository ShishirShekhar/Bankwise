# Bankwise

Bankwise is a fixed deposit (FD) comparison and decision-support application. It parses a user's stated amount and duration, uses only eligible source-verified catalogue data, calculates maturity deterministically, and explains gains and give-ups between available products.

## Start here

- [Codebase walkthrough](docs/codebase-walkthrough.md): local setup explained and end-to-end request flow.
- [Repository reference](docs/repository-reference.md): map of every tracked source, test, script, and configuration file.
- [Product specification](docs/product-specification.md): user problem, scope, and product behavior.
- [Architecture](docs/architecture.md): frontend, API, repositories, and request flow.
- [Data model](docs/data-model.md): catalogue records and provenance relationships.
- [API documentation](docs/api.md): routes, authentication, request and response behavior.
- [AI and agent architecture](docs/ai-agent-architecture.md): six-stage request workflow, RAG, Search grounding, and trust boundaries.
- [Financial calculations](docs/financial-calculations.md): supported formula and limitations.
- [Verification system](docs/verification-system.md): source status, conflicts, and usability rules.
- [Deployment instructions](docs/deployment.md): local run and current release workflow.

## Run locally

Requirements: Python 3.11+ and Node.js compatible with the version in the frontend lockfile (Node 20+ recommended).

In terminal 1, start the API:

```sh
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8080
```

In terminal 2, create the frontend environment file, fill in the Firebase web values from your Firebase project, then start the UI:

```sh
cd frontend
npm ci
cp .env.example .env.local
npm run dev
```

Set the Firebase values in `frontend/.env.local` before running `npm run dev` if you want to use browser sign-in.

On the deployed Bankwise demo, sign in with **test@test.com** and password **test123**. These credentials work only with the Firebase project provisioned for the demo. Do not reuse this password for a personal account.

Visit <http://localhost:3000>. Local backend mode uses `backend/data/fd-products.json` and in-memory sessions; it does not need Google Cloud credentials. Authentication still needs a configured Firebase project to complete the sign-in flow. The API can be exercised directly with a local auth session/token setup; see [deployment and local configuration](docs/deployment.md).

The frontend expects `NEXT_PUBLIC_BANKWISE_API_URL=http://localhost:8080` for direct local API requests. The `.env.example` has this value. Do not commit `.env` or `.env.local`.

## Checks

```sh
cd backend
pip install -r requirements-dev.txt
python -m ruff check app tests
python -m pytest
```

```sh
cd frontend
npm ci
npm run lint
npm run typecheck
npm run build
```

## Current scope and trust boundary

Only fixed deposits are supported. `/api/ask` redacts sensitive input, deterministically extracts numeric requirements, retrieves evidence from the separate BigQuery RAG corpus, and invokes Vertex AI Google Search grounding when that corpus has no current verified match. Catalogue verification, calculations, and trade-offs remain deterministic; search results and RAG excerpts never become calculation rates. The controlled source-ingestion command stores bounded excerpts and pending candidate facts in `bankwise_rag` for review. See [AI and agent architecture](docs/ai-agent-architecture.md) for execution order and limits.

Only current, conflict-free `HIGH` rates can be used to calculate maturity. If no usable rate or its required compounding convention exists, the API withholds the amount and gives a reason. Generic compound interest can differ from a bank's exact day-count and rounding rules; results carry a warning.

## Repository map

```text
backend/app/api/          HTTP routes, auth and request security
backend/app/domain/       parsing, source rules, catalogue shaping, comparison
backend/app/calculators/  deterministic financial formulas
backend/app/repositories/ local JSON, BigQuery, memory and Firestore adapters
backend/data/             local catalogue seed
backend/sql/              production BigQuery schema
backend/tests/             backend tests
frontend/app/              Next.js routes
frontend/components/       page and shared UI components
frontend/lib/               API client, auth, formatting, and view helpers
docs/                      product and engineering documentation
```

## Production at a glance

Production is configured for BigQuery catalogue data, Firestore decision sessions, Firebase Authentication/Hosting, and Cloud Run. A published GitHub release triggers `.github/workflows/deploy-production.yaml`; CI runs first, then it deploys the API and static frontend. See [deployment instructions](docs/deployment.md) before changing production settings.

## Contributing

Keep business rules and calculations deterministic, attach provenance to financial facts, preserve conflicts instead of choosing silently, and update the relevant docs when behavior changes. See [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md).
