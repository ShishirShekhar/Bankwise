"""Process-local session storage for the local environment."""

from copy import deepcopy
from datetime import datetime, timezone


class MemorySessionRepository:
    def __init__(self):
        self._documents: dict[str, dict] = {}

    def save_decision(
        self,
        session_id: str,
        user_id: str,
        requirements: dict,
        comparisons: list,
        missing_information=None,
    ) -> dict:
        missing_information = missing_information or []
        now = datetime.now(timezone.utc)
        record = {
            "session_id": session_id,
            "user_id": user_id,
            "requirements": deepcopy(requirements),
            "product_ids": [item["product"]["id"] for item in comparisons],
            "comparison": deepcopy(comparisons),
            "conversation_state": {
                "status": "awaiting_requirements" if missing_information else "decision_ready",
                "missing_information": list(missing_information),
            },
            "created_at": now,
            "updated_at": now,
        }
        self._documents[session_id] = record
        return deepcopy(record)

    def get(self, session_id: str) -> dict | None:
        record = self._documents.get(session_id)
        return deepcopy(record) if record else None

    def get_for_user(self, session_id: str, user_id: str) -> dict | None:
        record = self._documents.get(session_id)
        if not record or record.get("user_id") != user_id:
            return None
        owned_record = deepcopy(record)
        owned_record.pop("user_id", None)
        return owned_record
