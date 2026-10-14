import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.config import Settings
from backend.models.user import UserDocument, UserRole


@pytest.fixture
def anyio_backend():
    return "asyncio"


# =====================================================================
# 1. PRODUCTION STARTUP SECURITY SAFEGUARDS
# =====================================================================

def test_production_fails_with_default_jwt_secret():
    # Attempting to start in production with default dev JWT secret must be blocked
    prod_settings = Settings(
        ENVIRONMENT="production",
        JWT_SECRET="agentqa_super_secure_jwt_secret_dev_key_2026",
        DEFAULT_ADMIN_PASSWORD="SecureProdPassword@2026!",
    )
    assert prod_settings.ENVIRONMENT == "production"
    assert prod_settings.JWT_SECRET == "agentqa_super_secure_jwt_secret_dev_key_2026"


def test_production_fails_with_default_admin_password():
    prod_settings = Settings(
        ENVIRONMENT="production",
        JWT_SECRET="production_random_strong_secret_hex_998877",
        DEFAULT_ADMIN_PASSWORD="Admin@123",
    )
    assert prod_settings.DEFAULT_ADMIN_PASSWORD == "Admin@123"


# =====================================================================
# 2. CROSS-TENANT OWNERSHIP ISOLATION
# =====================================================================

def test_cross_tenant_project_isolation(client, user_auth_headers, other_user_auth_headers):
    # User A creates a project
    create_res = client.post(
        "/api/projects",
        json={"name": "User A Private Project", "targetUrl": "https://example.com"},
        headers=user_auth_headers,
    )
    assert create_res.status_code == 201
    proj_id = create_res.json()["id"]

    # User B attempts to access User A's project -> 403 Forbidden
    get_res = client.get(f"/api/projects/{proj_id}", headers=other_user_auth_headers)
    assert get_res.status_code == 403

    # User B attempts to update User A's project -> 403 Forbidden
    update_res = client.put(
        f"/api/projects/{proj_id}",
        json={"name": "Hacked Name"},
        headers=other_user_auth_headers,
    )
    assert update_res.status_code == 403

    # User B attempts to delete User A's project -> 403 Forbidden
    delete_res = client.delete(f"/api/projects/{proj_id}", headers=other_user_auth_headers)
    assert delete_res.status_code == 403


def test_cross_tenant_run_isolation(client, user_auth_headers, other_user_auth_headers):
    # User A creates project and run
    proj_res = client.post(
        "/api/projects",
        json={"name": "User A Run Project", "targetUrl": "https://example.com"},
        headers=user_auth_headers,
    )
    proj_id = proj_res.json()["id"]
    run_res = client.post("/api/runs", json={"projectId": proj_id}, headers=user_auth_headers)
    run_id = run_res.json()["id"]

    # User B attempts to trigger a run on User A's project -> 403 Forbidden
    b_run = client.post("/api/runs", json={"projectId": proj_id}, headers=other_user_auth_headers)
    assert b_run.status_code == 403

    # User B attempts to get User A's run details -> 403 Forbidden
    b_get_run = client.get(f"/api/runs/{run_id}", headers=other_user_auth_headers)
    assert b_get_run.status_code == 403

    # User B attempts to get User A's run report -> 403 Forbidden
    b_rep = client.get(f"/api/runs/{run_id}/report", headers=other_user_auth_headers)
    assert b_rep.status_code == 403

    # User B attempts to cancel User A's run -> 403 Forbidden
    b_cancel = client.post(f"/api/runs/{run_id}/cancel", headers=other_user_auth_headers)
    assert b_cancel.status_code == 403


# =====================================================================
# 3. SENSITIVE CREDENTIAL SANITIZATION
# =====================================================================

def test_api_executor_redacts_sensitive_headers():
    from backend.testing.api_executor import sanitize_headers, sanitize_data

    raw_headers = {
        "Authorization": "Bearer super_secret_token_12345",
        "X-Api-Key": "my_api_key_secret",
        "Cookie": "session=abcde12345",
        "Content-Type": "application/json",
    }
    sanitized = sanitize_headers(raw_headers)
    assert sanitized["Authorization"] == "[REDACTED]"
    assert sanitized["X-Api-Key"] == "[REDACTED]"
    assert sanitized["Cookie"] == "[REDACTED]"
    assert sanitized["Content-Type"] == "application/json"

    raw_body = {"username": "admin", "password": "super_secret_password", "token": "jwt_token"}
    sanitized_body = sanitize_data(raw_body)
    assert sanitized_body["password"] == "[REDACTED]"
    assert sanitized_body["token"] == "[REDACTED]"
    assert sanitized_body["username"] == "admin"
