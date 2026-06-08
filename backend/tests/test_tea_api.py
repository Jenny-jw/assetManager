from datetime import datetime, timezone

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

def test_create_and_update_tea(client):
    create_response = client.post(
        "/api/tea/",
        json={
            "name": "Alishan Oolong",
            "genre": "Oolong",
            "origin": "Alishan",
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

def test_patch_clears_optional_string_fields(client):
    create_response = client.post(
        "/api/tea/",
        json={
            "name": "Alishan Oolong",
            "genre": "Oolong",
            "origin": "Japan",
            "producer": "Farmer Tan",
            "comment": "Floral",
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
            "quantity": 3,
            "price": 1200,
        },
    )
    tea_id = create_response.json()["id"]

    response = client.patch(f"/api/tea/{tea_id}", json={"quantity": 0})

    assert response.status_code == 200
    assert response.json()["quantity"] == 0

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