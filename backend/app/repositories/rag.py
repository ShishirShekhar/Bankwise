"""BigQuery-backed evidence corpus. Research chunks are never canonical rates."""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.config import (
    BIGQUERY_LOCATION,
    BIGQUERY_PROJECT,
    EMBEDDING_MODEL,
    RAG_DATASET,
    RAG_FRESHNESS_DAYS,
    RAG_MAX_DISTANCE,
    RAG_TOP_K,
)


def normalize_url(url: str) -> str:
    parsed = urlsplit(url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username:
        raise ValueError("Only public HTTP(S) source URLs are accepted")
    query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
    if any(re.search(r"(?:api_?key|token|auth|session|password|secret|credential)", key, re.IGNORECASE)
           for key, _value in query_pairs):
        raise ValueError("Credential-like URL parameters are not accepted")
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path or "/", urlencode(query_pairs), ""))


def split_chunks(text: str, size: int, overlap: int) -> list[str]:
    """Split extracted text into bounded, stable overlapping excerpts."""
    if size < 1 or overlap < 0 or overlap >= size:
        raise ValueError("Invalid chunk size or overlap")
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    chunks = []
    start = 0
    while start < len(normalized):
        end = min(start + size, len(normalized))
        if end < len(normalized):
            boundary = normalized.rfind(" ", start, end)
            if boundary > start:
                end = boundary
        chunks.append(normalized[start:end])
        if end == len(normalized):
            break
        start = max(end - overlap, start + 1)
    return chunks


def stable_id(*values: str) -> str:
    return hashlib.sha256("\x1f".join(values).encode("utf-8")).hexdigest()


class GeminiEmbedder:
    """Use the configured Google Gen AI SDK Vertex AI client for both text types."""

    def __init__(self, client=None, model: str = EMBEDDING_MODEL):
        self.model = model
        if client is None:
            from google import genai
            from google.genai import types

            from app.config import GOOGLE_CLOUD_LOCATION

            client = genai.Client(
                vertexai=True,
                project=BIGQUERY_PROJECT,
                location=GOOGLE_CLOUD_LOCATION,
                http_options=types.HttpOptions(timeout=15_000),
            )
        self.client = client

    def embed(self, text: str, task_type: str) -> list[float]:
        response = self.client.models.embed_content(
            model=self.model,
            contents=text,
            config={"task_type": task_type},
        )
        if not response.embeddings or not response.embeddings[0].values:
            raise RuntimeError("Embedding provider returned no vector")
        return [float(value) for value in response.embeddings[0].values]


