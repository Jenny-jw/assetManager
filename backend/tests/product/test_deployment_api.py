from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from core.deployment import load_deployment_config, load_personal_preset
from main import create_app

_REPO_ROOT = Path(__file__).resolve().parents[3]

def test_get_deployment_personal_returns_orders_disabled():
    app = create_app(load_personal_preset())
    client = TestClient(app)

    response = client.get("/api/deployment")

    assert response.status_code == 200
    body = response.json()
    assert body["edition"] == "personal"
    assert body["locale"] in {"zh-TW", "en"}
    assert body["modules"]["orders"] is False
    assert "pending_orders" not in body["dashboard_layout"]

def test_get_deployment_professional_includes_pending_orders():
    professional = load_deployment_config(_REPO_ROOT / "deploy" / "presets" / "professional.yaml")
    app = create_app(professional)
    client = TestClient(app)

    response = client.get("/api/deployment")

    assert response.status_code == 200
    body = response.json()
    assert body["edition"] == "professional"
    assert body["modules"]["orders"] is True
    assert "pending_orders" in body["dashboard_layout"]
