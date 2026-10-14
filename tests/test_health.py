def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert "database" in data


def test_404_fallback(client):
    response = client.get("/api/non-existent-route")
    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "Not found."
