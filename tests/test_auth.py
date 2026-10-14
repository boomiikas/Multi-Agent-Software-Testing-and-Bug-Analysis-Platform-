def test_register_success(client):
    payload = {
        "fullName": "Alice Johnson",
        "email": "alice@example.com",
        "password": "Password123",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "token" in data
    assert "user" in data
    assert data["user"]["email"] == "alice@example.com"
    assert data["user"]["fullName"] == "Alice Johnson"
    assert data["user"]["role"] == "USER"
    assert "password" not in data["user"]


def test_register_duplicate_email(client, standard_user):
    payload = {
        "fullName": "Duplicate User",
        "email": standard_user.email,
        "password": "Password123",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 409
    data = response.json()
    assert data["error"] == "An account with this email already exists."


def test_register_validation_errors(client):
    # Short name (< 2 chars)
    r1 = client.post("/api/auth/register", json={"fullName": "A", "email": "a@b.com", "password": "Password123"})
    assert r1.status_code == 400
    assert "at least 2 characters" in r1.json()["error"]

    # Invalid email
    r2 = client.post("/api/auth/register", json={"fullName": "Valid Name", "email": "not-an-email", "password": "Password123"})
    assert r2.status_code == 400
    assert "valid email is required" in r2.json()["error"]

    # Short password (< 8 chars)
    r3 = client.post("/api/auth/register", json={"fullName": "Valid Name", "email": "valid@email.com", "password": "Pass1"})
    assert r3.status_code == 400
    assert "at least 8 characters" in r3.json()["error"]

    # Missing uppercase/number
    r4 = client.post("/api/auth/register", json={"fullName": "Valid Name", "email": "valid@email.com", "password": "passwordonly"})
    assert r4.status_code == 400
    assert "uppercase letter and one number" in r4.json()["error"]


def test_login_success(client, standard_user):
    payload = {
        "email": standard_user.email,
        "password": "UserPass123",
        "rememberMe": True,
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["rememberMe"] is True
    assert data["user"]["email"] == standard_user.email


def test_login_wrong_password(client, standard_user):
    payload = {
        "email": standard_user.email,
        "password": "WrongPassword123",
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 401
    assert response.json()["error"] == "Invalid email or password."


def test_login_unregistered_email(client):
    payload = {
        "email": "ghost@example.com",
        "password": "Password123",
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 401
    assert response.json()["error"] == "Invalid email or password."


def test_logout(client, user_auth_headers):
    response = client.post("/api/auth/logout", headers=user_auth_headers)
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_me_authenticated(client, standard_user, user_auth_headers):
    response = client.get("/api/auth/me", headers=user_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["id"] == standard_user.id
    assert data["user"]["email"] == standard_user.email


def test_me_unauthenticated(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["error"]


def test_forgot_and_reset_password(client, standard_user):
    # Request reset link
    forgot_resp = client.post("/api/auth/forgot-password", json={"email": standard_user.email})
    assert forgot_resp.status_code == 200
    forgot_data = forgot_resp.json()
    assert forgot_data["success"] is True
    token = forgot_data.get("resetTokenForDev")
    assert token is not None

    # Reset password using token
    reset_resp = client.post("/api/auth/reset-password", json={"token": token, "password": "NewSecret123"})
    assert reset_resp.status_code == 200
    assert reset_resp.json()["success"] is True

    # Old password no longer works
    fail_login = client.post("/api/auth/login", json={"email": standard_user.email, "password": "UserPass123"})
    assert fail_login.status_code == 401

    # New password works
    success_login = client.post("/api/auth/login", json={"email": standard_user.email, "password": "NewSecret123"})
    assert success_login.status_code == 200


def test_reset_password_invalid_token(client):
    response = client.post("/api/auth/reset-password", json={"token": "fake-or-expired-token", "password": "NewSecret123"})
    assert response.status_code == 400
    assert "invalid or has expired" in response.json()["error"]


def test_change_password(client, standard_user, user_auth_headers):
    # Incorrect current password
    bad_resp = client.put(
        "/api/auth/change-password",
        headers=user_auth_headers,
        json={"currentPassword": "WrongCurrent123", "password": "BrandNewPass123"},
    )
    assert bad_resp.status_code == 401
    assert bad_resp.json()["error"] == "Current password is incorrect."

    # Correct current password
    good_resp = client.put(
        "/api/auth/change-password",
        headers=user_auth_headers,
        json={"currentPassword": "UserPass123", "password": "BrandNewPass123"},
    )
    assert good_resp.status_code == 200
    assert good_resp.json()["success"] is True

    # Login with new password succeeds
    login_resp = client.post("/api/auth/login", json={"email": standard_user.email, "password": "BrandNewPass123"})
    assert login_resp.status_code == 200
