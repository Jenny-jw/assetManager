# TEMPORARY — v1 routes (tea, auth, orders) still import this module.
# Product branch uses PostgreSQL via core/db.py. Delete mongo_legacy when those
# routes are rewritten or removed (P0 #6+).
from pymongo import MongoClient
import os

import core.env  # noqa: F401

MONGO_URI = os.getenv("MONGO_URI")
_DB_NAME = "assetManager"

_client: MongoClient | None = None

def get_mongo_client() -> MongoClient | None:
    global _client
    if not MONGO_URI:
        return None
    if _client is None:
        _client = MongoClient(MONGO_URI)
    return _client

def get_mongo_db():
    mongo_client = get_mongo_client()
    if mongo_client is None:
        return None
    return mongo_client[_DB_NAME]

class _MongoClientProxy:
    def __getattr__(self, name: str):
        mongo_client = get_mongo_client()
        if mongo_client is None:
            raise RuntimeError("MONGO_URI is not set; legacy Mongo routes are disabled")
        return getattr(mongo_client, name)

class _MongoDBProxy:
    def __getattr__(self, name: str):
        database = get_mongo_db()
        if database is None:
            raise RuntimeError("MONGO_URI is not set; legacy Mongo routes are disabled")
        return getattr(database, name)

client = _MongoClientProxy()
db = _MongoDBProxy()
