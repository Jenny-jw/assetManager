from datetime import datetime, timezone

import pytest
from bson import ObjectId

def test_create_tea_rejects_invalid_package_weight(client):
    response = client.post(
        "/api/tea/",
        json={
            "name": "Invalid Weight Tea",
            "genre": "Oolong",
            "weight": 100,
            "quantity": 1,
            "price": 1200,
        },
    )

    assert response.status_code == 422

@pytest.mark.parametrize("field", ["weight", "quantity"])
def test_create_tea_rejects_missing_package_field(client, field):
    payload = {
        "name": "Incomplete Tea",
        "genre": "Oolong",
        "weight": 150,
        "quantity": 1,
    }
    del payload[field]

    response = client.post("/api/tea/", json=payload)

    assert response.status_code == 422

def test_create_and_update_tea(client):
    create_response = client.post(
        "/api/tea/",
        json={
            "name": "Alishan Oolong",
            "genre": "Oolong",
            "origin": "Alishan",
            "weight": 150,
            "quantity": 3,
            "score": 88,
            "price": 1200,
        },
    )

    assert create_response.status_code == 200
    created = create_response.json()
    assert created["id"]
    assert created["name"] == "Alishan Oolong"

    update_response = client.patch(
        f"/api/tea/{created['id']}",
        json={"quantity": 5, "score": 91},
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["quantity"] == 5
    assert updated["score"] == 91

def test_create_tea_sets_owner_id_and_ignores_client_value(client, admin_user, fake_db):
    response = client.post(
        "/api/tea/",
        json={
            "name": "Owned Tea",
            "genre": "Oolong",
            "weight": 150,
            "quantity": 1,
            "owner_id": str(ObjectId()),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert ObjectId.is_valid(body["owner_id"])
    assert body["owner_id"] == admin_user["id"]
    assert fake_db.teas.docs[ObjectId(body["id"])]["owner_id"] == admin_user["id"]

def test_patch_does_not_change_owner_id(client, admin_user):
    created = client.post(
        "/api/tea/",
        json={"name": "Owned Tea", "genre": "Oolong", "weight": 150, "quantity": 1},
    )
    tea_id = created.json()["id"]

    response = client.patch(
        f"/api/tea/{tea_id}",
        json={"owner_id": str(ObjectId()), "quantity": 2},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["owner_id"] == admin_user["id"]
    assert body["quantity"] == 2

def test_create_tea_ignores_client_created_at(client, fake_db):
    response = client.post(
        "/api/tea/",
        json={
            "name": "Timed Tea",
            "genre": "Oolong",
            "weight": 150,
            "quantity": 1,
            "created_at": "2000-01-01T00:00:00Z",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert not body["created_at"].startswith("2000-01-01")
    stored = fake_db.teas.docs[ObjectId(body["id"])]["created_at"]
    assert stored.year != 2000

def test_patch_ignores_client_owner_and_timestamps(client, admin_user, fake_db):
    created = client.post(
        "/api/tea/",
        json={
            "name": "Timed Tea",
            "genre": "Oolong",
            "weight": 150,
            "quantity": 1,
        },
    )
    created_body = created.json()
    tea_id = created_body["id"]

    response = client.patch(
        f"/api/tea/{tea_id}",
        json={
            "quantity": 4,
            "owner_id": str(ObjectId()),
            "created_at": "1999-01-01T00:00:00Z",
            "updated_at": "1999-01-01T00:00:00Z",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["quantity"] == 4
    assert body["owner_id"] == admin_user["id"]
    assert body["created_at"] == created_body["created_at"]
    assert not str(body["updated_at"]).startswith("1999")
    stored = fake_db.teas.docs[ObjectId(tea_id)]
    assert stored["updated_at"].year != 1999

def test_existing_tea_without_owner_id_stays_unset(client, fake_db):
    fake_db.teas.seed({"name": "Legacy Tea", "genre": "Green", "quantity": 1})

    response = client.get("/api/tea/")

    assert response.status_code == 200
    assert response.json()["data"][0]["owner_id"] is None
    assert next(iter(fake_db.teas.docs.values())).get("owner_id") is None

def test_patch_clears_optional_string_fields(client):
    create_response = client.post(
        "/api/tea/",
        json={
            "name": "Alishan Oolong",
            "genre": "Oolong",
            "origin": "Japan",
            "producer": "Farmer Tan",
            "comment": "Floral",
            "weight": 150,
            "quantity": 3,
            "price": 1200,
        },
    )

    assert create_response.status_code == 200
    tea_id = create_response.json()["id"]

    clear_origin = client.patch(f"/api/tea/{tea_id}", json={"origin": None})
    assert clear_origin.status_code == 200
    assert clear_origin.json().get("origin") is None

    restore_origin = client.patch(f"/api/tea/{tea_id}", json={"origin": "Japan"})
    assert restore_origin.status_code == 200

    clear_via_empty = client.patch(f"/api/tea/{tea_id}", json={"origin": ""})
    assert clear_via_empty.status_code == 200
    assert clear_via_empty.json().get("origin") is None

def test_patch_allows_zero_packages(client):
    create_response = client.post(
        "/api/tea/",
        json={
            "name": "Alishan Oolong",
            "genre": "Oolong",
            "weight": 150,
            "quantity": 3,
            "price": 1200,
        },
    )
    tea_id = create_response.json()["id"]

    response = client.patch(f"/api/tea/{tea_id}", json={"quantity": 0})

    assert response.status_code == 200
    assert response.json()["quantity"] == 0

def test_tea_summary_aggregates_entire_inventory(client, fake_db):
    fake_db.teas.seed(
        {
            "name": "Alishan Oolong",
            "genre": "Oolong",
            "origin": "Taiwan",
            "quantity": 2,
            "weight": 150,
            "price": 1200,
        },
        {
            "name": "Sencha",
            "genre": "Green",
            "origin": "Japan",
            "quantity": 1,
            "weight": 75,
            "price": 900,
        },
    )

    response = client.get("/api/tea/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["total_assets"] == 2
    assert body["total_packages"] == 3
    assert body["total_weight_grams"] == 375
    assert body["total_value"] == 712
    assert body["by_origin"] == {"Japan": 1, "Taiwan": 1}
    assert body["by_genre"] == {"Green": 1, "Oolong": 1}

def test_list_teas_pagination_returns_second_page(client, fake_db):
    for index in range(32):
        fake_db.teas.seed(
            {
                "name": f"Tea {index}",
                "genre": "Oolong",
                "quantity": 1,
                "price": 1000,
                "score": index,
            },
        )

    page_one = client.get(
        "/api/tea/",
        params={"page": 1, "limit": 20, "sort_by": "score", "sort_direction": "asc"},
    )
    page_two = client.get(
        "/api/tea/",
        params={"page": 2, "limit": 20, "sort_by": "score", "sort_direction": "asc"},
    )

    assert page_one.status_code == 200
    assert page_two.status_code == 200
    assert page_one.json()["total"] == 32
    assert len(page_one.json()["data"]) == 20
    assert len(page_two.json()["data"]) == 12

def test_list_teas_supports_pagination_filtering_and_sorting(client, fake_db):
    fake_db.teas.seed(
        {
            "name": "Alishan Oolong",
            "genre": "Oolong",
            "origin": "Alishan",
            "quantity": 3,
            "score": 88,
            "price": 1200,
        },
        {
            "name": "Lishan Oolong",
            "genre": "Oolong",
            "origin": "Lishan",
            "quantity": 1,
            "score": 95,
            "price": 1800,
        },
        {
            "name": "Sun Moon Lake Black Tea",
            "genre": "Black",
            "origin": "Nantou",
            "quantity": 7,
            "score": 82,
            "price": 900,
        },
    )

    response = client.get(
        "/api/tea/",
        params={
            "genre": "Oolong",
            "page": 1,
            "limit": 1,
            "sort_by": "score",
            "sort_direction": "desc",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["page"] == 1
    assert body["limit"] == 1
    assert body["total"] == 2
    assert len(body["data"]) == 1
    assert body["data"][0]["name"] == "Lishan Oolong"

def test_list_teas_supports_text_search(client, fake_db):
    fake_db.teas.seed(
        {
            "name": "Alishan Oolong",
            "genre": "Oolong",
            "origin": "Alishan",
            "comment": "floral aroma",
            "created_at": datetime.now(timezone.utc),
        },
        {
            "name": "Everyday Black Tea",
            "genre": "Black",
            "origin": "Nantou",
            "comment": "malty body",
            "created_at": datetime.now(timezone.utc),
        },
    )

    response = client.get("/api/tea/", params={"search": "floral"})

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["data"][0]["name"] == "Alishan Oolong"

def test_delete_tea(client, fake_db):
    fake_db.teas.seed(
        {
            "name": "Alishan Oolong",
            "genre": "Oolong",
            "origin": "Alishan",
            "created_at": datetime.now(timezone.utc),
        }
    )
    tea_id = str(next(iter(fake_db.teas.docs)))

    response = client.delete(f"/api/tea/{tea_id}")

    assert response.status_code == 200
    assert response.json() == {"message": "Tea deleted"}
    assert fake_db.teas.find_one({"_id": next(iter(fake_db.teas.docs), None)}) is None