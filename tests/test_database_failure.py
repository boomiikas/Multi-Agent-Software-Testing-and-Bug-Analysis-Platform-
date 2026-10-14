from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app


def test_database_disconnected_health():
    # In disconnected state, /api/health returns database: disconnected
    with patch("backend.database.is_mongo_connected", return_value=False):
        with TestClient(app) as c:
            resp = c.get("/api/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ok"
            assert data["database"] == "disconnected"


def test_database_disconnected_endpoint_returns_503():
    # When MongoDB is disconnected, endpoints requiring database return 503
    with patch("backend.database.is_mongo_connected", return_value=False), \
         patch("backend.database._is_connected", False), \
         patch("backend.database._db", None):
        with TestClient(app, raise_server_exceptions=False) as c:
            resp = c.post(
                "/api/auth/login",
                json={"email": "any@example.com", "password": "Password123"},
            )
            assert resp.status_code == 503
            data = resp.json()
            assert "Database service is unavailable" in data["error"]
