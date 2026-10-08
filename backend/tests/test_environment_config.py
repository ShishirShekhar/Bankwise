from app.api import dependencies
from app.repositories.local_json import LocalJsonCatalog
from app.repositories.memory_sessions import MemorySessionRepository


def test_dependencies_use_local_and_memory_in_development(monkeypatch):
    monkeypatch.setattr(dependencies, "ENVIRONMENT", "development")
    dependencies.get_catalog.cache_clear()
    dependencies.get_sessions.cache_clear()

    catalog = dependencies.get_catalog()
    sessions = dependencies.get_sessions()

    assert isinstance(catalog, LocalJsonCatalog)
    assert isinstance(sessions, MemorySessionRepository)

    dependencies.get_catalog.cache_clear()
    dependencies.get_sessions.cache_clear()
