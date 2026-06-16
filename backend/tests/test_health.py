from pymongo.errors import PyMongoError
from sqlalchemy.exc import SQLAlchemyError

from core.db import ping_postgres

def test_health_returns_ok_without_db(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_ready_returns_200_when_postgres_pings(client, monkeypatch):
    monkeypatch.setattr("routes.health.ping_postgres", lambda: None)
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}

def test_ready_returns_503_when_postgres_unreachable(client, monkeypatch):
    def _fail():
        raise SQLAlchemyError("connection failed")

    monkeypatch.setattr("routes.health.ping_postgres", _fail)
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
