"""Current Google Search grounding for the request-scoped research specialist."""

from __future__ import annotations

from datetime import UTC, datetime

from app.config import (
    GEMINI_MODEL,
    GOOGLE_CLOUD_PROJECT,
    GOOGLE_SEARCH_LOCATION,
    SEARCH_MAX_RESULTS,
)
from app.domain.input import redact_sensitive_input


class GoogleSearchResearcher:
    """Calls the Gen AI Google Search grounding tool and preserves grounding URLs."""

    def __init__(self, client=None):
        self.client = client
        if client is None:
            from google import genai
            from google.genai import types

            if not GOOGLE_CLOUD_PROJECT:
                raise RuntimeError("Google Cloud project is not configured")
            self.client = genai.Client(
                vertexai=True,
                project=GOOGLE_CLOUD_PROJECT,
                location=GOOGLE_SEARCH_LOCATION,
                http_options=types.HttpOptions(api_version="v1", timeout=15_000),
            )

    def search(self, query: str) -> dict:
        from google.genai import types

        safe_query = redact_sensitive_input(query)
        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=("Find current, authoritative official bank fixed-deposit rates and conditions. "
                      "Prefer bank and regulator sources. Return factual findings with source URLs. Query: " + safe_query),
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0,
            ),
        )
        grounding = getattr(response, "grounding_metadata", None)
        if grounding is None and getattr(response, "candidates", None):
            grounding = getattr(response.candidates[0], "grounding_metadata", None)
        sources = []
        for chunk in getattr(grounding, "grounding_chunks", None) or []:
            web = getattr(chunk, "web", None)
            if web and getattr(web, "uri", None):
                sources.append({"url": web.uri, "title": getattr(web, "title", "")})
        return {
            "invoked": True,
            "text": getattr(response, "text", "") or "",
            "sources": sources[:SEARCH_MAX_RESULTS],
            "retrieved_at": datetime.now(UTC).isoformat(),
            "search_suggestions": getattr(grounding, "search_entry_point", None),
        }
