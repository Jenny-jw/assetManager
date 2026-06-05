import pytest

TEA_CREATE_PAYLOAD = {
    "name": "Test Tea",
    "genre": "Oolong",
    "origin": "Alishan",
    "quantity": 1,
}

@pytest.mark.parametrize(
    "method,path_factory",
    [
        ("post", lambda tea_id: "/api/tea/"),
        ("patch", lambda tea_id: f"/api/tea/{tea_id}"),
        ("delete", lambda tea_id: f"/api/tea/{tea_id}"),
    ],
)
def test_tea_mutations_require_authentication(
    client_no_auth, method, path_factory, seeded_tea_id
):
    path = path_factory(seeded_tea_id)
    request = getattr(client_no_auth, method)

    if method == "post":
        response = request(path, json=TEA_CREATE_PAYLOAD)
    elif method == "patch":
        response = request(path, json={"quantity": 10})
    else:
        response = request(path)

    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.parametrize(
    "client_fixture,role",
    [
        ("client_user", "user"),
        ("client_guest", "guest"),
    ],
)

@pytest.mark.parametrize(
    "method,path_factory",
    [
        ("post", lambda tea_id: "/api/tea/"),
        ("patch", lambda tea_id: f"/api/tea/{tea_id}"),
        ("delete", lambda tea_id: f"/api/tea/{tea_id}"),
    ],
)
def test_tea_mutations_forbid_non_admin(
    client_fixture, role, method, path_factory, seeded_tea_id, request
):
    client = request.getfixturevalue(client_fixture)
    path = path_factory(seeded_tea_id)
    http_request = getattr(client, method)

    if method == "post":
        response = http_request(path, json=TEA_CREATE_PAYLOAD)
    elif method == "patch":
        response = http_request(path, json={"quantity": 10})
    else:
        response = http_request(path)

    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden"

def test_admin_can_create_tea(client):
    response = client.post("/api/tea/", json=TEA_CREATE_PAYLOAD)
    assert response.status_code == 200
    assert response.json()["name"] == "Test Tea"

def test_user_can_list_teas(client_user, fake_db):
    fake_db.teas.seed({"name": "Readable Tea", "genre": "Green", "origin": "Taiwan"})
    response = client_user.get("/api/tea/")
    assert response.status_code == 200
    assert response.json()["total"] == 1