from tests.conftest import seed_orderable_tea


def test_user_can_place_order_and_stock_is_reduced(client_user, fake_db):
    tea_id = seed_orderable_tea(fake_db, quantity=5, price=1200)

    response = client_user.post(
        "/api/orders/",
        json={"items": [{"tea_id": tea_id, "quantity": 2}]},
    )

    assert response.status_code == 201
    body = response.json()
    # 150g pkg, 1200/斤 → 300/pkg × 2 packages = 600
    assert body["total_amount"] == 600
    assert body["items"][0]["unit_price"] == 300
    assert len(body["items"]) == 1
    assert body["items"][0]["tea_id"] == tea_id

    tea = fake_db.teas.find_one({"_id": next(iter(fake_db.teas.docs))})
    assert tea["quantity"] == 3
    assert len(fake_db.stock_movements.docs) == 1
    movement = next(iter(fake_db.stock_movements.docs.values()))
    assert movement["delta"] == -2
    assert movement["reason"] == "order"


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
