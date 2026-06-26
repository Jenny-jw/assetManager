from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.db import get_db
from core.deployment import DeploymentConfig, get_deployment, load_personal_preset
from dependencies.auth import get_current_user
from models.stock import Stock
from models.user import User
from routes.stock import router as product_stock_router

_OWNER: dict[str, Any] = {
    "id": "00000000-0000-0000-0000-000000000001",
    "username": "owner1",
    "role": "owner",
    "name": "Owner",
    "email": "owner@example.com",
    "is_active": True,
}

_STOCK_PAYLOAD = {
    "name": "Alishan Oolong",
    "genre": "Oolong",
    "origin": "Alishan",
    "weight_grams": 75,
    "quantity": 2,
    "price_per_jin": 1200,
}

@pytest.fixture
def stock_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    User.__table__.create(bind=engine)
    Stock.__table__.create(bind=engine)
    session_factory = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        User.__table__.drop(bind=engine)
        Stock.__table__.drop(bind=engine)
        engine.dispose()

@pytest.fixture
def personal_deployment() -> DeploymentConfig:
    return load_personal_preset()

@pytest.fixture
def stock_client(
    stock_session: Session,
    personal_deployment: DeploymentConfig,
) -> Generator[TestClient, None, None]:
    app = FastAPI()
    app.include_router(product_stock_router, prefix="/api")

    def override_get_db() -> Generator[Session, None, None]:
        yield stock_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: _OWNER
    app.dependency_overrides[get_deployment] = lambda: personal_deployment
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()

def test_create_stock_returns_201(stock_client: TestClient):
    response = stock_client.post("/api/stock/", json=_STOCK_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Alishan Oolong"
    assert body["weight_grams"] == 75
    assert body["quantity"] == 2
    assert "id" in body
    assert "created_at" in body

def test_create_stock_rejects_invalid_weight_for_personal(stock_client: TestClient):
    response = stock_client.post(
        "/api/stock/",
        json={**_STOCK_PAYLOAD, "weight_grams": 100},
    )

    assert response.status_code == 400
    assert "75 or 150" in response.json()["detail"]

def test_create_stock_requires_owner(stock_session: Session, personal_deployment: DeploymentConfig):
    app = FastAPI()
    app.include_router(product_stock_router, prefix="/api")

    def override_get_db() -> Generator[Session, None, None]:
        yield stock_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_deployment] = lambda: personal_deployment

    with TestClient(app) as client:
        response = client.post("/api/stock/", json=_STOCK_PAYLOAD)

    assert response.status_code == 401

