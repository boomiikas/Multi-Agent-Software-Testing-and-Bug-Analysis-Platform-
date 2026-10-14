import time
import asyncio
from enum import Enum
from typing import List, Dict, Any, Optional, Callable, Awaitable
from pydantic import BaseModel, Field
from loguru import logger
from .rca_engine import RcaDiagnosis, FailureCategory


class FinalOutcome(str, Enum):
    PASSED_INITIALLY = "PASSED_INITIALLY"
    PASSED_AFTER_RETRY = "PASSED_AFTER_RETRY"
    STILL_FAILED = "STILL_FAILED"
    BLOCKED = "BLOCKED"
    RETRY_SKIPPED = "RETRY_SKIPPED"


class RetryAttempt(BaseModel):
    attemptNumber: int
    executedAt: float
    durationSeconds: float
    status: str  # PASSED, FAILED, BLOCKED
    error: Optional[str] = None
    reason: str
    diffFromInitial: Optional[str] = None


class RetryRecord(BaseModel):
    testIdentifier: str
    testType: str  # "API", "UI", "PIPELINE"
    initialResult: str  # PASSED, FAILED, BLOCKED
    initialError: Optional[str] = None
    retryEligible: bool
    eligibilityReason: str
    maxRetriesAllowed: int = 2
    attemptsCount: int = 0
    attempts: List[RetryAttempt] = Field(default_factory=list)
    finalOutcome: FinalOutcome
    humanReviewRecommendation: Optional[str] = None

    model_config = {"extra": "ignore"}


