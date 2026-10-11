"""Bounded, allow-listed public web ingestion for evidence staging only."""

from __future__ import annotations

import ipaddress
import json
import re
import socket
from datetime import UTC, datetime
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.robotparser import RobotFileParser

from app.config import INGEST_MAX_DOCUMENT_BYTES, RAG_CHUNK_OVERLAP, RAG_CHUNK_SIZE
from app.domain.input import redact_sensitive_input
from app.repositories.rag import make_document, stable_id


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1

    def handle_endtag(self, tag):
        if tag.lower() in {"script", "style", "noscript", "svg"} and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data):
        if not self.skip_depth and data.strip():
            self.parts.append(data.strip())


def _public_destination(url: str, allow_domains: set[str]) -> str:
    parsed = urlsplit(url)
    host = parsed.hostname or ""
    if parsed.scheme not in {"http", "https"} or not host or parsed.username or parsed.password:
        raise ValueError("URL must be a public HTTP(S) destination")
    if not any(host == domain or host.endswith("." + domain) for domain in allow_domains):
        raise ValueError("Source domain is not allow-listed")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80))}
    except OSError as exc:
        raise ValueError("Source hostname did not resolve") from exc
    if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
        raise ValueError("Source hostname resolves to a non-public address")
    return url


def _fetch(url: str, allow_domains: set[str], max_bytes: int) -> tuple[str, str, str]:
    class SafeRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            _public_destination(newurl, allow_domains)
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    safe_url = _public_destination(url, allow_domains)
    parsed_url = urlsplit(safe_url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    try:
        _public_destination(robots_url, allow_domains)
        with build_opener(SafeRedirect).open(
            Request(robots_url, headers={"User-Agent": "BankwiseResearch/1.0"}), timeout=5
        ) as robots_response:
            if robots_response.status == 200:
                rules = robots_response.read(128_000).decode("utf-8", errors="replace")
                parser = RobotFileParser(robots_url)
                parser.parse(rules.splitlines())
                if not parser.can_fetch("BankwiseResearch", safe_url):
                    raise ValueError("robots.txt disallows source retrieval")
    except ValueError:
        raise
    except (HTTPError, URLError, TimeoutError, OSError):
        # An unavailable robots.txt is treated conservatively: do not fetch.
        raise ValueError("robots.txt could not be checked")
    request = Request(safe_url, headers={"User-Agent": "BankwiseResearch/1.0 (+public-source-indexing)"})
    try:
        with build_opener(SafeRedirect).open(request, timeout=8) as response:
            final_url = _public_destination(response.geturl(), allow_domains)
            content_type = response.headers.get_content_type().lower()
            if content_type not in {"text/html", "application/xhtml+xml", "text/plain"}:
                raise ValueError("Only public HTML and plain text are currently indexable")
            body = response.read(max_bytes + 1)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise ValueError("Source could not be fetched") from exc
    if len(body) > max_bytes:
        raise ValueError("Source exceeds the configured document size limit")
    decoded = body.decode("utf-8", errors="replace")
    if content_type in {"text/html", "application/xhtml+xml"}:
        parser = _TextExtractor()
        parser.feed(decoded)
        text = " ".join(parser.parts)
    else:
        text = decoded
    return final_url, text, content_type


def ingest_public_source(url: str, *, allowed_domains: set[str], repository,
                         title: str | None = None, publisher: str | None = None,
                         trusted_official_domains: set[str] | None = None,
                         max_bytes: int = INGEST_MAX_DOCUMENT_BYTES) -> dict:
    """Fetch, excerpt, embed and idempotently stage an allow-listed source.

    The routine never writes catalogue tables and never promotes financial facts.
    """
    final_url, text, content_type = _fetch(url, allowed_domains, min(max_bytes, INGEST_MAX_DOCUMENT_BYTES))
    text = redact_sensitive_input(text)
    document, _excerpts = make_document(final_url, title or final_url, text, publisher, content_type, datetime.now(UTC))
    domain = (urlsplit(final_url).hostname or "").lower()
    official_domains = {item.lower() for item in (trusted_official_domains or set())}
    source_verified = any(domain == item or domain.endswith("." + item) for item in official_domains)
    from app.repositories.rag import split_chunks

    chunks = []
    for index, excerpt in enumerate(split_chunks(text, RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP)):
        vector = repository.embedder.embed(excerpt, "RETRIEVAL_DOCUMENT")
        chunks.append({
            "chunk_id": stable_id(document["document_id"], document["content_hash"], str(index)),
            "chunk_index": index, "excerpt": excerpt, "product_category": "FD",
            "embedding": vector,
        })
    # Source indexing is evidence collection; human/policy verification and any
    # canonical promotion are separate workflows.
    document["verification_status"] = "HIGH" if source_verified else "PENDING"
    repository.upsert_document(document, chunks)
    candidate_pattern = re.compile(r"(?<![\w.])(\d{1,2}(?:\.\d{1,4})?)\s*%")
    candidates = []
    for chunk in chunks:
        for match in candidate_pattern.finditer(chunk["excerpt"]):
            value = float(match.group(1))
            candidate_id = stable_id(document["document_id"], document["content_hash"],
                                     chunk["chunk_id"], "rate_percent", match.group(0))
            candidates.append({
                "candidate_id": candidate_id, "fact_type": "rate_percent",
                "candidate_value": json.dumps({"value": value, "unit": "percent", "evidence": match.group(0)}),
                "evidence_chunk_ids": [chunk["chunk_id"]], "source_url": final_url,
                "retrieved_at": document["retrieved_at"], "content_hash": document["content_hash"],
            })
    repository.upsert_candidates(candidates)
    return {"document_id": document["document_id"], "content_hash": document["content_hash"],
            "documents_upserted": 1, "chunks_upserted": len(chunks),
            "candidate_facts": len(candidates), "promotion_status": "NOT_PROMOTED",
            "evidence_status": "SOURCE_VERIFIED" if source_verified else "PENDING_REVIEW",
            "reason": "Financial candidate facts remain pending deterministic product, applicability, date, and conflict verification"}
