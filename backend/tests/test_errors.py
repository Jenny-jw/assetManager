from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from core.errors import ErrorCode, api_error, register_exception_handlers

def _app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    return app

def test_api_error_envelope_uses_stable_code():
    app = _app()

    @app.get("/denied")
    def denied():
        raise api_error(403, ErrorCode.module_disabled)

    response = TestClient(app).get("/denied")

    assert response.status_code == 403
    body = response.json()
    assert body["detail"] == "module_disabled"
    assert body["error"]["code"] == "module_disabled"
    assert "not enabled" in body["error"]["message"].lower()
    assert "request_id" in body["error"]

def test_api_error_can_override_message():
    app = _app()

    @app.get("/weight")
    def bad_weight():
        raise api_error(400, ErrorCode.invalid_weight, message="weight must be 75 or 150")

    response = TestClient(app).get("/weight")

    assert response.status_code == 400
    body = response.json()
    assert body["detail"] == "invalid_weight"
    assert body["error"]["code"] == "invalid_weight"
    assert "75 or 150" in body["error"]["message"]

def test_legacy_http_exception_keeps_detail_and_uses_http_error_code():
    app = _app()

    @app.get("/legacy")
    def legacy():
        raise HTTPException(status_code=400, detail="Some legacy message")

    response = TestClient(app).get("/legacy")

    assert response.status_code == 400
    body = response.json()
    assert body["detail"] == "Some legacy message"
    assert body["error"]["code"] == "http_error"
    assert body["error"]["message"] == "Some legacy message"

def test_plain_error_code_detail_is_recognized():
    app = _app()

    @app.get("/trial")
    def trial():
        raise HTTPException(status_code=403, detail="trial_expired")

    response = TestClient(app).get("/trial")

    assert response.status_code == 403
    body = response.json()
    assert body["detail"] == "trial_expired"
    assert body["error"]["code"] == "trial_expired"
    assert "expired" in body["error"]["message"].lower()

def test_validation_error_envelope():
    app = _app()

    @app.get("/items")
    def items(limit: int):
        return {"limit": limit}

    response = TestClient(app).get("/items")

    assert response.status_code == 422
    body = response.json()
    assert isinstance(body["detail"], list)
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["details"] == body["detail"]
