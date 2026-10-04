import os
from dotenv import load_dotenv

load_dotenv()


def setting(name: str, default: str) -> str:
    return os.getenv(name, default)


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
CORS_ORIGINS = [origin.strip() for origin in setting("CORS_ORIGINS", "http://localhost:3000").split(",") if origin.strip()]
