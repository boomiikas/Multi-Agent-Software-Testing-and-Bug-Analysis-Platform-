def test_get_profile(client, standard_user, user_auth_headers):
    response = client.get("/api/users/profile", headers=user_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["id"] == standard_user.id
    assert data["user"]["fullName"] == standard_user.fullName
    assert data["user"]["email"] == standard_user.email


def test_update_profile(client, standard_user, user_auth_headers):
    payload = {"fullName": "Updated Name", "profileImage": "https://example.com/avatar.png"}
    response = client.put("/api/users/profile", headers=user_auth_headers, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["fullName"] == "Updated Name"
    assert data["user"]["profileImage"] == "https://example.com/avatar.png"


def test_profile_unauthenticated(client):
    response = client.get("/api/users/profile")
    assert response.status_code == 401


def test_update_profile_invalid_name(client, user_auth_headers):
    response = client.put("/api/users/profile", headers=user_auth_headers, json={"fullName": "A"})
    assert response.status_code == 400
    assert "at least 2 characters" in response.json()["error"]
