import os

from dotenv import load_dotenv

load_dotenv()


def setting(name: str, default: str) -> str:
    return os.getenv(name, default)


ENVIRONMENT = setting("ENVIRONMENT", "local").lower()
if ENVIRONMENT == "development":
    ENVIRONMENT = "local"
if ENVIRONMENT not in {"local", "production"}:
    raise ValueError("ENVIRONMENT must be local or production")
GEMINI_MODEL = setting("GEMINI_MODEL", "gemini-2.5-flash")
ENABLE_ADK_EXPLANATION = setting("ENABLE_ADK_EXPLANATION", "false").lower() == "true"
GOOGLE_CLOUD_PROJECT = setting("GOOGLE_CLOUD_PROJECT", "")
GOOGLE_CLOUD_LOCATION = setting("GOOGLE_CLOUD_LOCATION", "us-central1")
GOOGLE_SEARCH_LOCATION = setting("GOOGLE_SEARCH_LOCATION", "global")
BIGQUERY_PROJECT = setting("BIGQUERY_PROJECT", "") or GOOGLE_CLOUD_PROJECT
BIGQUERY_DATASET = setting("BIGQUERY_DATASET", "bankwise")
BIGQUERY_LOCATION = setting("BIGQUERY_LOCATION", GOOGLE_CLOUD_LOCATION)
RAG_DATASET = setting("RAG_DATASET", "bankwise_rag")
EMBEDDING_MODEL = setting("EMBEDDING_MODEL", "gemini-embedding-001")
RAG_TOP_K = int(setting("RAG_TOP_K", "6"))
RAG_MAX_DISTANCE = float(setting("RAG_MAX_DISTANCE", "0.55"))
RAG_CHUNK_SIZE = int(setting("RAG_CHUNK_SIZE", "1200"))
RAG_CHUNK_OVERLAP = int(setting("RAG_CHUNK_OVERLAP", "150"))
SEARCH_MAX_RESULTS = int(setting("SEARCH_MAX_RESULTS", "5"))
INGEST_MAX_DOCUMENT_BYTES = int(setting("INGEST_MAX_DOCUMENT_BYTES", "2000000"))
FIRESTORE_DATABASE = setting("FIRESTORE_DATABASE", "(default)")
FIRESTORE_PROJECT = setting("FIRESTORE_PROJECT", "") or GOOGLE_CLOUD_PROJECT
FIRESTORE_COLLECTION = setting("FIRESTORE_COLLECTION", "decision_sessions")
SOURCE_MAX_AGE_DAYS = int(setting("SOURCE_MAX_AGE_DAYS", "90"))
RAG_FRESHNESS_DAYS = int(setting("RAG_FRESHNESS_DAYS", str(SOURCE_MAX_AGE_DAYS)))
if min(RAG_TOP_K, RAG_CHUNK_SIZE, SEARCH_MAX_RESULTS, INGEST_MAX_DOCUMENT_BYTES, RAG_FRESHNESS_DAYS) < 1:
    raise ValueError("RAG, search, and ingestion limits must be positive")
if RAG_CHUNK_OVERLAP < 0 or RAG_CHUNK_OVERLAP >= RAG_CHUNK_SIZE:
    raise ValueError("RAG_CHUNK_OVERLAP must be non-negative and smaller than RAG_CHUNK_SIZE")
if not 0 <= RAG_MAX_DISTANCE <= 2:
    raise ValueError("RAG_MAX_DISTANCE must be between 0 and 2")
ASK_RATE_LIMIT = int(setting("ASK_RATE_LIMIT", "10"))
ASK_RATE_WINDOW_SECONDS = int(setting("ASK_RATE_WINDOW_SECONDS", "60"))
if ASK_RATE_LIMIT < 1 or ASK_RATE_WINDOW_SECONDS < 1:
    raise ValueError("ASK_RATE_LIMIT and ASK_RATE_WINDOW_SECONDS must be positive")
CORS_ORIGINS = [
    origin.strip()
    for origin in setting("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
FIREBASE_PROJECT_ID = setting("FIREBASE_PROJECT_ID", "") or GOOGLE_CLOUD_PROJECT
CSRF_SECRET = setting("CSRF_SECRET", "")
if ENVIRONMENT == "production" and len(CSRF_SECRET) < 32:
    raise ValueError("CSRF_SECRET must be set to at least 32 characters in production")
if ENVIRONMENT == "local" and not CSRF_SECRET:
    CSRF_SECRET = "bankwise-local-csrf-secret-not-for-production"


def validate_production_settings() -> None:
    """Fail closed when a production deployment lacks its required settings."""
    missing_production_settings = [
        name
        for name, value in (
            ("GOOGLE_CLOUD_PROJECT", GOOGLE_CLOUD_PROJECT),
            ("BIGQUERY_PROJECT", BIGQUERY_PROJECT),
            ("FIREBASE_PROJECT_ID", FIREBASE_PROJECT_ID),
        )
        if not value
    ]
    if missing_production_settings:
        raise ValueError(
            "Production requires: " + ", ".join(missing_production_settings)
        )
    if not CORS_ORIGINS or any(
        "localhost" in origin or "127.0.0.1" in origin for origin in CORS_ORIGINS
    ):
        raise ValueError("Production CORS_ORIGINS must contain only deployed origins")


if ENVIRONMENT == "production":
    validate_production_settings()
AUTH_COOKIE_SECURE = setting(
    "AUTH_COOKIE_SECURE", "true" if ENVIRONMENT == "production" else "false"
).lower() == "true"
AUTH_COOKIE_SAMESITE = setting(
    "AUTH_COOKIE_SAMESITE", "none" if ENVIRONMENT == "production" else "lax"
).lower()
if AUTH_COOKIE_SAMESITE not in {"lax", "strict", "none"}:
    raise ValueError("AUTH_COOKIE_SAMESITE must be lax, strict, or none")
if (AUTH_COOKIE_SAMESITE == "none" or ENVIRONMENT == "production") and not AUTH_COOKIE_SECURE:
    raise ValueError("AUTH_COOKIE_SECURE must be true in production and with SameSite=none")
