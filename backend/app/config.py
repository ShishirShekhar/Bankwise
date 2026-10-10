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
GOOGLE_CLOUD_PROJECT = setting("GOOGLE_CLOUD_PROJECT", "")
GOOGLE_CLOUD_LOCATION = setting("GOOGLE_CLOUD_LOCATION", "us-central1")
BIGQUERY_PROJECT = setting("BIGQUERY_PROJECT", "") or GOOGLE_CLOUD_PROJECT
BIGQUERY_DATASET = setting("BIGQUERY_DATASET", "bankwise")
BIGQUERY_LOCATION = setting("BIGQUERY_LOCATION", GOOGLE_CLOUD_LOCATION)
FIRESTORE_DATABASE = setting("FIRESTORE_DATABASE", "(default)")
FIRESTORE_PROJECT = setting("FIRESTORE_PROJECT", "") or GOOGLE_CLOUD_PROJECT
FIRESTORE_COLLECTION = setting("FIRESTORE_COLLECTION", "decision_sessions")
SOURCE_MAX_AGE_DAYS = int(setting("SOURCE_MAX_AGE_DAYS", "90"))
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
