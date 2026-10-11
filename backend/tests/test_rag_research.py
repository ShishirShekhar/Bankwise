import asyncio

import pytest

from app.ai import ingestion
from app.ai.orchestrator import _is_grounded_explanation
from app.ai.specialists import BankwiseAgentWorkflow, RequirementOutput
from app.repositories.rag import (
    BigQueryRagRepository,
    normalize_url,
    split_chunks,
    stable_id,
)


def test_chunking_and_ids_are_stable_and_bounded():
    chunks = split_chunks("one two three four five", 10, 2)
    assert chunks == split_chunks("one two three four five", 10, 2)
    assert all(len(chunk) <= 10 for chunk in chunks)
    assert stable_id("url", "hash") == stable_id("url", "hash")
    assert normalize_url("HTTPS://Bank.Example/rates#section") == "https://bank.example/rates"


def test_bigquery_ingestion_uses_parameterized_idempotent_merges(monkeypatch):
    class Job:
        def result(self):
            return []

    class Client:
        def __init__(self):
            self.calls = []

        def query(self, sql, **kwargs):
            self.calls.append((sql, kwargs))
            return Job()

    class Embedder:
        model = "gemini-embedding-001"

    monkeypatch.setattr("app.repositories.rag.BIGQUERY_PROJECT", "test-project")
    client = Client()
    repository = BigQueryRagRepository(client=client, dataset="bankwise_rag", embedder=Embedder())
    document = {"document_id": "d1", "canonical_url": "https://bank.example/fd",
                "title": "Rates", "domain": "bank.example", "document_type": "text/html",
                "retrieved_at": "2026-10-11T00:00:00Z", "content_hash": "hash-1"}
    chunk = {"chunk_id": "c1", "chunk_index": 0, "excerpt": "official excerpt",
             "embedding": [0.1, 0.2]}
    repository.upsert_document(document, [chunk])
    repository.upsert_document(document, [chunk])
    merges = [sql for sql, _kwargs in client.calls if sql.lstrip().startswith("MERGE")]
    assert len(merges) == 4
    assert all("official excerpt" not in sql for sql in merges)
    assert all("WHEN NOT MATCHED THEN INSERT" in sql for sql in merges)


def test_url_normalization_rejects_non_web_and_userinfo():
    with pytest.raises(ValueError):
        normalize_url("file:///etc/passwd")
    with pytest.raises(ValueError):
        normalize_url("https://user:pass@bank.example/rates")
    with pytest.raises(ValueError):
        normalize_url("https://bank.example/rates?api_key=private")


def test_ingestion_destination_blocks_private_addresses_and_unlisted_hosts(monkeypatch):
    monkeypatch.setattr(ingestion.socket, "getaddrinfo", lambda *_args: [(None, None, None, None, ("127.0.0.1", 443))])
    with pytest.raises(ValueError, match="non-public"):
        ingestion._public_destination("https://bank.example/rates", {"bank.example"})
    with pytest.raises(ValueError, match="not allow-listed"):
        ingestion._public_destination("https://other.example/rates", {"bank.example"})


def test_rag_runs_before_search_and_search_runs_when_rag_is_empty():
    events = []

    class Catalog:
        def list_products(self, category):
            events.append("catalog")
            return []

    class Rag:
        def retrieve(self, query):
            events.append("rag")
            return []

    class Search:
        def search(self, query):
            events.append("search")
            assert "123456789012" not in query
            return {"sources": [{"url": "https://bank.example/fd"}], "retrieved_at": "2026-01-01T00:00:00Z"}

    workflow = BankwiseAgentWorkflow(Catalog(), Rag(), Search())
    req = RequirementOutput(requirements={"amount": 10000, "duration_months": 12, "product_category": "FD"})
    result = asyncio.run(workflow.research("FD for 1 year; PAN 123456789012", req))
    assert events == ["catalog", "rag", "search"]
    assert result.rag_invoked and result.search_invoked
    assert result.search_sources[0]["url"] == "https://bank.example/fd"


def test_verified_rag_avoids_live_search():
    class Catalog:
        def list_products(self, category):
            return []

    class Rag:
        def retrieve(self, query):
            return [{"chunk_id": "chunk-1", "verification_status": "HIGH"}]

    class Search:
        def search(self, query):
            pytest.fail("search should not be needed for sufficient retrieved evidence")

    output = asyncio.run(BankwiseAgentWorkflow(Catalog(), Rag(), Search()).research(
        "FD rates", RequirementOutput(requirements={"product_category": "FD"})
    ))
    assert output.rag_invoked
    assert not output.search_invoked


def test_verified_canonical_rate_avoids_unnecessary_live_search():
    from datetime import UTC, datetime

    class Catalog:
        def list_products(self, category):
            return [{"id": "bank-fd", "rates": [{"id": "rate-1", "min_amount": 1,
                    "max_amount": None, "tenure_months": 12, "source_id": "source-1",
                    "verification_status": "HIGH", "effective_from": None, "effective_to": None}]}]

        def get_conflicts(self, product_id, field_name=None):
            return []

        def get_source(self, source_id):
            return {"id": source_id, "source_type": "OFFICIAL_BANK_RATE_CARD", "status": "ACTIVE",
                    "verified_at": datetime.now(UTC)}

    class Search:
        def search(self, query):
            pytest.fail("a current verified catalogue match is sufficient")

    output = asyncio.run(BankwiseAgentWorkflow(Catalog(), searcher=Search()).research(
        "FD rates", RequirementOutput(requirements={"product_category": "FD", "amount": 10000,
                                                    "duration_months": 12})
    ))
    assert output.canonical_evidence_sufficient
    assert not output.search_invoked
    assert output.search_status == "not_needed_catalogue_sufficient"


def test_research_search_failure_is_explicit():
    class Catalog:
        def list_products(self, category):
            return []

    class Rag:
        def retrieve(self, query):
            raise RuntimeError("down")

    class Search:
        def search(self, query):
            raise TimeoutError()

    output = asyncio.run(BankwiseAgentWorkflow(Catalog(), Rag(), Search()).research(
        "FD rates", RequirementOutput(requirements={"product_category": "FD"})
    ))
    assert output.search_invoked
    assert output.search_status == "failed:TimeoutError"


def test_explanation_agent_output_must_preserve_context_numbers_and_urls():
    context = {"amount": 100000, "maturity": 106000, "verified_sources": [
        {"url": "https://bank.example/rates"}
    ]}
    valid = (
        "1. Executive Decision Summary: for 100000.\n"
        "2. The Key Trade-off: maturity 106000.\n"
        "3. Conditions & Transparency: https://bank.example/rates"
    )
    assert _is_grounded_explanation(valid, context)
    assert not _is_grounded_explanation(valid.replace("106000", "108000"), context)
    assert not _is_grounded_explanation(valid.replace("bank.example/rates", "other.example/fd"), context)
