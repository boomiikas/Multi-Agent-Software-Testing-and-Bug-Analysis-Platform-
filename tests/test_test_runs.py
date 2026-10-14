def test_start_run_success(client, user_auth_headers):
    # Setup project
    p_res = client.post(
        "/api/projects",
        json={"name": "Run Test Project", "targetUrl": "https://runtest.com"},
        headers=user_auth_headers,
    )
    proj_id = p_res.json()["id"]

    # Start run
    res = client.post("/api/runs", json={"projectId": proj_id}, headers=user_auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert "id" in data
    assert data["projectId"] == proj_id
    assert data["status"] == "running"
    assert data["stepsCompleted"] == 1
    assert data["totalSteps"] == 9
    assert len(data["logs"]) >= 1

    # Verify project totalRuns incremented
    proj_check = client.get(f"/api/projects/{proj_id}", headers=user_auth_headers)
    assert proj_check.json()["totalRuns"] == 1
    assert proj_check.json()["status"] == "running"


def test_start_run_unauthorized_project(client, user_auth_headers, other_user_auth_headers):
    p_res = client.post(
        "/api/projects",
        json={"name": "User 1 Project", "targetUrl": "https://u1.com"},
        headers=user_auth_headers,
    )
    proj_id = p_res.json()["id"]

    # Other user attempts to start run on User 1's project
    res = client.post("/api/runs", json={"projectId": proj_id}, headers=other_user_auth_headers)
    assert res.status_code == 403
    assert "Access denied" in res.json().get("error", "")


def test_get_run_and_forbidden_check(client, user_auth_headers, other_user_auth_headers):
    p_res = client.post(
        "/api/projects",
        json={"name": "Ownership Project", "targetUrl": "https://own.com"},
        headers=user_auth_headers,
    )
    proj_id = p_res.json()["id"]

    r_res = client.post("/api/runs", json={"projectId": proj_id}, headers=user_auth_headers)
    run_id = r_res.json()["id"]

    # Owner can get run
    get_res = client.get(f"/api/runs/{run_id}", headers=user_auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == run_id

    # Other user is forbidden
    other_res = client.get(f"/api/runs/{run_id}", headers=other_user_auth_headers)
    assert other_res.status_code == 403


def test_lifecycle_allowed_and_invalid_transitions(client, user_auth_headers):
    p_res = client.post(
        "/api/projects",
        json={"name": "Lifecycle Project", "targetUrl": "https://lifecycle.com"},
        headers=user_auth_headers,
    )
    proj_id = p_res.json()["id"]

    r_res = client.post("/api/runs", json={"projectId": proj_id}, headers=user_auth_headers)
    run_id = r_res.json()["id"]

    # Valid transition: running -> completed
    patch_res = client.patch(
        f"/api/runs/{run_id}/status",
        json={"status": "completed", "stepsCompleted": 9},
        headers=user_auth_headers,
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["status"] == "completed"
    assert data["stepsCompleted"] == 9
    assert data["endTime"] is not None

    # Invalid transition: completed -> running (terminal state cannot be overwritten)
    bad_res = client.patch(
        f"/api/runs/{run_id}/status",
        json={"status": "running"},
        headers=user_auth_headers,
    )
    assert bad_res.status_code == 400
    assert "Invalid status transition" in bad_res.json().get("error", "")


def test_cancel_and_restart_run(client, user_auth_headers):
    p_res = client.post(
        "/api/projects",
        json={"name": "Cancel Project", "targetUrl": "https://cancel.com"},
        headers=user_auth_headers,
    )
    proj_id = p_res.json()["id"]

    r_res = client.post("/api/runs", json={"projectId": proj_id}, headers=user_auth_headers)
    run_id = r_res.json()["id"]

    # Cancel run
    cancel_res = client.post(f"/api/runs/{run_id}/cancel", headers=user_auth_headers)
    assert cancel_res.status_code == 200
    assert cancel_res.json().get("success") is True

    # Verify run is marked failed
    run_check = client.get(f"/api/runs/{run_id}", headers=user_auth_headers)
    assert run_check.json()["status"] == "failed"
    assert "Cancelled by user" in run_check.json()["errorTrace"]

    # Restart run creates a fresh run for project
    restart_res = client.post(f"/api/runs/{run_id}/restart", headers=user_auth_headers)
    assert restart_res.status_code == 201
    fresh_run = restart_res.json()
    assert fresh_run["id"] != run_id
    assert fresh_run["projectId"] == proj_id
    assert fresh_run["status"] == "running"
