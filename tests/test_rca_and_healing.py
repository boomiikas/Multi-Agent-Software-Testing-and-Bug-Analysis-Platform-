import pytest
import asyncio
from backend.testing.rca_engine import (
    analyze_execution_evidence,
    FailureCategory,
    RcaDiagnosis,
)
from backend.testing.retry_controller import (
    RetryController,
    FinalOutcome,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


# =====================================================================
# 1. EVIDENCE-BASED RCA CLASSIFICATION TESTS
# =====================================================================

def test_rca_classifies_srs_selector_missing_error():
    pipeline_err = "ValueError: Generated selectors are absent from the SRS: .title"
    summary = analyze_execution_evidence(pipeline_error=pipeline_err)

    assert summary.hasFailures is True
    assert summary.totalDiagnoses == 1
    diag = summary.diagnoses[0]
    assert diag.failureCategory == FailureCategory.TEST_SCRIPT_ERROR
    assert diag.retryEligible is False
    assert diag.confidence == "HIGH"
    assert diag.isHypothesis is False
    assert "agent_4_ui_script.py" in diag.artifactReferences


def test_rca_classifies_ssrf_security_block():
    pipeline_err = "Target URL security validation failed: Access to cloud metadata IP 169.254.169.254 is strictly forbidden."
    summary = analyze_execution_evidence(pipeline_error=pipeline_err)

    assert summary.hasFailures is True
    diag = summary.diagnoses[0]
    assert diag.failureCategory == FailureCategory.SECURITY_VULNERABILITY
    assert diag.retryEligible is False
    assert "NEVER" in diag.retryReason.upper()


def test_rca_classifies_playwright_locator_timeout():
    ui_exec = {
        "status": "FAILED",
        "error_type": "PlaywrightTimeoutError",
        "error_message": "Timeout 30000ms exceeded waiting for locator('.title')",
        "screenshot": "screenshot_fail.png",
    }
    summary = analyze_execution_evidence(ui_execution=ui_exec)

    assert summary.hasFailures is True
    diag = summary.diagnoses[0]
    assert diag.failureCategory == FailureCategory.APPLICATION_DEFECT
    assert diag.retryEligible is True
    assert "screenshot_fail.png" in diag.artifactReferences


def test_rca_classifies_playwright_assertion_failure():
    ui_exec = {
        "status": "FAILED",
        "error_type": "AssertionError",
        "error_message": "assert 'Products' in 'Login Failed'",
        "screenshot": "assert_err.png",
    }
    summary = analyze_execution_evidence(ui_execution=ui_exec)

    assert summary.hasFailures is True
    diag = summary.diagnoses[0]
    assert diag.failureCategory == FailureCategory.APPLICATION_DEFECT
    assert diag.retryEligible is False
    assert diag.isHypothesis is False


def test_rca_classifies_api_404_incorrect_expectations():
    api_exec = {
        "tests": [
            {
                "endpoint": "/nonexistent-route",
                "method": "GET",
                "status": "FAILED",
                "actualStatus": 404,
                "expectedStatus": 200,
            }
        ]
    }
    summary = analyze_execution_evidence(api_execution=api_exec)

    assert summary.hasFailures is True
    diag = summary.diagnoses[0]
    assert diag.failureCategory == FailureCategory.INCORRECT_EXPECTATIONS
    assert diag.retryEligible is False


def test_rca_classifies_api_500_application_defect():
    api_exec = {
        "tests": [
            {
                "endpoint": "/api/users",
                "method": "POST",
                "status": "FAILED",
                "actualStatus": 500,
                "expectedStatus": 201,
                "error": "Internal Server Error in database driver",
            }
        ]
    }
    summary = analyze_execution_evidence(api_execution=api_exec)

    assert summary.hasFailures is True
    diag = summary.diagnoses[0]
    assert diag.failureCategory == FailureCategory.APPLICATION_DEFECT
    assert diag.retryEligible is False


def test_rca_classifies_security_cve_finding():
    sec_exec = {
        "findings": [
            {
                "tool": "pip-audit",
                "ruleId": "CVE-2023-37276",
                "severity": "HIGH",
                "file": "requirements.txt",
                "line": 12,
                "description": "Vulnerability in aiohttp",
                "remediation": "Upgrade to aiohttp>=3.8.5",
            }
        ]
    }
    summary = analyze_execution_evidence(security_execution=sec_exec)

    assert summary.hasFailures is True
    diag = summary.diagnoses[0]
    assert diag.failureCategory == FailureCategory.SECURITY_VULNERABILITY
    assert diag.retryEligible is False


# =====================================================================
# 2. CONTROLLED RETRY CONTROLLER TESTS
# =====================================================================

@pytest.mark.anyio
async def test_retry_controller_successful_transient_recovery():
    controller = RetryController(default_max_retries=2, backoff_base_seconds=0.01)

    attempts_done = 0

    async def flaky_api_call():
        nonlocal attempts_done
        attempts_done += 1
        if attempts_done == 1:
            return {"status": "FAILED", "error": "Transient socket timeout"}
        return {"status": "PASSED", "error": None}

    record = await controller.execute_controlled_retry(
        test_identifier="GET /api/inventory",
        test_type="API",
        initial_status="FAILED",
        initial_error="Transient socket timeout",
        retry_fn=flaky_api_call,
    )

    assert record.retryEligible is True
    assert record.finalOutcome == FinalOutcome.PASSED_AFTER_RETRY
    assert record.attemptsCount == 2
    assert len(record.attempts) == 2
    assert record.attempts[0].status == "FAILED"
    assert record.attempts[1].status == "PASSED"
    assert "Resolved after retry" in (record.humanReviewRecommendation or "")


@pytest.mark.anyio
async def test_retry_controller_exhausts_retries_on_persistent_failure():
    controller = RetryController(default_max_retries=2, backoff_base_seconds=0.01)

    attempts_done = 0

    async def persistently_failing_call():
        nonlocal attempts_done
        attempts_done += 1
        return {"status": "FAILED", "error": "Target server timed out"}

    record = await controller.execute_controlled_retry(
        test_identifier="GET /api/heavy-job",
        test_type="API",
        initial_status="FAILED",
        initial_error="Target server timed out",
        retry_fn=persistently_failing_call,
    )

    assert record.retryEligible is True
    assert record.finalOutcome == FinalOutcome.STILL_FAILED
    assert record.attemptsCount == 2
    assert "Exhausted 2 retries" in (record.humanReviewRecommendation or "")


@pytest.mark.anyio
async def test_retry_controller_strictly_rejects_ssrf_retry():
    controller = RetryController(default_max_retries=2)

    call_executed = False

    async def unexpected_call():
        nonlocal call_executed
        call_executed = True
        return {"status": "PASSED"}

    record = await controller.execute_controlled_retry(
        test_identifier="GET http://169.254.169.254",
        test_type="API",
        initial_status="BLOCKED",
        initial_error="Access to cloud metadata IP 169.254.169.254 is strictly forbidden.",
        retry_fn=unexpected_call,
    )

    assert record.retryEligible is False
    assert record.finalOutcome == FinalOutcome.BLOCKED
    assert record.attemptsCount == 0
    assert call_executed is False
    assert "NEVER retry security violations" in record.eligibilityReason


@pytest.mark.anyio
async def test_retry_controller_strictly_rejects_auth_retry():
    controller = RetryController(default_max_retries=2)

    call_executed = False

    async def unexpected_call():
        nonlocal call_executed
        call_executed = True
        return {"status": "PASSED"}

    record = await controller.execute_controlled_retry(
        test_identifier="GET /api/admin/metrics",
        test_type="API",
        initial_status="FAILED",
        initial_error="HTTP 401 Unauthorized: Invalid token",
        retry_fn=unexpected_call,
    )

    assert record.retryEligible is False
    assert record.finalOutcome == FinalOutcome.RETRY_SKIPPED
    assert record.attemptsCount == 0
    assert call_executed is False
    assert "401" in record.eligibilityReason


@pytest.mark.anyio
async def test_retry_controller_strictly_rejects_cve_retry():
    controller = RetryController(default_max_retries=2)

    call_executed = False

    async def unexpected_call():
        nonlocal call_executed
        call_executed = True
        return {"status": "PASSED"}

    record = await controller.execute_controlled_retry(
        test_identifier="SECURITY:pip-audit",
        test_type="SECURITY",
        initial_status="FAILED",
        initial_error="Vulnerability CVE-2023-37276 detected in requirements.txt",
        retry_fn=unexpected_call,
    )

    assert record.retryEligible is False
    assert record.finalOutcome == FinalOutcome.RETRY_SKIPPED
    assert record.attemptsCount == 0
    assert call_executed is False
    assert "Deterministic security vulnerability" in record.eligibilityReason
