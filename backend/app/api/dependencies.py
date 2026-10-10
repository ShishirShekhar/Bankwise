"""Shared repository dependencies for API routes and agent tools."""

from functools import lru_cache

from app.config import ENVIRONMENT


@lru_cache(maxsize=1)
def get_catalog():
    """Use BigQuery in production and the local JSON catalogue locally."""
    if ENVIRONMENT == "production":
        from app.repositories.bigquery import BigQueryRepository

        return BigQueryRepository()
    from app.repositories.local_json import LocalJsonCatalog

    return LocalJsonCatalog()


@lru_cache(maxsize=1)
def get_sessions():
    """Use Firestore in production and in-memory sessions locally."""
    if ENVIRONMENT == "production":
        from app.repositories.firestore import FirestoreSessionRepository

        return FirestoreSessionRepository()
    from app.repositories.memory_sessions import MemorySessionRepository

    return MemorySessionRepository()
