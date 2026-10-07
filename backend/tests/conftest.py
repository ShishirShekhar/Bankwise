"""Keep API and ADK tests independent of configured cloud services."""

import pytest

from app import tools
from app.api import dependencies
from app.main import app
from app.repositories.local_json import LocalJsonCatalog


@pytest.fixture(autouse=True)
def use_local_catalog(monkeypatch):
    """Use the checked-in catalogue instead of querying BigQuery in tests."""
    catalog = LocalJsonCatalog()
    app.dependency_overrides[dependencies.get_catalog] = lambda: catalog
    monkeypatch.setattr(tools, "get_catalog", lambda: catalog)
    yield
    app.dependency_overrides.pop(dependencies.get_catalog, None)
