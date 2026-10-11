"""Explicitly ingest one allow-listed public source into the RAG staging corpus."""

import argparse
import json

from app.ai.ingestion import ingest_public_source
from app.config import RAG_DATASET
from app.repositories.rag import BigQueryRagRepository


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--allowed-domain", action="append", required=True,
                        help="Exact source domain allow-list entry; may be repeated")
    parser.add_argument("--trusted-official-domain", action="append", default=[],
                        help="Operator-reviewed official domain eligible for source-level RAG retrieval")
    args = parser.parse_args()
    result = ingest_public_source(args.url, allowed_domains=set(args.allowed_domain),
                                  trusted_official_domains=set(args.trusted_official_domain),
                                  repository=BigQueryRagRepository(dataset=RAG_DATASET))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
