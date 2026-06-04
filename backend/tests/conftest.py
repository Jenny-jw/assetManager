from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

import main as app_module
from dependencies.auth import get_current_user
from main import app
from routes import tea as tea_routes


@dataclass
class InsertOneResult:
    inserted_id: ObjectId


@dataclass
class DeleteResult:
    deleted_count: int


class FakeCursor:
    def __init__(self, docs: list[dict[str, Any]]):
        self.docs = docs

    def sort(self, key: str, direction: int):
        self.docs.sort(key=lambda doc: doc.get(key), reverse=direction == -1)
        return self

    def skip(self, count: int):
        self.docs = self.docs[count:]
        return self

    def limit(self, count: int):
        self.docs = self.docs[:count]
        return self

    def __iter__(self):
        return iter(self.docs)


class FakeCollection:
    def __init__(self):
        self.docs: dict[ObjectId, dict[str, Any]] = {}

    def create_index(self, *args, **kwargs):
        return None

    def insert_one(self, doc: dict[str, Any]):
        doc_id = ObjectId()
        stored_doc = deepcopy(doc)
        stored_doc["_id"] = doc_id
        self.docs[doc_id] = stored_doc
        return InsertOneResult(inserted_id=doc_id)

    def find(self, filters: dict[str, Any] | None = None):
        return FakeCursor(
            [
                deepcopy(doc)
                for doc in self.docs.values()
                if self._matches(doc, filters or {})
            ]
        )

    def count_documents(self, filters: dict[str, Any] | None = None):
        return sum(
            1 for doc in self.docs.values() if self._matches(doc, filters or {})
        )

    def find_one(self, filters: dict[str, Any]):
        for doc in self.docs.values():
            if self._matches(doc, filters):
                return deepcopy(doc)
        return None

    def find_one_and_update(
        self, filters: dict[str, Any], update: dict[str, Any], return_document=None
    ):
        for doc_id, doc in self.docs.items():
            if self._matches(doc, filters):
                doc.update(update.get("$set", {}))
                self.docs[doc_id] = doc
                return deepcopy(doc)
        return None

    def delete_one(self, filters: dict[str, Any]):
        for doc_id, doc in list(self.docs.items()):
            if self._matches(doc, filters):
                del self.docs[doc_id]
                return DeleteResult(deleted_count=1)
        return DeleteResult(deleted_count=0)

    def seed(self, *docs: dict[str, Any]):
        for doc in docs:
            self.insert_one({"created_at": datetime.now(timezone.utc), **doc})

    def _matches(self, doc: dict[str, Any], filters: dict[str, Any]):
        for key, expected in filters.items():
            if key == "$text":
                query = expected["$search"].lower()
                searchable = " ".join(
                    str(doc.get(field, "")) for field in ("name", "producer", "comment")
                )
                if query not in searchable.lower():
                    return False
                continue

            if key == "_id" and isinstance(expected, ObjectId):
                if doc.get("_id") != expected:
                    return False
                continue

            if doc.get(key) != expected:
                return False

        return True


class FakeDB:
    def __init__(self):
        self.teas = FakeCollection()
        self.users = FakeCollection()


def _make_user(role: str) -> dict[str, Any]:
    return {
        "id": str(ObjectId()),
        "role": role,
        "email": f"{role}@example.com",
        "name": role.capitalize(),
        "is_active": True,
    }


@pytest.fixture
def fake_db():
    return FakeDB()


def _build_client(monkeypatch, fake_db: FakeDB, auth_user: dict[str, Any] | None):
    monkeypatch.setattr(tea_routes, "db", fake_db)
    monkeypatch.setattr(app_module, "ensure_indexes", lambda: None)

    if auth_user is not None:
        app.dependency_overrides[get_current_user] = lambda: auth_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def client(monkeypatch, fake_db: FakeDB):
    yield from _build_client(monkeypatch, fake_db, _make_user("admin"))


@pytest.fixture
def client_no_auth(monkeypatch, fake_db: FakeDB):
    yield from _build_client(monkeypatch, fake_db, None)


@pytest.fixture
def client_user(monkeypatch, fake_db: FakeDB):
    yield from _build_client(monkeypatch, fake_db, _make_user("user"))


@pytest.fixture
def client_guest(monkeypatch, fake_db: FakeDB):
    yield from _build_client(monkeypatch, fake_db, _make_user("guest"))


@pytest.fixture
def seeded_tea_id(fake_db: FakeDB) -> str:
    fake_db.teas.seed(
        {
            "name": "Alishan Oolong",
            "genre": "Oolong",
            "origin": "Alishan",
            "quantity": 3,
        }
    )
    return str(next(iter(fake_db.teas.docs)))


TEA_CREATE_PAYLOAD = {
    "name": "Test Tea",
    "genre": "Oolong",
    "origin": "Alishan",
    "quantity": 1,
}
