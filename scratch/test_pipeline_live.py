import httpx
import time

BASE_URL = "http://127.0.0.1:4000/api"

def run_test():
    client = httpx.Client(base_url=BASE_URL, timeout=30.0)

    # 1. Login
    login_res = client.post("/auth/login", json={"email": "admin@example.com", "password": "Admin@123"})
    print("Login status:", login_res.status_code)
    assert login_res.status_code == 200, login_res.text
    token = login_res.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. SSRF Validation Test
    print("\n--- Testing SSRF Validation ---")
    ssrf_proj = client.post("/projects", json={"name": "SSRF Target", "targetUrl": "http://169.254.169.254"}, headers=headers).json()
    ssrf_run = client.post("/runs", json={"projectId": ssrf_proj["id"]}, headers=headers)
    print("SSRF Run response status:", ssrf_run.status_code)
    print("SSRF Error response:", ssrf_run.json().get("error"))
    assert ssrf_run.status_code == 400
    assert "security validation failed" in ssrf_run.json().get("error", "").lower()
    client.delete(f"/projects/{ssrf_proj['id']}", headers=headers)
    print("SSRF test PASSED!")

    # 3. Create Valid Project
    print("\n--- Creating Valid Testing Project ---")
    proj = client.post("/projects", json={
        "name": "Live SauceDemo Test",
        "targetUrl": "https://www.saucedemo.com",
        "markdownSRS": "Verify SauceDemo login and checkout workflow."
    }, headers=headers).json()
    proj_id = proj["id"]
    print(f"Project created with ID: {proj_id}")

    # 4. Start Pipeline Run
    print("\n--- Initiating Multi-Agent Pipeline Run ---")
    run_res = client.post("/runs", json={"projectId": proj_id}, headers=headers)
    print("Start run status:", run_res.status_code)
    assert run_res.status_code == 201
    run = run_res.json()
    run_id = run["id"]
    print(f"Run initiated with ID: {run_id}, initial status: {run['status']}, step: {run['stepsCompleted']}/9")

    # 5. Test Duplicate Run Prevention
    print("\n--- Testing Concurrent Duplicate Run Prevention ---")
    dup_res = client.post("/runs", json={"projectId": proj_id}, headers=headers)
    print("Duplicate run status:", dup_res.status_code, "(Expected 409)")
    assert dup_res.status_code == 409
    print("Duplicate prevention PASSED!")

    # 6. Poll Run Status for progress
    print("\n--- Monitoring Pipeline Live Progress ---")
    for _ in range(10):
        status_res = client.get(f"/runs/{run_id}", headers=headers).json()
        print(f"Status: {status_res['status']} | Stage: {status_res.get('currentStage')} | Steps: {status_res['stepsCompleted']}/9 | Logs count: {len(status_res.get('logs', []))}")
        if status_res['status'] in ('completed', 'failed'):
            break
        time.sleep(2)

    # 7. Check Report Endpoint
    rep_res = client.get(f"/runs/{run_id}/report", headers=headers)
    print("\nReport endpoint status:", rep_res.status_code)
    print("Report summary keys:", list(rep_res.json().keys()))

    # Cleanup
    client.delete(f"/projects/{proj_id}", headers=headers)
    print("\nLive Integration Verification PASSED successfully!")

if __name__ == "__main__":
    run_test()
