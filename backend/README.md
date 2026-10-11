# Bankwise API

FastAPI service for source-grounded FD comparison. The root [README](../README.md) has the project overview and local quick start. Detailed behavior is documented in:

- [Architecture](../docs/architecture.md)
- [API routes and contracts](../docs/api.md)
- [Data model](../docs/data-model.md)
- [Financial calculations](../docs/financial-calculations.md)
- [Verification and conflicts](../docs/verification-system.md)
- [AI and optional agent code](../docs/ai-agent-architecture.md)
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

Local mode is the default (`ENVIRONMENT=local`): it reads `data/fd-products.json` and stores sessions in memory. Production selects BigQuery and Firestore and requires cloud configuration. The user-facing `/api/ask` path is deterministic and does not invoke Gemini or ADK. No source-crawling process is enabled.

Production BigQuery schema and import commands are described in [deployment](../docs/deployment.md). Calculation evaluation fixtures live in `evals/fd_calculation/`; regular tests validate them without calling Gemini. An optional live Gemini evaluation can be run with Vertex AI credentials:

```sh
RUN_AGENT_EVALS=1 GOOGLE_CLOUD_PROJECT=your-project python -m pytest tests/test_fd_calculation_tool.py -k eval_with_gemini
```
