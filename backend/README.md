# Bankwise API

FastAPI service for source-grounded FD comparison. The root [README](../README.md) has the project overview and local quick start. Detailed behavior is documented in:

- [Architecture](../docs/architecture.md)
- [API routes and contracts](../docs/api.md)
- [Data model](../docs/data-model.md)
- [Financial calculations](../docs/financial-calculations.md)
- [Verification and conflicts](../docs/verification-system.md)
- [AI and research workflow](../docs/ai-agent-architecture.md)
- [Deployment](../docs/deployment.md)

## Backend commands

From this directory, create/activate a virtual environment, install dependencies, copy `.env.example` to `.env`, and run:

```sh
uvicorn app.main:app --reload --port 8080
```

Run checks from this directory:

```sh
pip install -r requirements-dev.txt
python -m ruff check app tests
python -m pytest
```

Local mode is the default (`ENVIRONMENT=local`): it reads `data/fd-products.json` and stores sessions in memory without Google Cloud calls. Production selects BigQuery and Firestore. `/api/ask` runs deterministic requirement, verification, calculation, and explanation stages; it reads current verified RAG evidence and invokes Google Search grounding when RAG returns no eligible chunks. Research evidence is isolated from the canonical catalogue. An explicit, bounded source ingestion command stores excerpts and pending candidates; it never promotes rate records.

Production BigQuery schema and import commands are described in [deployment](../docs/deployment.md). Calculation evaluation fixtures live in `evals/fd_calculation/`; regular tests validate them without calling Gemini. An optional live Gemini evaluation can be run with Vertex AI credentials:

Initialize both BigQuery datasets with `python -m scripts.create_bigquery_dataset`. Run a one-source ingestion only for an explicitly allow-listed public domain with `python -m scripts.ingest_public_source URL --allowed-domain bank.example`.

```sh
RUN_AGENT_EVALS=1 GOOGLE_CLOUD_PROJECT=your-project python -m pytest tests/test_fd_calculation_tool.py -k eval_with_gemini
```
