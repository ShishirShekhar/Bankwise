"""Shared FastAPI dependencies for API routes."""

from app.repositories.bigquery import BigQueryRepository
from app.repositories.firestore import FirestoreSessionRepository


def get_catalog():
    return BigQueryRepository()


def get_sessions():
    return FirestoreSessionRepository()
