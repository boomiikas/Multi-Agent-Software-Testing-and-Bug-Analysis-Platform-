import os
import pytest
from fastapi.testclient import TestClient

from backend.security.url_validator import is_safe_target_url, validate_target_url
from backend.models.test_run import RunStatus
from backend.models.project import ProjectStatus
from backend.pipeline.runner import (
    execute_pipeline_for_run,
    request_cancellation,
    STAGE_CONFIG,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


# =====================================================================
# 1. SSRF URL VALIDATOR UNIT TESTS
# =====================================================================

def test_ssrf_validator_blocks_internal_and_private_ips():
    # Loopback
    is_safe, err = is_safe_target_url("http://127.0.0.1:8080/admin", allow_local=False)
    assert not is_safe
    assert "loopback" in err.lower() or "blocked" in err.lower()

    is_safe, err = is_safe_target_url("http://localhost:3000", allow_local=False)
    assert not is_safe

    # RFC 1918 Private
    is_safe, err = is_safe_target_url("http://192.168.1.100", allow_local=False)
    assert not is_safe
    assert "private" in err.lower() or "blocked" in err.lower()

    is_safe, err = is_safe_target_url("http://10.0.0.1", allow_local=False)
    assert not is_safe

    is_safe, err = is_safe_target_url("http://172.16.0.1", allow_local=False)
    assert not is_safe

    # Cloud metadata (AWS/GCP/Azure)
    is_safe, err = is_safe_target_url("http://169.254.169.254/latest/meta-data/", allow_local=False)
    assert not is_safe
    assert "metadata" in err.lower()

    # Even if allow_local=True, metadata MUST still be blocked
    is_safe_meta_local, _ = is_safe_target_url("http://169.254.169.254", allow_local=True)
    assert not is_safe_meta_local

    # Non-http schemes
    is_safe, err = is_safe_target_url("ftp://example.com/file")
    assert not is_safe
    assert "scheme" in err.lower()

    is_safe, err = is_safe_target_url("file:///etc/passwd")
    assert not is_safe


def test_ssrf_validator_allows_valid_public_urls():
    is_safe, err = is_safe_target_url("https://www.saucedemo.com")
    assert is_safe
    assert err is None

    # Local development override
    is_safe_local, _ = is_safe_target_url("http://127.0.0.1:8000", allow_local=True)
    assert is_safe_local


def test_validate_target_url_raises_value_error():
    with pytest.raises(ValueError) as excinfo:
        validate_target_url("http://169.254.169.254", allow_local=False)
    assert "metadata" in str(excinfo.value).lower()


# =====================================================================
# 2. TARGET URL SSRF REJECTION AT RUN CREATION
# =====================================================================

def test_start_run_rejects_ssrf_target_url(client, user_auth_headers):
    # Create project pointing to internal metadata
    proj_res = client.post(
        "/api/projects",
        json={"name": "SSRF Project", "targetUrl": "http://169.254.169.254/metadata"},
        headers=user_auth_headers,
    )
    assert proj_res.status_code == 201
    proj_id = proj_res.json()["id"]

    # Starting a run must be blocked by SSRF check
    run_res = client.post("/api/runs", json={"projectId": proj_id}, headers=user_auth_headers)
    assert run_res.status_code == 400
    assert "security validation failed" in run_res.json().get("error", "").lower()


# =====================================================================
# 3. PREVENT CONCURRENT DUPLICATE RUNS ON SAME PROJECT
# =====================================================================

def test_prevent_concurrent_duplicate_runs(client, user_auth_headers):
    proj_res = client.post(
        "/api/projects",
        json={"name": "Duplicate Run Project", "targetUrl": "https://example.com"},
        headers=user_auth_headers,
    )
    proj_id = proj_res.json()["id"]

    # First run succeeds
    r1 = client.post("/api/runs", json={"projectId": proj_id}, headers=user_auth_headers)
    assert r1.status_code == 201

    # Second run immediately attempted while r1 is RUNNING returns 409
    r2 = client.post("/api/runs", json={"projectId": proj_id}, headers=user_auth_headers)
    assert r2.status_code == 409
    assert "already currently in progress" in r2.json().get("error", "")


# =====================================================================
# 4. ARTIFACT PATH TRAVERSAL AND ACCESS CONTROLS
# =====================================================================

def test_artifact_path_traversal_protection(client, user_auth_headers, other_user_auth_headers):
    proj_res = client.post(
        "/api/projects",
        json={"name": "Artifact Project", "targetUrl": "https://example.com"},
        headers=user_auth_headers,
    )
    proj_id = proj_res.json()["id"]
    run_res = client.post("/api/runs", json={"projectId": proj_id}, headers=user_auth_headers)
    run_id = run_res.json()["id"]

    # 1. Reject path traversal sequences
    res_dot = client.get(f"/api/runs/{run_id}/artifacts/..%2F..%2Fconfig.py", headers=user_auth_headers)
    assert res_dot.status_code in (400, 404)

    res_slash = client.get(f"/api/runs/{run_id}/artifacts/subdir%2Ffile.txt", headers=user_auth_headers)
    assert res_slash.status_code in (400, 404)

    # 2. Non-existent file returns 404
    res_missing = client.get(f"/api/runs/{run_id}/artifacts/nonexistent_file.txt", headers=user_auth_headers)
    assert res_missing.status_code == 404

    # 3. Other user receives 403 Forbidden
    res_other = client.get(f"/api/runs/{run_id}/artifacts/any.txt", headers=other_user_auth_headers)
    assert res_other.status_code == 403


# =====================================================================
# 5. REPORT ENDPOINT (JSON AND RAW MARKDOWN)
# =====================================================================

def test_get_run_report_endpoint(client, user_auth_headers):
    proj_res = client.post(
        "/api/projects",
        json={"name": "Report Project", "targetUrl": "https://example.com"},
        headers=user_auth_headers,
    )
    proj_id = proj_res.json()["id"]
    run_res = client.post("/api/runs", json={"projectId": proj_id}, headers=user_auth_headers)
    run_id = run_res.json()["id"]

    # Set mock report via patch
    client.patch(
        f"/api/runs/{run_id}/status",
        json={"status": "completed", "report": "# Final QA Test Report\n\nAll tests passed successfully."},
        headers=user_auth_headers,
    )

    # JSON report
    rep_res = client.get(f"/api/runs/{run_id}/report", headers=user_auth_headers)
    assert rep_res.status_code == 200
    data = rep_res.json()
    assert data["runId"] == run_id
    assert "# Final QA Test Report" in data["report"]
    assert "limitations" in data

    # Raw markdown via raw=true
    raw_res = client.get(f"/api/runs/{run_id}/report?raw=true", headers=user_auth_headers)
    assert raw_res.status_code == 200
    assert "text/markdown" in raw_res.headers.get("content-type", "")
    assert "# Final QA Test Report" in raw_res.text

    # Markdown export via format=markdown
    md_res = client.get(f"/api/runs/{run_id}/report?format=markdown", headers=user_auth_headers)
    assert md_res.status_code == 200
    assert "attachment" in md_res.headers.get("content-disposition", "")

    # Printable HTML / PDF view via format=html
    html_res = client.get(f"/api/runs/{run_id}/report?format=html", headers=user_auth_headers)
    assert html_res.status_code == 200
    assert "text/html" in html_res.headers.get("content-type", "")
    assert "AgentQA Executive Quality & Test Report" in html_res.text
    assert "Print / Save as PDF" in html_res.text


# =====================================================================
# 6. PIPELINE RUNNER WITH MOCKED LANGGRAPH STREAMING
# =====================================================================

class MockLangGraphWorkflow:
    """Mock LangGraph workflow that streams all 9 nodes for testing."""
    async def astream(self, initial_state):
        yield {"agent_1": {"requirements": ["Req 1: Login", "Req 2: Cart"]}}
        yield {"agent_2": {"test_plan": "Plan: Test Cart Flow"}}
        yield {"agent_3": {"test_cases": [{"id": "TC1", "title": "Check Login"}]}}
        yield {"agent_4_gen": {"ui_script": "page.click('btn')"}}
        yield {"agent_4_exec": {"execution_result": {"status": "PASSED", "page_title": "Store"}}}
        yield {"agent_5_api": {"api_test_cases": "{}"}}
        yield {"agent_6_security": {"security_report": "No critical vulnerabilities found"}}
        yield {"agent_7_rca": {"rca_report": "Root cause: None (All tests passed)"}}
        yield {"agent_8_report": {"final_report": "# Test Report\n\nExecution was successful."}}


@pytest.mark.anyio
async def test_pipeline_runner_cancellation():
    from conftest import InMemoryProjectRepository, InMemoryTestRunRepository
    from backend.models.project import ProjectDocument
    from backend.models.test_run import TestRunDocument

    p_repo = InMemoryProjectRepository()
    r_repo = InMemoryTestRunRepository()

    proj = ProjectDocument(
        name="Cancel Test Project",
        ownerId="usr-123",
        targetUrl="https://example.com",
    )
    await p_repo.create(proj)
    run = TestRunDocument(projectId=proj.id, status=RunStatus.RUNNING)
    await r_repo.create(run)

    class SlowWorkflow:
        async def astream(self, initial_state):
            yield {"agent_1": {"requirements": ["Req 1"]}}
            # Signal cancellation
            request_cancellation(run.id)
            yield {"agent_2": {"test_plan": "Plan 2"}}

    await execute_pipeline_for_run(
        run.id,
        proj.id,
        test_run_repo=r_repo,
        project_repo=p_repo,
        workflow_override=SlowWorkflow(),
    )

    cancelled_run = await r_repo.find_by_id(run.id)
    assert cancelled_run.status == RunStatus.FAILED
    assert cancelled_run.cancelled is True
    assert "cancelled by user" in cancelled_run.errorTrace.lower()


@pytest.mark.anyio
async def test_pipeline_runner_error_handling():
    from conftest import InMemoryProjectRepository, InMemoryTestRunRepository
    from backend.models.project import ProjectDocument
    from backend.models.test_run import TestRunDocument

    p_repo = InMemoryProjectRepository()
    r_repo = InMemoryTestRunRepository()

    proj = ProjectDocument(
        name="Error Project",
        ownerId="usr-123",
        targetUrl="https://example.com",
    )
    await p_repo.create(proj)
    run = TestRunDocument(projectId=proj.id, status=RunStatus.RUNNING)
    await r_repo.create(run)

    class FailingWorkflow:
        async def astream(self, initial_state):
            yield {"agent_1": {"requirements": ["Req 1"]}}
            raise RuntimeError("Ollama connection timeout during stage 2")

    await execute_pipeline_for_run(
        run.id,
        proj.id,
        test_run_repo=r_repo,
        project_repo=p_repo,
        workflow_override=FailingWorkflow(),
    )

    failed_run = await r_repo.find_by_id(run.id)
    assert failed_run.status == RunStatus.FAILED
    assert "Ollama connection timeout" in failed_run.errorTrace
    assert failed_run.endTime is not None


@pytest.mark.anyio
async def test_pipeline_runner_mock_workflow():
    from conftest import InMemoryProjectRepository, InMemoryTestRunRepository
    from backend.models.project import ProjectDocument
    from backend.models.test_run import TestRunDocument

    p_repo = InMemoryProjectRepository()
    r_repo = InMemoryTestRunRepository()

    proj = ProjectDocument(
        name="Mock Pipeline Project",
        ownerId="usr-123",
        targetUrl="https://example.com",
        markdownSRS="# Specs\n- Login test",
    )
    await p_repo.create(proj)

    run = TestRunDocument(
        projectId=proj.id,
        status=RunStatus.RUNNING,
    )
    await r_repo.create(run)

    # Execute with MockLangGraphWorkflow
    mock_wf = MockLangGraphWorkflow()
    await execute_pipeline_for_run(
        run.id,
        proj.id,
        test_run_repo=r_repo,
        project_repo=p_repo,
        workflow_override=mock_wf,
    )

    # Verify run completed with all 9 steps
    finished_run = await r_repo.find_by_id(run.id)
    assert finished_run.status == RunStatus.COMPLETED
    assert finished_run.stepsCompleted == 9
    assert finished_run.currentStage == "Completed"
    assert finished_run.report == "# Test Report\n\nExecution was successful."
    assert finished_run.metrics.get("passRate") == 100
    assert len(finished_run.limitations) == 5
    assert "Agent 4 performed live Chromium browser execution" in finished_run.limitations[0]
    assert "Agent 5 executed live HTTP requests" in finished_run.limitations[1]
    assert "Agent 6 executed real Bandit static analysis" in finished_run.limitations[2]
    assert finished_run.apiExecution is not None
    assert finished_run.securityExecution is not None

    # Verify project status updated
    updated_proj = await p_repo.find_by_id(proj.id)
    assert updated_proj.status == ProjectStatus.COMPLETED
    assert updated_proj.passRate == 100


@pytest.mark.anyio
async def test_reconcile_interrupted_runs_on_restart():
    from conftest import InMemoryProjectRepository, InMemoryTestRunRepository
    from backend.models.project import ProjectDocument
    from backend.models.test_run import TestRunDocument
    from backend.services.test_run_service import reconcile_interrupted_runs

    p_repo = InMemoryProjectRepository()
    r_repo = InMemoryTestRunRepository()

    proj = ProjectDocument(
        name="Interrupted Project",
        ownerId="usr-123",
        targetUrl="https://example.com",
        status=ProjectStatus.RUNNING,
    )
    await p_repo.create(proj)

    # Run left in RUNNING status from crashed server instance
    run = TestRunDocument(projectId=proj.id, status=RunStatus.RUNNING, stepsCompleted=4)
    await r_repo.create(run)

    # Server restarts and calls reconciliation
    reconciled_count = await reconcile_interrupted_runs(test_run_repo=r_repo, project_repo=p_repo)
    assert reconciled_count == 1

    # Verify run transitioned cleanly to FAILED
    updated_run = await r_repo.find_by_id(run.id)
    assert updated_run.status == RunStatus.FAILED
    assert "restarted" in updated_run.errorTrace.lower()
    assert any("restarted" in l.get("message", "").lower() for l in updated_run.logs)

    # Verify project status transitioned
    updated_proj = await p_repo.find_by_id(proj.id)
    assert updated_proj.status == ProjectStatus.FAILED
