def test_admin_list_users(client, admin_auth_headers):
    response = client.get("/api/admin/users", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert isinstance(data["users"], list)
    assert len(data["users"]) >= 1


def test_admin_create_user(client, admin_auth_headers):
    payload = {
        "fullName": "Created By Admin",
        "email": "created@example.com",
        "password": "CreatedPass123",
        "role": "ADMIN",
    }
    response = client.post("/api/admin/users", headers=admin_auth_headers, json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["fullName"] == "Created By Admin"
    assert data["user"]["email"] == "created@example.com"
    assert data["user"]["role"] == "ADMIN"


def test_admin_update_user(client, admin_auth_headers, standard_user):
    payload = {
        "fullName": "Renamed Standard User",
        "role": "ADMIN",
    }
    response = client.put(f"/api/admin/users/{standard_user.id}", headers=admin_auth_headers, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["fullName"] == "Renamed Standard User"
    assert data["user"]["role"] == "ADMIN"


def test_admin_delete_user(client, admin_auth_headers, standard_user):
    response = client.delete(f"/api/admin/users/{standard_user.id}", headers=admin_auth_headers)
    assert response.status_code == 200
    assert response.json()["success"] is True

    # User is no longer found
    list_resp = client.get("/api/admin/users", headers=admin_auth_headers)
    ids = [u["id"] for u in list_resp.json()["users"]]
    assert standard_user.id not in ids


def test_admin_endpoints_forbidden_for_regular_user(client, user_auth_headers, standard_user):
    # Regular user attempting GET
    r1 = client.get("/api/admin/users", headers=user_auth_headers)
    assert r1.status_code == 403
    assert "Access denied" in r1.json()["error"]

    # Regular user attempting POST
    r2 = client.post("/api/admin/users", headers=user_auth_headers, json={"fullName": "Test", "email": "x@x.com", "password": "x", "role": "USER"})
    assert r2.status_code == 403

    # Regular user attempting DELETE
    r3 = client.delete(f"/api/admin/users/{standard_user.id}", headers=user_auth_headers)
    assert r3.status_code == 403


def test_admin_cannot_demote_self(client, admin_user, admin_auth_headers):
    response = client.put(
        f"/api/admin/users/{admin_user.id}",
        headers=admin_auth_headers,
        json={"role": "USER"},
    )
    assert response.status_code == 400
    assert "cannot demote your own account" in response.json()["error"]


def test_admin_cannot_delete_self(client, admin_user, admin_auth_headers):
    response = client.delete(
        f"/api/admin/users/{admin_user.id}",
        headers=admin_auth_headers,
    )
    assert response.status_code == 400
    assert "cannot delete your own account" in response.json()["error"]
