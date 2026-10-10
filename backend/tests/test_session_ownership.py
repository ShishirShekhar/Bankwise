from copy import deepcopy

from app.repositories.firestore import FirestoreSessionRepository
from app.repositories.memory_sessions import MemorySessionRepository


class Snapshot:
    def __init__(self, value):
        self.value = value
        self.exists = value is not None

    def to_dict(self):
        return deepcopy(self.value)


class Document:
    def __init__(self, documents, key):
        self.documents = documents
        self.key = key

    def set(self, value):
        self.documents[self.key] = deepcopy(value)

    def get(self):
        return Snapshot(self.documents.get(self.key))


class Collection:
    def __init__(self):
        self.documents = {}

    def document(self, key):
        return Document(self.documents, key)


class FirestoreClient:
    def __init__(self):
        self.collection_ref = Collection()

    def collection(self, _name):
        return self.collection_ref


def assert_repository_ownership(repository):
    repository.save_decision("session-1", "user-A", {}, [])

    assert repository.get_for_user("session-1", "user-A") == {
        "session_id": "session-1",
        "requirements": {},
        "product_ids": [],
        "comparison": [],
        "conversation_state": {
            "status": "decision_ready",
            "missing_information": [],
        },
        "created_at": repository.get("session-1")["created_at"],
        "updated_at": repository.get("session-1")["updated_at"],
    }
    assert repository.get_for_user("session-1", "user-B") is None
    assert repository.get_for_user("legacy-session", "user-A") is None


def test_memory_sessions_are_scoped_to_user():
    assert_repository_ownership(MemorySessionRepository())


def test_firestore_sessions_are_scoped_to_user():
    assert_repository_ownership(FirestoreSessionRepository(client=FirestoreClient()))
