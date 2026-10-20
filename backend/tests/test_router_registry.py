from pathlib import Path

from fastapi.testclient import TestClient

from core.deployment import load_deployment_config, load_personal_preset
from main import create_app

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PROFESSIONAL_PRESET = _REPO_ROOT / "deploy" / "presets" / "professional.yaml"

def _personal_client() -> TestClient:
    return TestClient(create_app(load_personal_preset()))

def _professional_client() -> TestClient:
    return TestClient(create_app(load_deployment_config(_PROFESSIONAL_PRESET)))

def test_personal_registers_health_auth_and_inventory():
    client = _personal_client()
    assert client.get("/health").status_code == 200
    assert client.post("/api/auth/signup", json={}).status_code == 422
    assert client.get("/api/deployment").status_code == 401
    assert client.get("/api/security/me").status_code == 401
    assert client.get("/api/stock/summary").status_code == 401

def test_profit_endpoint_returns_module_disabled_on_personal_app():
    response = _personal_client().get("/api/analytics/profit")
    assert response.status_code == 403
    body = response.json()
    assert body["detail"] == "module_disabled"
    assert body["error"]["code"] == "module_disabled"

def test_orders_endpoint_returns_module_disabled_on_personal_app():
    response = _personal_client().get("/api/orders/")
    assert response.status_code == 403
    body = response.json()
    assert body["detail"] == "module_disabled"
    assert body["error"]["code"] == "module_disabled"

def test_professional_orders_and_profit_require_auth():
    client = _professional_client()
    orders = client.get("/api/orders/")
    assert orders.status_code == 401
    assert orders.json()["error"]["code"] == "not_authenticated"
    profit = client.get("/api/analytics/profit")
    assert profit.status_code == 401
    assert profit.json()["error"]["code"] == "not_authenticated"

def test_default_module_app_matches_personal_preset():
    default = TestClient(create_app())
    personal = _personal_client()
    for path in (
        "/health",
        "/api/stock/summary",
        "/api/orders/",
        "/api/analytics/profit",
        "/api/security/me",
    ):
        assert default.get(path).status_code == personal.get(path).status_code