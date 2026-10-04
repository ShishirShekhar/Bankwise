"""Firestore persistence for redacted decision-session state."""

from datetime import date, datetime, time, timezone

from app.config import FIRESTORE_COLLECTION, FIRESTORE_DATABASE, FIRESTORE_PROJECT


def _firestore_safe(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, time.min, tzinfo=timezone.utc)
    if isinstance(value, dict):
        return {key: _firestore_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_firestore_safe(item) for item in value]
    return value


class FirestoreSessionRepository:
    def __init__(self, client=None):
        if client is None:
            from google.cloud import firestore
            client = firestore.Client(project=FIRESTORE_PROJECT or None, database=FIRESTORE_DATABASE)
        self.client = client
        self.collection = client.collection(FIRESTORE_COLLECTION)

    def save_decision(self, session_id: str, requirements: dict, comparisons: list, missing_information=None) -> dict:
        from google.cloud import firestore
        missing_information = missing_information or []
        record = _firestore_safe({
            "session_id": session_id,
            "requirements": requirements,
            "product_ids": [item["product"]["id"] for item in comparisons],
            "comparison": comparisons,
            "conversation_state": {"status": "awaiting_requirements" if missing_information else "decision_ready",
                                   "missing_information": missing_information},
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP,
        })
        self.collection.document(session_id).set(record)
        return record

    def get(self, session_id: str):
        snapshot = self.collection.document(session_id).get()
        return snapshot.to_dict() if snapshot.exists else None
