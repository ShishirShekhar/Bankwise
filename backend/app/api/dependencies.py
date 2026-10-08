"""Shared repository dependencies for API routes and agent tools."""

from functools import lru_cache

from app.config import ENVIRONMENT


@lru_cache(maxsize=1)
def get_catalog():
    """Use the verified product catalogue: BigQuery in production, LocalJson in development."""
    if ENVIRONMENT == "production":
        from app.repositories.bigquery import BigQueryRepository

        return BigQueryRepository()
    from app.repositories.local_json import LocalJsonCatalog

    return LocalJsonCatalog()


@lru_cache(maxsize=1)
def get_sessions():
    """Persist redacted decision sessions: Firestore in production, Memory in development."""
    if ENVIRONMENT == "production":
        from app.repositories.firestore import FirestoreSessionRepository

        return FirestoreSessionRepository()
    from app.repositories.memory_sessions import MemorySessionRepository

    return MemorySessionRepository()
