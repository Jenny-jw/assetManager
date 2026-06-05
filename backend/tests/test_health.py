from pymongo.errors import PyMongoError

class FakeAdmin:
    def __init__(self, *, fail: bool = False):
        self.fail = fail

    def command(self, cmd: str):
        if self.fail:
            raise PyMongoError("connection failed")
        if cmd == "ping":
            return {"ok": 1}
        raise ValueError(f"unexpected command: {cmd}")

class FakeMongoClient:
    def __init__(self, *, fail: bool = False):
        self.admin = FakeAdmin(fail=fail)

def test_health_returns_ok_without_db(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_ready_returns_200_when_db_pings(client, monkeypatch):
    monkeypatch.setattr(
        "routes.health.client",
        FakeMongoClient(),
    )
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}

def test_ready_returns_503_when_db_unreachable(client, monkeypatch):
    monkeypatch.setattr(
        "routes.health.client",
        FakeMongoClient(fail=True),
    )
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"