def test_create_project_success(client, user_auth_headers):
    payload = {
        "name": "E-Commerce Testing Suite",
        "targetUrl": "https://shop.example.com",
        "srsDocument": "# E-Commerce SRS\nTest checkout flow."
    }
    res = client.post("/api/projects", json=payload, headers=user_auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "E-Commerce Testing Suite"
    assert data["targetUrl"] == "https://shop.example.com"
    assert data["srsDocument"] == "# E-Commerce SRS\nTest checkout flow."
    assert data["status"] == "pending"
    assert data["totalRuns"] == 0
    assert "id" in data
    assert data["ownerId"] == "usr-test-123"


def test_create_project_invalid_url(client, user_auth_headers):
    # Unsafe javascript: scheme
    res = client.post(
        "/api/projects",
        json={"name": "Bad Project", "targetUrl": "javascript:alert(1)"},
        headers=user_auth_headers,
    )
    assert res.status_code == 400
    assert "error" in res.json()

    # Missing scheme / invalid format
    res2 = client.post(
        "/api/projects",
        json={"name": "Bad Project", "targetUrl": "htp:/invalid"},
        headers=user_auth_headers,
    )
    assert res2.status_code == 400


def test_create_project_short_name(client, user_auth_headers):
    res = client.post(
        "/api/projects",
        json={"name": "ab", "targetUrl": "https://example.com"},
        headers=user_auth_headers,
    )
    assert res.status_code == 400
    assert "at least 3 characters" in res.json().get("error", "").lower()


def test_list_projects_owner_isolation(client, user_auth_headers, other_user_auth_headers):
    # Create project under standard_user
    client.post(
        "/api/projects",
        json={"name": "User 1 Project", "targetUrl": "https://user1.com"},
        headers=user_auth_headers,
    )

    # Create project under other_user
    client.post(
        "/api/projects",
        json={"name": "User 2 Project", "targetUrl": "https://user2.com"},
        headers=other_user_auth_headers,
    )

    # Standard user lists projects
    res1 = client.get("/api/projects", headers=user_auth_headers)
    assert res1.status_code == 200
    data1 = res1.json()
    assert len(data1) == 1
    assert data1[0]["name"] == "User 1 Project"

    # Other user lists projects
    res2 = client.get("/api/projects", headers=other_user_auth_headers)
    assert res2.status_code == 200
    data2 = res2.json()
    assert len(data2) == 1
    assert data2[0]["name"] == "User 2 Project"


def test_get_project_by_id_and_forbidden_check(client, user_auth_headers, other_user_auth_headers):
    res = client.post(
        "/api/projects",
        json={"name": "Protected Project", "targetUrl": "https://protected.com"},
        headers=user_auth_headers,
    )
    proj_id = res.json()["id"]

    # Owner can get project
    res_owner = client.get(f"/api/projects/{proj_id}", headers=user_auth_headers)
    assert res_owner.status_code == 200
    assert res_owner.json()["id"] == proj_id

    # Other user is forbidden
    res_other = client.get(f"/api/projects/{proj_id}", headers=other_user_auth_headers)
    assert res_other.status_code == 403
    assert "Access denied" in res_other.json().get("error", "")


def test_get_project_not_found(client, user_auth_headers):
    res = client.get("/api/projects/non-existent-id", headers=user_auth_headers)
    assert res.status_code == 404
    assert res.json().get("error") == "Project not found."


def test_update_project_success_and_forbidden(client, user_auth_headers, other_user_auth_headers):
    res = client.post(
        "/api/projects",
        json={"name": "Original Name", "targetUrl": "https://orig.com"},
        headers=user_auth_headers,
    )
    proj_id = res.json()["id"]

    # Other user cannot update
    res_other = client.put(
        f"/api/projects/{proj_id}",
        json={"name": "Hacked Name"},
        headers=other_user_auth_headers,
    )
    assert res_other.status_code == 403

    # Owner updates project
    res_update = client.put(
        f"/api/projects/{proj_id}",
        json={"name": "Updated Name", "targetUrl": "https://updated.com"},
        headers=user_auth_headers,
    )
    assert res_update.status_code == 200
    assert res_update.json()["name"] == "Updated Name"
    assert res_update.json()["targetUrl"] == "https://updated.com"


def test_delete_project_cascades_test_runs(client, user_auth_headers, other_user_auth_headers):
    # Create project
    res_p = client.post(
        "/api/projects",
        json={"name": "Project to Delete", "targetUrl": "https://delete.com"},
        headers=user_auth_headers,
    )
    proj_id = res_p.json()["id"]

    # Create run for this project
    res_r = client.post("/api/runs", json={"projectId": proj_id}, headers=user_auth_headers)
    assert res_r.status_code == 201
    run_id = res_r.json()["id"]

    # Other user cannot delete
    res_del_other = client.delete(f"/api/projects/{proj_id}", headers=other_user_auth_headers)
    assert res_del_other.status_code == 403

    # Owner deletes project
    res_del = client.delete(f"/api/projects/{proj_id}", headers=user_auth_headers)
    assert res_del.status_code == 200
    assert res_del.json().get("success") is True

    # Verify project is gone
    assert client.get(f"/api/projects/{proj_id}", headers=user_auth_headers).status_code == 404

    # Verify run is cleaned up
    assert client.get(f"/api/runs/{run_id}", headers=user_auth_headers).status_code == 404
