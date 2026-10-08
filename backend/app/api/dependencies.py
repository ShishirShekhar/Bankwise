"""Shared cloud repository dependencies for API routes and agent tools."""

from functools import lru_cache

from app.repositories.bigquery import BigQueryRepository
from app.repositories.firestore import FirestoreSessionRepository


@lru_cache(maxsize=1)
def get_catalog() -> BigQueryRepository:
    """Use the verified product catalogue stored in BigQuery."""
    return BigQueryRepository()


@lru_cache(maxsize=1)
def get_sessions() -> FirestoreSessionRepository:
    """Persist redacted decision sessions in Firestore."""
    return FirestoreSessionRepository()
