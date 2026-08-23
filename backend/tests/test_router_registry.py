from pathlib import Path

from fastapi.testclient import TestClient

from core.deployment import load_deployment_config, load_personal_preset
from core.router_registry import route_paths
from main import create_app

_REPO_ROOT = Path(__file__).resolve().parents[2]

def test_personal_deployment_registers_inventory_and_orders_routes():
    app = create_app(load_personal_preset())
    paths = route_paths(app)
    assert any(path.startswith("/api/stock") for path in paths)
    assert "/api/stock/summary" in paths
    assert any(path.startswith("/api/orders") for path in paths)

def test_personal_deployment_always_registers_auth_and_health():
    app = create_app(load_personal_preset())
    paths = route_paths(app)
    assert "/health" in paths
    assert "/api/auth/signup" in paths
    assert "/api/deployment" in paths
    assert "/api/security/me" in paths

def test_professional_deployment_registers_orders():
    app = create_app(load_deployment_config(_REPO_ROOT / "deploy" / "presets" / "professional.yaml"))
    paths = route_paths(app)
    assert any(path.startswith("/api/orders") for path in paths)
    assert "/api/analytics/profit" in paths

def test_profit_endpoint_returns_module_disabled_on_personal_app():
    app = create_app(load_personal_preset())
    client = TestClient(app)
    response = client.get("/api/analytics/profit")
    assert response.status_code == 403
    body = response.json()
    assert body["detail"] == "module_disabled"
    assert body["error"]["code"] == "module_disabled"

def test_orders_endpoint_returns_module_disabled_on_personal_app():
    app = create_app(load_personal_preset())
    client = TestClient(app)
    response = client.get("/api/orders/")
    assert response.status_code == 403
    body = response.json()
    assert body["detail"] == "module_disabled"
    assert body["error"]["code"] == "module_disabled"

def test_orders_endpoint_reachable_when_orders_module_enabled():
    app = create_app(load_deployment_config(_REPO_ROOT / "deploy" / "presets" / "professional.yaml"))
    client = TestClient(app)
    response = client.get("/api/orders/")
    # Module check passes; owner auth then rejects unauthenticated request.
    assert response.status_code == 401
    body = response.json()
    assert body["detail"] == "not_authenticated"
    assert body["error"]["code"] == "not_authenticated"

def test_default_module_app_matches_personal_preset():
    default_app = create_app()
    personal_app = create_app(load_personal_preset())
    assert route_paths(default_app) == route_paths(personal_app)
