"""Shared local development dependencies for API routes."""

from app.repositories.local_json import LocalJsonCatalog
from app.repositories.memory_sessions import MemorySessionRepository

_catalog = LocalJsonCatalog()
_sessions = MemorySessionRepository()


def get_catalog():
    return _catalog


def get_sessions():
    return _sessions