def test_get_stock_returns_active_row(stock_client: TestClient):
    created = stock_client.post("/api/stock/", json=_STOCK_PAYLOAD).json()
    stock_id = created["id"]

    response = stock_client.get(f"/api/stock/{stock_id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Alishan Oolong"

def test_get_stock_returns_404_when_missing(stock_client: TestClient):
    response = stock_client.get(f"/api/stock/{uuid4()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Stock not found"

def test_get_stock_returns_404_when_soft_deleted(stock_client: TestClient, stock_session: Session):
    created = stock_client.post("/api/stock/", json=_STOCK_PAYLOAD).json()
    stock = stock_session.get(Stock, UUID(created["id"]))
    assert stock is not None
    stock.deleted_at = datetime.now(timezone.utc)
    stock_session.commit()

    response = stock_client.get(f"/api/stock/{created['id']}")
    assert response.status_code == 404

def test_get_stock_returns_400_for_invalid_id(stock_client: TestClient):
    response = stock_client.get("/api/stock/not-a-uuid")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid stock id"

def test_list_stocks_returns_empty_page(stock_client: TestClient):
    response = stock_client.get("/api/stock/")

    assert response.status_code == 200
    body = response.json()
    assert body == {"data": [], "page": 1, "limit": 20, "total": 0}

def test_list_stocks_paginates_active_rows(stock_client: TestClient):
    for index in range(3):
        stock_client.post(
            "/api/stock/",
            json={**_STOCK_PAYLOAD, "name": f"Tea {index}"},
        )

    page_one = stock_client.get("/api/stock/", params={"page": 1, "limit": 2})
    page_two = stock_client.get("/api/stock/", params={"page": 2, "limit": 2})

    assert page_one.status_code == 200
    assert page_one.json()["total"] == 3
    assert len(page_one.json()["data"]) == 2
    assert page_two.json()["total"] == 3
    assert len(page_two.json()["data"]) == 1

def test_list_stocks_excludes_soft_deleted(stock_client: TestClient, stock_session: Session):
    created = stock_client.post("/api/stock/", json=_STOCK_PAYLOAD).json()
    stock = stock_session.get(Stock, UUID(created["id"]))
    assert stock is not None
    stock.deleted_at = datetime.now(timezone.utc)
    stock_session.commit()

    response = stock_client.get("/api/stock/")
    assert response.status_code == 200
    assert response.json()["total"] == 0

def test_list_stocks_sorts_by_name_asc(stock_client: TestClient):
    stock_client.post("/api/stock/", json={**_STOCK_PAYLOAD, "name": "Zebra"})
    stock_client.post("/api/stock/", json={**_STOCK_PAYLOAD, "name": "Alpha"})

    response = stock_client.get(
        "/api/stock/",
        params={"sort_by": "name", "sort_direction": "asc"},
    )

    names = [row["name"] for row in response.json()["data"]]
    assert names == ["Alpha", "Zebra"]

def _seed_filter_fixtures(stock_client: TestClient) -> None:
    stock_client.post(
        "/api/stock/",
        json={
            **_STOCK_PAYLOAD,
            "name": "Alishan Oolong",
            "genre": "Oolong",
            "origin": "Alishan",
        },
    )
    stock_client.post(
        "/api/stock/",
        json={
            **_STOCK_PAYLOAD,
            "name": "Sun Moon Black",
            "genre": "Black",
            "origin": "Sun Moon Lake",
        },
    )

def test_list_stocks_filters_by_genre(stock_client: TestClient):
    _seed_filter_fixtures(stock_client)

    response = stock_client.get("/api/stock/", params={"genre": "Oolong"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["data"][0]["name"] == "Alishan Oolong"

def test_list_stocks_filters_by_origin(stock_client: TestClient):
    _seed_filter_fixtures(stock_client)

    response = stock_client.get("/api/stock/", params={"origin": "Sun Moon Lake"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["data"][0]["genre"] == "Black"

def test_list_stocks_search_matches_name(stock_client: TestClient):
    _seed_filter_fixtures(stock_client)

    response = stock_client.get("/api/stock/", params={"search": "alishan"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["data"][0]["name"] == "Alishan Oolong"

def test_list_stocks_combines_genre_and_search(stock_client: TestClient):
    _seed_filter_fixtures(stock_client)

    response = stock_client.get(
        "/api/stock/",
        params={"genre": "Oolong", "search": "Moon"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 0

def test_patch_stock_updates_fields(stock_client: TestClient):
    created = stock_client.post("/api/stock/", json=_STOCK_PAYLOAD).json()

    response = stock_client.patch(
        f"/api/stock/{created['id']}",
        json={"name": "Renamed Oolong", "quantity": 0},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Renamed Oolong"
    assert body["quantity"] == 0
    assert body["updated_at"] is not None

def test_patch_stock_clears_optional_strings(stock_client: TestClient):
    created = stock_client.post("/api/stock/", json=_STOCK_PAYLOAD).json()

    response = stock_client.patch(
        f"/api/stock/{created['id']}",
        json={"origin": "", "comment": ""},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["origin"] is None
    assert body["comment"] is None

def test_patch_stock_returns_400_when_empty(stock_client: TestClient):
    created = stock_client.post("/api/stock/", json=_STOCK_PAYLOAD).json()

    response = stock_client.patch(f"/api/stock/{created['id']}", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "No fields to update"

def test_patch_stock_returns_404_when_missing(stock_client: TestClient):
    response = stock_client.patch(f"/api/stock/{uuid4()}", json={"name": "Nope"})
    assert response.status_code == 404

def test_patch_stock_rejects_invalid_weight_for_personal(stock_client: TestClient):
    created = stock_client.post("/api/stock/", json=_STOCK_PAYLOAD).json()

    response = stock_client.patch(
        f"/api/stock/{created['id']}",
        json={"weight_grams": 100},
    )

    assert response.status_code == 400
    assert "75 or 150" in response.json()["detail"]

def test_delete_stock_soft_deletes_row(stock_client: TestClient):
    created = stock_client.post("/api/stock/", json=_STOCK_PAYLOAD).json()
    stock_id = created["id"]

    response = stock_client.delete(f"/api/stock/{stock_id}")

    assert response.status_code == 200
    assert response.json() == {"message": "Stock deleted"}
    assert stock_client.get(f"/api/stock/{stock_id}").status_code == 404

def test_delete_stock_hides_row_from_list(stock_client: TestClient):
    created = stock_client.post("/api/stock/", json=_STOCK_PAYLOAD).json()
    stock_client.delete(f"/api/stock/{created['id']}")

    response = stock_client.get("/api/stock/")
    assert response.status_code == 200
    assert response.json()["total"] == 0

def test_delete_stock_returns_404_when_missing(stock_client: TestClient):
    response = stock_client.delete(f"/api/stock/{uuid4()}")
    assert response.status_code == 404

def test_delete_stock_returns_404_when_already_deleted(stock_client: TestClient):
    created = stock_client.post("/api/stock/", json=_STOCK_PAYLOAD).json()
    stock_id = created["id"]
    stock_client.delete(f"/api/stock/{stock_id}")

    response = stock_client.delete(f"/api/stock/{stock_id}")
    assert response.status_code == 404

def test_delete_stock_returns_400_for_invalid_id(stock_client: TestClient):
    response = stock_client.delete("/api/stock/not-a-uuid")
    assert response.status_code == 400
