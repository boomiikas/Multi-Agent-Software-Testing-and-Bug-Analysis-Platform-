def test_dashboard_unauthenticated(client):
    res_stats = client.get("/api/dashboard/stats")
    assert res_stats.status_code == 401

    res_runs = client.get("/api/dashboard/runs")
    assert res_runs.status_code == 401


def test_dashboard_stats_and_recent_runs(client, user_auth_headers):
    # Initial empty state
    stats_empty = client.get("/api/dashboard/stats", headers=user_auth_headers).json()
    assert stats_empty["totalProjects"] == 0
    assert stats_empty["activeRuns"] == 0
    assert stats_empty["passRate"] == 0.0

    # Create project 1 and run 1 (completed)
    p1 = client.post(
        "/api/projects",
        json={"name": "Dashboard Project 1", "targetUrl": "https://p1.com"},
        headers=user_auth_headers,
    ).json()
    r1 = client.post("/api/runs", json={"projectId": p1["id"]}, headers=user_auth_headers).json()
    client.patch(
        f"/api/runs/{r1['id']}/status",
        json={"status": "completed", "stepsCompleted": 9},
        headers=user_auth_headers,
    )

    # Create project 2 and run 2 (running)
    p2 = client.post(
        "/api/projects",
        json={"name": "Dashboard Project 2", "targetUrl": "https://p2.com"},
        headers=user_auth_headers,
    ).json()
    r2 = client.post("/api/runs", json={"projectId": p2["id"]}, headers=user_auth_headers).json()

    # Query dashboard stats
    stats_live = client.get("/api/dashboard/stats", headers=user_auth_headers).json()
    assert stats_live["totalProjects"] == 2
    assert stats_live["activeRuns"] == 1
    assert stats_live["passRate"] == 100.0  # 1 completed, 0 failed

    # Query dashboard runs
    recent_runs = client.get("/api/dashboard/runs", headers=user_auth_headers).json()
    assert len(recent_runs) == 2
    project_names = [r["projectName"] for r in recent_runs]
    assert "Dashboard Project 1" in project_names
    assert "Dashboard Project 2" in project_names
