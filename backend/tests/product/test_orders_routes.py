from tests.conftest import seed_orderable_tea

def test_personal_app_returns_404_for_orders(client_owner, fake_db):
    tea_id = seed_orderable_tea(fake_db)
    response = client_owner.post(
        "/api/orders/",
        json={"items": [{"tea_id": tea_id, "quantity": 1}]},
    )
    assert response.status_code == 404

def test_professional_app_registers_orders_route(client_owner_professional, fake_db):
    response = client_owner_professional.get("/api/orders/")
    assert response.status_code != 404
