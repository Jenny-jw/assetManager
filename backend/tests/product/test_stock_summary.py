from __future__ import annotations

from core.tea_pricing import line_total_value

pytest_plugins = ["tests.product.test_stock_api"]

from tests.product.test_stock_api import _STOCK_PAYLOAD

def test_stock_summary_empty(stock_client):
    response = stock_client.get("/api/stock/summary")

    assert response.status_code == 200
    assert response.json() == {
        "total_assets": 0,
        "total_packages": 0,
        "total_weight_grams": 0,
        "total_value": 0,
        "by_origin": {},
        "by_genre": {},
    }

def test_stock_summary_aggregates_active_inventory(stock_client):
    stock_client.post("/api/stock/", json=_STOCK_PAYLOAD)
    stock_client.post(
        "/api/stock/",
        json={
            **_STOCK_PAYLOAD,
            "name": "Sun Moon Black",
            "genre": "Black",
            "origin": "Sun Moon Lake",
            "weight_grams": 150,
            "quantity": 1,
            "price_per_jin": 900,
        },
    )

    response = stock_client.get("/api/stock/summary")
    body = response.json()

    assert response.status_code == 200
    assert body["total_assets"] == 2
    assert body["total_packages"] == 3
    assert body["total_weight_grams"] == (75 * 2) + (150 * 1)
    expected_value = line_total_value(1200, 75, 2) + line_total_value(900, 150, 1)
    assert body["total_value"] == expected_value
    assert body["by_origin"] == {"Alishan": 1, "Sun Moon Lake": 1}
    assert body["by_genre"] == {"Oolong": 1, "Black": 1}

def test_stock_summary_excludes_soft_deleted(stock_client):
    created = stock_client.post("/api/stock/", json=_STOCK_PAYLOAD).json()
    stock_client.delete(f"/api/stock/{created['id']}")

    response = stock_client.get("/api/stock/summary")
    assert response.json()["total_assets"] == 0