class RetryController:
    """
    Controlled Self-Healing Retry Controller.
    Enforces bounded retries, eligibility rules, and before/after outcome tracking.
    """

    def __init__(self, default_max_retries: int = 2, backoff_base_seconds: float = 1.0):
        self.default_max_retries = default_max_retries
        self.backoff_base_seconds = backoff_base_seconds

    def evaluate_eligibility(
        self,
        test_type: str,
        initial_status: str,
        diagnosis: Optional[RcaDiagnosis] = None,
        error_message: Optional[str] = None,
    ) -> tuple[bool, str]:
        """
        Determines whether a failed test is eligible for controlled retry.
        Strictly enforces non-retry rules for SSRF, Auth, Security findings, and script errors.
        """
        # If it passed initially, no retry needed
        if initial_status.upper() == "PASSED":
            return False, "Test passed initially; no retry required."

        # If it was blocked by SSRF
        if initial_status.upper() == "BLOCKED":
            return False, "SSRF or security boundary blocked execution. NEVER retry security violations."

        err_text = (error_message or "").lower()

        # Strict Non-Retry Constraints
        if "ssrf" in err_text or "cloud metadata" in err_text or "forbidden" in err_text and "ip" in err_text:
            return False, "SSRF violation detected. Retries are strictly prohibited for security violations."

        if "401" in err_text or "unauthorized" in err_text:
            return False, "Authentication failure (401). Retries without valid credentials are prohibited."

        if "403" in err_text or "access denied" in err_text:
            return False, "Authorization failure (403). Retries without required permission scopes are prohibited."

        if "cve-" in err_text or "bandit" in err_text or "vulnerability" in err_text:
            return False, "Deterministic security vulnerability. Must be remediated in code, not retried."

        if "absent from the srs" in err_text:
            return False, "Deterministic SRS selector validation failure. Requires specification or prompt correction."

        # Check RCA diagnosis if provided
        if diagnosis:
            if not diagnosis.retryEligible:
                return False, diagnosis.retryReason
            if diagnosis.failureCategory in (
                FailureCategory.SECURITY_VULNERABILITY,
                FailureCategory.AUTHENTICATION_PROBLEM,
                FailureCategory.INCORRECT_EXPECTATIONS,
                FailureCategory.TEST_SCRIPT_ERROR,
            ):
                return False, f"Category '{diagnosis.failureCategory.value}' is deterministic and ineligible for automated retry."

        # Transient condition check
        if any(term in err_text for term in ["timeout", "timed out", "connection reset", "econnreset", "locator.wait_for"]):
            return True, "Transient timeout or rendering latency detected. Eligible for bounded retry with backoff."

        return False, "Failure is not identified as a transient retryable condition."

    async def execute_controlled_retry(
        self,
        test_identifier: str,
        test_type: str,
        initial_status: str,
        initial_error: Optional[str],
        retry_fn: Callable[[], Awaitable[Dict[str, Any]]],
        diagnosis: Optional[RcaDiagnosis] = None,
        max_retries: Optional[int] = None,
    ) -> RetryRecord:
        """
        Executes bounded, auditable retries with backoff and comparison.
        """
        limit = max_retries if max_retries is not None else self.default_max_retries
        eligible, reason = self.evaluate_eligibility(
            test_type=test_type,
            initial_status=initial_status,
            diagnosis=diagnosis,
            error_message=initial_error,
        )

        record = RetryRecord(
            testIdentifier=test_identifier,
            testType=test_type,
            initialResult=initial_status,
            initialError=initial_error,
            retryEligible=eligible,
            eligibilityReason=reason,
            maxRetriesAllowed=limit,
            finalOutcome=FinalOutcome.PASSED_INITIALLY if initial_status == "PASSED" else (
                FinalOutcome.BLOCKED if initial_status == "BLOCKED" else FinalOutcome.RETRY_SKIPPED
            ),
        )

        if not eligible:
            logger.info(f"Skipping retry for '{test_identifier}': {reason}")
            if initial_status != "PASSED":
                record.humanReviewRecommendation = (
                    f"Automated retry skipped ({reason}). Manual human review required. "
                    "Autonomous code changes are disabled by policy."
                )
            return record

        # Perform controlled bounded retries
        current_status = initial_status
        for attempt_idx in range(1, limit + 1):
            backoff = self.backoff_base_seconds * (2 ** (attempt_idx - 1))
            logger.info(f"Controlled retry {attempt_idx}/{limit} for '{test_identifier}' after {backoff}s backoff...")
            await asyncio.sleep(backoff)

            t0 = time.time()
            try:
                res = await retry_fn()
                dur = time.time() - t0
                st = res.get("status", "FAILED").upper()
                err = res.get("error")

                diff = (
                    f"Status changed from {initial_status} to {st}"
                    if st != initial_status
                    else "Status remained FAILED"
                )

                attempt = RetryAttempt(
                    attemptNumber=attempt_idx,
                    executedAt=t0,
                    durationSeconds=round(dur, 3),
                    status=st,
                    error=err,
                    reason=f"Attempt {attempt_idx} after {backoff}s backoff",
                    diffFromInitial=diff,
                )
                record.attempts.append(attempt)
                record.attemptsCount = attempt_idx

                if st == "PASSED":
                    record.finalOutcome = FinalOutcome.PASSED_AFTER_RETRY
                    record.humanReviewRecommendation = (
                        f"Resolved after retry {attempt_idx}. Transient latency or race condition mitigated."
                    )
                    return record

            except Exception as exc:
                dur = time.time() - t0
                attempt = RetryAttempt(
                    attemptNumber=attempt_idx,
                    executedAt=t0,
                    durationSeconds=round(dur, 3),
                    status="FAILED",
                    error=str(exc),
                    reason=f"Attempt {attempt_idx} exception",
                    diffFromInitial=f"Exception: {str(exc)[:100]}",
                )
                record.attempts.append(attempt)
                record.attemptsCount = attempt_idx

        # If loop finishes without pass
        record.finalOutcome = FinalOutcome.STILL_FAILED
        record.humanReviewRecommendation = (
            f"Exhausted {limit} retries without resolution. Issue is persistent and requires human review. "
            "Self-healing controller preserved original failure evidence."
        )
        return record
