"""Transaction-safe stock fulfillment — approve flow and concurrency."""
from __future__ import annotations

import threading

import pytest
from bson import ObjectId
from fastapi import HTTPException

import services.order_service as order_service_module
from schemas.order import OrderCreate, OrderItemCreate
from services.order_service import approve_order, place_order
from tests.conftest import _make_user, seed_orderable_tea

@pytest.fixture
def order_db(monkeypatch, fake_db):
    monkeypatch.setattr(order_service_module, "db", fake_db)
    monkeypatch.setenv("USE_DB_TRANSACTIONS", "false")
    return fake_db

def _place(fake_db, tea_id: str, quantity: int, user: dict | None = None) -> str:
    user = user or _make_user("user")
    order = place_order(
        OrderCreate(items=[OrderItemCreate(tea_id=tea_id, quantity=quantity)]),
        user,
    )
    return order["id"]

def test_approve_succeeds_when_stock_sufficient(order_db):
    tea_id = seed_orderable_tea(order_db, quantity=5)
    order_id = _place(order_db, tea_id, 2)
    admin = _make_user("admin")

    result = approve_order(order_id, admin)

    assert result["status"] == "confirmed"
    tea = order_db.teas.find_one({"_id": ObjectId(tea_id)})
    assert tea["quantity"] == 3
    assert len(order_db.stock_movements.docs) == 1

def test_approve_fails_409_when_stock_insufficient(order_db):
    tea_id = seed_orderable_tea(order_db, quantity=5)
    order_id = _place(order_db, tea_id, 2)
    tea_oid = ObjectId(tea_id)
    order_db.teas.docs[tea_oid]["quantity"] = 1
    admin = _make_user("admin")

    with pytest.raises(HTTPException) as exc:
        approve_order(order_id, admin)

    assert exc.value.status_code == 409
    tea = order_db.teas.find_one({"_id": tea_oid})
    assert tea["quantity"] == 1
    order = order_db.orders.find_one({"_id": ObjectId(order_id)})
    assert order["status"] == "pending"
    assert len(order_db.stock_movements.docs) == 0

def test_double_approve_same_order_only_fulfills_once(order_db):
    tea_id = seed_orderable_tea(order_db, quantity=5)
    order_id = _place(order_db, tea_id, 2)
    admin = _make_user("admin")

    approve_order(order_id, admin)

    with pytest.raises(HTTPException) as exc:
        approve_order(order_id, admin)

    assert exc.value.status_code == 409
    tea = order_db.teas.find_one({"_id": ObjectId(tea_id)})
    assert tea["quantity"] == 3
    assert len(order_db.stock_movements.docs) == 1

def test_concurrent_approvals_cannot_oversell(order_db):
    """Two pending orders (2 pkgs each) on stock of 3 — only one may succeed."""
    tea_id = seed_orderable_tea(order_db, quantity=3)
    order_a = _place(order_db, tea_id, 2)
    order_b = _place(order_db, tea_id, 2)
    admin = _make_user("admin")
    results: list[int | str] = [None, None]

    def try_approve(order_id: str, slot: int) -> None:
        try:
            approve_order(order_id, admin)
            results[slot] = "ok"
        except HTTPException as exc:
            results[slot] = exc.status_code

    threads = [
        threading.Thread(target=try_approve, args=(order_a, 0)),
        threading.Thread(target=try_approve, args=(order_b, 1)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert results.count("ok") == 1
    assert results.count(409) == 1

    tea = order_db.teas.find_one({"_id": ObjectId(tea_id)})
    assert tea["quantity"] == 1
    assert len(order_db.stock_movements.docs) == 1

def test_multi_item_approve_rolls_back_when_second_line_insufficient(order_db):
    """If line 2 cannot be reserved, line 1 stock and order status are rolled back."""
    tea_a = seed_orderable_tea(order_db, quantity=5, price=1200, weight=150)
    tea_b_insert = order_db.teas.insert_one(
        {
            "name": "Second Tea",
            "genre": "Green",
            "quantity": 5,
            "price": 600,
            "weight": 75,
        }
    )
    tea_b_id = str(tea_b_insert.inserted_id)

    user = _make_user("user")
    order = place_order(
        OrderCreate(
            items=[
                OrderItemCreate(tea_id=tea_a, quantity=2),
                OrderItemCreate(tea_id=tea_b_id, quantity=2),
            ]
        ),
        user,
    )
    order_id = order["id"]
    order_db.teas.docs[ObjectId(tea_b_id)]["quantity"] = 1
    admin = _make_user("admin")

    with pytest.raises(HTTPException) as exc:
        approve_order(order_id, admin)

    assert exc.value.status_code == 409
    assert order_db.teas.find_one({"_id": ObjectId(tea_a)})["quantity"] == 5
    assert order_db.teas.find_one({"_id": ObjectId(tea_b_id)})["quantity"] == 1
    assert order_db.orders.find_one({"_id": ObjectId(order_id)})["status"] == "pending"
    assert len(order_db.stock_movements.docs) == 0
