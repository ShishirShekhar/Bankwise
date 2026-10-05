import pytest


@pytest.fixture(autouse=True)
def no_real_gemini_explanations(monkeypatch):
    monkeypatch.setattr("app.ai.explanation._generate", lambda _facts: None)