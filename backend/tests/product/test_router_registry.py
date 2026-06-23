from pathlib import Path

from fastapi.testclient import TestClient

from core.deployment import load_deployment_config, load_personal_preset
from core.router_registry import route_paths
from main import create_app

_REPO_ROOT = Path(__file__).resolve().parents[3]

def test_personal_deployment_registers_inventory_not_orders():
    app = create_app(load_personal_preset())
    paths = route_paths(app)
    assert any(path.startswith("/api/tea") for path in paths)
    assert not any(path.startswith("/api/orders") for path in paths)

def test_personal_deployment_always_registers_auth_and_health():
    app = create_app(load_personal_preset())
    paths = route_paths(app)
    assert "/health" in paths
    assert "/api/auth/signup" in paths
    assert "/api/security/me" in paths

def test_professional_deployment_registers_orders():
    app = create_app(load_deployment_config(_REPO_ROOT / "deploy" / "presets" / "professional.yaml"))
    paths = route_paths(app)
    assert any(path.startswith("/api/orders") for path in paths)

def test_orders_endpoint_not_found_on_personal_app():
    app = create_app(load_personal_preset())
    client = TestClient(app)
    response = client.get("/api/orders/")
    assert response.status_code == 404

def test_default_module_app_matches_personal_preset():
    default_app = create_app()
    personal_app = create_app(load_personal_preset())
    assert route_paths(default_app) == route_paths(personal_app)
