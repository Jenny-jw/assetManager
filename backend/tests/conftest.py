from __future__ import annotations

import os

os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret")
os.environ.setdefault("USE_DB_TRANSACTIONS", "false")

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import threading
from typing import Any

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient
from pymongo import ReturnDocument

import main as app_module
from dependencies.auth import get_current_user
from main import app
from routes import tea as tea_routes
import services.order_service as order_service_module

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
    def __init__(self, lock: threading.Lock | None = None):
        self.docs: dict[ObjectId, dict[str, Any]] = {}
        self._lock = lock

    def create_index(self, *args, **kwargs):
        return None

    def insert_one(self, doc: dict[str, Any], **kwargs):
        if self._lock:
            with self._lock:
                return self._insert_one(doc)
        return self._insert_one(doc)

    def _insert_one(self, doc: dict[str, Any]) -> InsertOneResult:
        doc_id = ObjectId()
        stored_doc = deepcopy(doc)
        stored_doc["_id"] = doc_id
        self.docs[doc_id] = stored_doc
        return InsertOneResult(inserted_id=doc_id)

    def find(
        self,
        filters: dict[str, Any] | None = None,
        projection: dict[str, Any] | None = None,
    ):
        docs = [
            self._apply_projection(deepcopy(doc), projection)
            for doc in self.docs.values()
            if self._matches(doc, filters or {})
        ]
        return FakeCursor(docs)

    def _apply_projection(
        self,
        doc: dict[str, Any],
        projection: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if not projection:
            return doc
        if projection.get("_id") == 0:
            doc.pop("_id", None)
        included = [key for key, value in projection.items() if key != "_id" and value]
        if included:
            projected = {key: doc.get(key) for key in included}
            if projection.get("_id") != 0:
                projected["_id"] = doc.get("_id")
            return projected
        return doc

    def count_documents(self, filters: dict[str, Any] | None = None):
        return sum(
            1 for doc in self.docs.values() if self._matches(doc, filters or {})
        )

    def find_one(self, filters: dict[str, Any], **kwargs):
        for doc in self.docs.values():
            if self._matches(doc, filters):
                return deepcopy(doc)
        return None

    def find_one_and_update(
        self,
        filters: dict[str, Any],
        update: dict[str, Any],
        return_document=None,
        **kwargs,
    ):
        if self._lock:
            with self._lock:
                return self._find_one_and_update(filters, update, return_document)
        return self._find_one_and_update(filters, update, return_document)

    def _find_one_and_update(
        self,
        filters: dict[str, Any],
        update: dict[str, Any],
        return_document=None,
    ):
        for doc_id, doc in self.docs.items():
            if self._matches(doc, filters):
                before = deepcopy(doc)
                if "$inc" in update:
                    for field, delta in update["$inc"].items():
                        doc[field] = doc.get(field, 0) + delta
                if "$set" in update:
                    doc.update(update["$set"])
                if "$unset" in update:
                    for field in update["$unset"]:
                        doc.pop(field, None)
                self.docs[doc_id] = doc
                if return_document == ReturnDocument.BEFORE:
                    return before
                return deepcopy(doc)
        return None

    def update_one(self, filters: dict[str, Any], update: dict[str, Any], **kwargs):
        updated = self.find_one_and_update(filters, update)
        return updated is not None

    def delete_many(self, filters: dict[str, Any], **kwargs):
        to_delete = [
            doc_id
            for doc_id, doc in self.docs.items()
            if self._matches(doc, filters)
        ]
        for doc_id in to_delete:
            del self.docs[doc_id]
        return len(to_delete)

    def delete_one(self, filters: dict[str, Any], **kwargs):
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

            if isinstance(expected, dict):
                value = doc.get(key)
                if "$gte" in expected and (value is None or value < expected["$gte"]):
                    return False
                continue

            if isinstance(expected, ObjectId):
                if doc.get(key) != expected:
                    return False
                continue

            if doc.get(key) != expected:
                return False

        return True

class FakeDB:
    def __init__(self):
        self._lock = threading.Lock()
        self.teas = FakeCollection(self._lock)
        self.users = FakeCollection(self._lock)
        self.orders = FakeCollection(self._lock)
        self.order_items = FakeCollection(self._lock)
        self.stock_movements = FakeCollection(self._lock)

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
    monkeypatch.setattr(order_service_module, "db", fake_db)
    monkeypatch.setenv("USE_DB_TRANSACTIONS", "false")
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
    return seed_orderable_tea(fake_db, quantity=3)

def seed_orderable_tea(
    fake_db: FakeDB,
    *,
    quantity: int = 5,
    price: int = 1200,
    weight: int = 150,
) -> str:
    fake_db.teas.seed(
        {
            "name": "Alishan Oolong",
            "genre": "Oolong",
            "origin": "Alishan",
            "quantity": quantity,
            "price": price,
            "weight": weight,
        }
    )
    return str(next(iter(fake_db.teas.docs)))

TEA_CREATE_PAYLOAD = {
    "name": "Test Tea",
    "genre": "Oolong",
    "origin": "Alishan",
    "quantity": 1,
}