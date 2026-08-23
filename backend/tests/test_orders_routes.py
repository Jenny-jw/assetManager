from tests.mongo_fake import seed_orderable_tea

def test_personal_app_returns_module_disabled_for_orders(client_owner, fake_db):
    tea_id = seed_orderable_tea(fake_db)
    response = client_owner.post(
        "/api/orders/",
        json={"items": [{"stock_id": tea_id, "quantity": 1}]},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "module_disabled"

def test_professional_app_registers_orders_route(client_owner_professional, fake_db):
    response = client_owner_professional.get("/api/orders/")
    assert response.status_code != 404
