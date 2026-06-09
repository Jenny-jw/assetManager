from dependencies.auth import get_current_user
from main import app
from tests.conftest import _make_user, seed_orderable_tea

def _use_admin_auth() -> None:
    app.dependency_overrides[get_current_user] = lambda: _make_user("admin")

def test_user_place_order_creates_pending_without_stock_change(client_user, fake_db):
    tea_id = seed_orderable_tea(fake_db, quantity=5, price=1200)

    response = client_user.post(
        "/api/orders/",
        json={"items": [{"tea_id": tea_id, "quantity": 2}]},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["total_amount"] == 600
    assert body["items"][0]["unit_price"] == 300
    assert len(body["items"]) == 1

    tea = fake_db.teas.find_one({"_id": next(iter(fake_db.teas.docs))})
    assert tea["quantity"] == 5
    assert len(fake_db.stock_movements.docs) == 0

def test_admin_approve_order_reduces_stock(client, client_user, fake_db):
    tea_id = seed_orderable_tea(fake_db, quantity=5, price=1200)
    placed = client_user.post(
        "/api/orders/",
        json={"items": [{"tea_id": tea_id, "quantity": 2}]},
    )
    order_id = placed.json()["id"]
    _use_admin_auth()

    response = client.patch(f"/api/orders/{order_id}/approve")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "confirmed"

    tea = fake_db.teas.find_one({"_id": next(iter(fake_db.teas.docs))})
    assert tea["quantity"] == 3
    assert len(fake_db.stock_movements.docs) == 1

def test_admin_reject_order_does_not_reduce_stock(client, client_user, fake_db):
    tea_id = seed_orderable_tea(fake_db, quantity=5, price=1200)
    placed = client_user.post(
        "/api/orders/",
        json={"items": [{"tea_id": tea_id, "quantity": 2}]},
    )
    order_id = placed.json()["id"]
    _use_admin_auth()

    response = client.patch(f"/api/orders/{order_id}/reject")

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"

    tea = fake_db.teas.find_one({"_id": next(iter(fake_db.teas.docs))})
    assert tea["quantity"] == 5
    assert len(fake_db.stock_movements.docs) == 0

def test_user_cannot_approve_order(client_user, fake_db):
    tea_id = seed_orderable_tea(fake_db)
    placed = client_user.post(
        "/api/orders/",
        json={"items": [{"tea_id": tea_id, "quantity": 1}]},
    )
    order_id = placed.json()["id"]

    response = client_user.patch(f"/api/orders/{order_id}/approve")
    assert response.status_code == 403

def test_approve_fails_when_stock_insufficient_at_approval(client, client_user, fake_db):
    tea_id = seed_orderable_tea(fake_db, quantity=5, price=1200)
    placed = client_user.post(
        "/api/orders/",
        json={"items": [{"tea_id": tea_id, "quantity": 2}]},
    )
    order_id = placed.json()["id"]

    tea_oid = next(iter(fake_db.teas.docs))
    fake_db.teas.docs[tea_oid]["quantity"] = 1
    _use_admin_auth()

    response = client.patch(f"/api/orders/{order_id}/approve")
    assert response.status_code == 409

def test_guest_cannot_place_order(client_guest, fake_db):
    tea_id = seed_orderable_tea(fake_db)
    response = client_guest.post(
        "/api/orders/",
        json={"items": [{"tea_id": tea_id, "quantity": 1}]},
    )
    assert response.status_code == 403

def test_order_rejects_tea_without_package_weight(client_user, fake_db):
    tea_id = seed_orderable_tea(fake_db)
    tea_oid = next(iter(fake_db.teas.docs))
    fake_db.teas.docs[tea_oid]["weight"] = None

    response = client_user.post(
        "/api/orders/",
        json={"items": [{"tea_id": tea_id, "quantity": 1}]},
    )
    assert response.status_code == 400

def test_insufficient_stock_returns_409(client_user, fake_db):
    tea_id = seed_orderable_tea(fake_db, quantity=1, price=900)
    response = client_user.post(
        "/api/orders/",
        json={"items": [{"tea_id": tea_id, "quantity": 3}]},
    )
    assert response.status_code == 409

def test_user_can_list_own_orders(client_user, fake_db):
    tea_id = seed_orderable_tea(fake_db)
    client_user.post("/api/orders/", json={"items": [{"tea_id": tea_id, "quantity": 1}]})

    response = client_user.get("/api/orders/")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["data"][0]["items"][0]["tea_name"] == "Alishan Oolong"
    assert body["data"][0]["status"] == "pending"

def test_admin_can_list_pending_orders(client, client_user, fake_db):
    tea_id = seed_orderable_tea(fake_db)
    client_user.post("/api/orders/", json={"items": [{"tea_id": tea_id, "quantity": 1}]})
    _use_admin_auth()

    response = client.get("/api/orders/", params={"status": "pending"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["data"][0]["status"] == "pending"

def test_pending_order_reflects_renamed_tea(client, client_user, fake_db):
    tea_id = seed_orderable_tea(fake_db)
    client_user.post("/api/orders/", json={"items": [{"tea_id": tea_id, "quantity": 1}]})

    tea_oid = next(iter(fake_db.teas.docs))
    fake_db.teas.docs[tea_oid]["name"] = "Renamed Oolong"
    _use_admin_auth()

    response = client.get("/api/orders/", params={"status": "pending"})
    assert response.status_code == 200
    assert response.json()["data"][0]["items"][0]["tea_name"] == "Renamed Oolong"
    assert response.json()["data"][0]["items"][0]["tea_available"] is True

def test_pending_order_marks_deleted_tea_unavailable(client, client_user, fake_db):
    tea_id = seed_orderable_tea(fake_db)
    placed = client_user.post(
        "/api/orders/",
        json={"items": [{"tea_id": tea_id, "quantity": 1}]},
    )
    order_id = placed.json()["id"]

    fake_db.teas.delete_one({"_id": next(iter(fake_db.teas.docs))})
    _use_admin_auth()

    response = client.get("/api/orders/", params={"status": "pending"})
    assert response.status_code == 200
    item = response.json()["data"][0]["items"][0]
    assert item["tea_name"] == "Alishan Oolong"
    assert item["tea_available"] is False

    approve = client.patch(f"/api/orders/{order_id}/approve")
    assert approve.status_code == 409

def test_user_cannot_read_other_users_order(client_user, fake_db):
    from datetime import datetime, timezone
    from bson import ObjectId

    order_id = ObjectId()
    now = datetime.now(timezone.utc)
    fake_db.orders.docs[order_id] = {
        "_id": order_id,
        "user_id": "someone-else",
        "status": "confirmed",
        "total_amount": 1200,
        "created_at": now,
        "updated_at": now,
    }

    response = client_user.get(f"/api/orders/{order_id}")
    assert response.status_code == 403
