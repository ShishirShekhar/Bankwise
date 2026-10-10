import pytest

from app import config
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


def test_production_configuration_requires_cloud_auth_and_deployed_cors(monkeypatch):
    monkeypatch.setattr(config, "ENVIRONMENT", "production")
    monkeypatch.setattr(config, "GOOGLE_CLOUD_PROJECT", "project-1")
    monkeypatch.setattr(config, "BIGQUERY_PROJECT", "project-1")
    monkeypatch.setattr(config, "FIREBASE_PROJECT_ID", "")
    monkeypatch.setattr(config, "CORS_ORIGINS", ["https://bankwise.example"])
    monkeypatch.setattr(config, "CSRF_SECRET", "x" * 32)

    with pytest.raises(ValueError, match="FIREBASE_PROJECT_ID"):
        config.validate_production_settings()

    monkeypatch.setattr(config, "FIREBASE_PROJECT_ID", "firebase-project")
    monkeypatch.setattr(config, "CORS_ORIGINS", ["http://localhost:3000"])
    with pytest.raises(ValueError, match="deployed origins"):
        config.validate_production_settings()