class BigQueryRagRepository:
    def __init__(self, client=None, dataset: str = RAG_DATASET, embedder=None):
        if not re.fullmatch(r"[A-Za-z0-9_]+", dataset) or not BIGQUERY_PROJECT:
            raise ValueError("Invalid RAG dataset or missing BigQuery project")
        if client is None:
            from google.cloud import bigquery

            client = bigquery.Client(project=BIGQUERY_PROJECT, location=BIGQUERY_LOCATION)
        self.client = client
        self.dataset = dataset
        self.prefix = f"`{BIGQUERY_PROJECT}.{dataset}"
        self.embedder = embedder or GeminiEmbedder()

    def _query(self, sql: str, parameters: list[Any]):
        from google.cloud import bigquery

        config = bigquery.QueryJobConfig(query_parameters=parameters)
        return self.client.query(sql, job_config=config, location=BIGQUERY_LOCATION).result()

    def upsert_document(self, document: dict[str, Any], chunks: list[dict[str, Any]]) -> None:
        """MERGE stable document/chunk identifiers; repeat ingestion replaces rows."""
        from google.cloud import bigquery

        # Retire excerpts from an earlier revision before adding changed content.
        self._query(
            f"UPDATE {self.prefix}.source_chunks` SET source_status='STALE' "
            "WHERE document_id=@document_id AND content_hash!=@content_hash",
            [bigquery.ScalarQueryParameter("document_id", "STRING", document["document_id"]),
             bigquery.ScalarQueryParameter("content_hash", "STRING", document["content_hash"])],
        )

        doc_params = [
            bigquery.ScalarQueryParameter("document_id", "STRING", document["document_id"]),
            bigquery.ScalarQueryParameter("canonical_url", "STRING", document["canonical_url"]),
            bigquery.ScalarQueryParameter("title", "STRING", document["title"]),
            bigquery.ScalarQueryParameter("publisher", "STRING", document.get("publisher")),
            bigquery.ScalarQueryParameter("domain", "STRING", document["domain"]),
            bigquery.ScalarQueryParameter("document_type", "STRING", document["document_type"]),
            bigquery.ScalarQueryParameter("published_at", "TIMESTAMP", document.get("published_at")),
            bigquery.ScalarQueryParameter("effective_from", "DATE", document.get("effective_from")),
            bigquery.ScalarQueryParameter("effective_to", "DATE", document.get("effective_to")),
            bigquery.ScalarQueryParameter("retrieved_at", "TIMESTAMP", document["retrieved_at"]),
            bigquery.ScalarQueryParameter("content_hash", "STRING", document["content_hash"]),
            bigquery.ScalarQueryParameter("source_status", "STRING", document.get("source_status", "ACTIVE")),
            bigquery.ScalarQueryParameter("verification_status", "STRING", document.get("verification_status", "PENDING")),
            bigquery.ScalarQueryParameter("ingestion_status", "STRING", document.get("ingestion_status", "INDEXED")),
        ]
        self._query(
            f"""MERGE {self.prefix}.source_documents` T USING (
              SELECT @document_id document_id, @canonical_url canonical_url, @title title,
              @publisher publisher, @domain domain, @document_type document_type,
              @published_at published_at, @effective_from effective_from, @effective_to effective_to,
              @retrieved_at retrieved_at, @content_hash content_hash, @source_status source_status,
              @verification_status verification_status, @ingestion_status ingestion_status
            ) S ON T.document_id=S.document_id
            WHEN MATCHED THEN UPDATE SET canonical_url=S.canonical_url, title=S.title,
              publisher=S.publisher, domain=S.domain, document_type=S.document_type,
              published_at=S.published_at, effective_from=S.effective_from, effective_to=S.effective_to,
              retrieved_at=S.retrieved_at, content_hash=S.content_hash, source_status=S.source_status,
              verification_status=S.verification_status, ingestion_status=S.ingestion_status
            WHEN NOT MATCHED THEN INSERT ROW""", doc_params)
        for chunk in chunks:
            params = [
                bigquery.ScalarQueryParameter("chunk_id", "STRING", chunk["chunk_id"]),
                bigquery.ScalarQueryParameter("document_id", "STRING", document["document_id"]),
                bigquery.ScalarQueryParameter("chunk_index", "INT64", chunk["chunk_index"]),
                bigquery.ScalarQueryParameter("excerpt", "STRING", chunk["excerpt"]),
                bigquery.ScalarQueryParameter("product_category", "STRING", chunk.get("product_category")),
                bigquery.ScalarQueryParameter("product_id", "STRING", chunk.get("product_id")),
                bigquery.ScalarQueryParameter("source_status", "STRING", document.get("source_status", "ACTIVE")),
                bigquery.ScalarQueryParameter("verification_status", "STRING", document.get("verification_status", "PENDING")),
                bigquery.ScalarQueryParameter("retrieved_at", "TIMESTAMP", document["retrieved_at"]),
                bigquery.ScalarQueryParameter("content_hash", "STRING", document["content_hash"]),
                bigquery.ArrayQueryParameter("embedding", "FLOAT64", chunk["embedding"]),
                bigquery.ScalarQueryParameter("embedding_model", "STRING", self.embedder.model),
                bigquery.ScalarQueryParameter("embedding_dimensions", "INT64", len(chunk["embedding"])),
            ]
            self._query(
                f"""MERGE {self.prefix}.source_chunks` T USING (
                  SELECT @chunk_id chunk_id, @document_id document_id, @chunk_index chunk_index,
                  @excerpt excerpt, @product_category product_category, @product_id product_id,
                  @source_status source_status, @verification_status verification_status,
                  @retrieved_at retrieved_at, @content_hash content_hash, @embedding embedding,
                  @embedding_model embedding_model, @embedding_dimensions embedding_dimensions
                ) S ON T.chunk_id=S.chunk_id
                WHEN MATCHED THEN UPDATE SET excerpt=S.excerpt, embedding=S.embedding,
                  embedding_model=S.embedding_model, embedding_dimensions=S.embedding_dimensions,
                  content_hash=S.content_hash, retrieved_at=S.retrieved_at,
                  verification_status=S.verification_status, source_status=S.source_status
                WHEN NOT MATCHED THEN INSERT ROW""", params)

    def upsert_candidates(self, candidates: list[dict[str, Any]]) -> None:
        """Store extracted facts for review without touching canonical records."""
        from google.cloud import bigquery
        for candidate in candidates:
            params = [
                bigquery.ScalarQueryParameter("candidate_id", "STRING", candidate["candidate_id"]),
                bigquery.ScalarQueryParameter("fact_type", "STRING", candidate["fact_type"]),
                bigquery.ScalarQueryParameter("candidate_value", "STRING", candidate["candidate_value"]),
                bigquery.ArrayQueryParameter("evidence_chunk_ids", "STRING", candidate["evidence_chunk_ids"]),
                bigquery.ScalarQueryParameter("source_url", "STRING", candidate["source_url"]),
                bigquery.ScalarQueryParameter("retrieved_at", "TIMESTAMP", candidate["retrieved_at"]),
                bigquery.ScalarQueryParameter("content_hash", "STRING", candidate["content_hash"]),
            ]
            self._query(
                f"""MERGE {self.prefix}.research_candidates` T USING (
                  SELECT @candidate_id candidate_id, @fact_type fact_type,
                  PARSE_JSON(@candidate_value) candidate_value,
                  @evidence_chunk_ids evidence_chunk_ids, @source_url source_url,
                  @retrieved_at retrieved_at, @content_hash content_hash
                ) S ON T.candidate_id=S.candidate_id
                WHEN MATCHED THEN UPDATE SET candidate_value=S.candidate_value,
                  evidence_chunk_ids=S.evidence_chunk_ids, retrieved_at=S.retrieved_at,
                  content_hash=S.content_hash
                WHEN NOT MATCHED THEN INSERT (candidate_id, fact_type, candidate_value,
                  evidence_chunk_ids, source_url, retrieved_at, verification_status,
                  validation_status, promotion_status, content_hash)
                VALUES (S.candidate_id, S.fact_type, S.candidate_value,
                  S.evidence_chunk_ids, S.source_url, S.retrieved_at, 'PENDING',
                  'PENDING', 'NOT_PROMOTED', S.content_hash)""", params)

    def retrieve(self, query: str, top_k: int = RAG_TOP_K, category: str = "FD") -> list[dict[str, Any]]:
        from google.cloud import bigquery

        vector = self.embedder.embed(query, "RETRIEVAL_QUERY")
        sql = f"""SELECT base.chunk_id, base.document_id, base.excerpt, base.product_category,
          base.product_id, base.source_status, base.verification_status, base.retrieved_at,
          base.content_hash, base.embedding_model, docs.canonical_url, docs.title, docs.domain,
          distance
          FROM VECTOR_SEARCH(
            (SELECT * FROM {self.prefix}.source_chunks` WHERE product_category=@category
              AND source_status='ACTIVE' AND verification_status='HIGH'
              AND embedding_model=@embedding_model AND embedding_dimensions=@embedding_dimensions
              AND retrieved_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL @freshness DAY)),
            'embedding', query_value=>@query_embedding, top_k=>@top_k, distance_type=>'COSINE',
            options=>'{{"use_brute_force":true}}') AS matches
          JOIN {self.prefix}.source_chunks` AS base ON base.chunk_id=matches.base.chunk_id
          JOIN {self.prefix}.source_documents` AS docs
            ON docs.document_id=base.document_id AND docs.content_hash=base.content_hash
            AND docs.source_status='ACTIVE' AND docs.verification_status='HIGH'
          ORDER BY distance ASC"""
        params = [
            bigquery.ScalarQueryParameter("category", "STRING", category),
            bigquery.ScalarQueryParameter("freshness", "INT64", RAG_FRESHNESS_DAYS),
            bigquery.ArrayQueryParameter("query_embedding", "FLOAT64", vector),
            bigquery.ScalarQueryParameter("embedding_model", "STRING", self.embedder.model),
            bigquery.ScalarQueryParameter("embedding_dimensions", "INT64", len(vector)),
            bigquery.ScalarQueryParameter("top_k", "INT64", min(max(top_k, 1), 20)),
        ]
        rows = [dict(row.items()) for row in self._query(sql, params)]
        return [row for row in rows if float(row.get("distance", 2)) <= RAG_MAX_DISTANCE]


def make_document(url: str, title: str, text: str, publisher: str | None, document_type: str, retrieved_at: datetime | None = None) -> tuple[dict[str, Any], list[str]]:
    """Create source metadata plus stable excerpt identifiers from extracted text."""
    normalized_url = normalize_url(url)
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    timestamp = retrieved_at or datetime.now(UTC)
    document_id = stable_id(normalized_url)
    from app.config import RAG_CHUNK_OVERLAP, RAG_CHUNK_SIZE

    excerpts = split_chunks(text, RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP)
    document = {
        "document_id": document_id, "canonical_url": normalized_url, "title": title[:500],
        "publisher": publisher, "domain": urlsplit(normalized_url).hostname or "",
        "document_type": document_type, "retrieved_at": timestamp, "content_hash": content_hash,
        "source_status": "ACTIVE", "verification_status": "PENDING", "ingestion_status": "INDEXED",
    }
    return document, excerpts
