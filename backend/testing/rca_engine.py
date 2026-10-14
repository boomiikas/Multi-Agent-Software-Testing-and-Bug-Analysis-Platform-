from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class FailureCategory(str, Enum):
    APPLICATION_DEFECT = "APPLICATION_DEFECT"
    TEST_SCRIPT_ERROR = "TEST_SCRIPT_ERROR"
    INCORRECT_EXPECTATIONS = "INCORRECT_EXPECTATIONS"
    INFRASTRUCTURE_ISSUE = "INFRASTRUCTURE_ISSUE"
    AUTHENTICATION_PROBLEM = "AUTHENTICATION_PROBLEM"
    SECURITY_VULNERABILITY = "SECURITY_VULNERABILITY"
    UNKNOWN_CAUSE = "UNKNOWN_CAUSE"


class RcaDiagnosis(BaseModel):
    failureCategory: FailureCategory
    rootCauseHypothesis: str
    supportingEvidence: List[str] = Field(default_factory=list)
    artifactReferences: List[str] = Field(default_factory=list)
    confidence: str = "HIGH"  # HIGH, MEDIUM, LOW
    justification: str
    recommendedAction: str
    retryEligible: bool = False
    retryReason: str = "Non-retryable condition detected."
    isHypothesis: bool = True  # Distinguishes verified facts from hypotheses

    model_config = {"extra": "ignore"}


class RcaSummary(BaseModel):
    hasFailures: bool
    diagnoses: List[RcaDiagnosis] = Field(default_factory=list)
    totalDiagnoses: int = 0
    categoriesCount: Dict[str, int] = Field(default_factory=dict)
    retryableCount: int = 0
    nonRetryableCount: int = 0


def analyze_execution_evidence(
    ui_execution: Optional[Dict[str, Any]] = None,
    api_execution: Optional[Dict[str, Any]] = None,
    security_execution: Optional[Dict[str, Any]] = None,
    pipeline_error: Optional[str] = None,
    run_output_dir: Optional[str] = None,
) -> RcaSummary:
    """
    Analyzes verified evidence across Playwright, API tests, security scans,
    and pipeline logs to produce structured, evidence-based RCA diagnoses.
    """
    diagnoses: List[RcaDiagnosis] = []

    # 1. Pipeline Execution Errors
    if pipeline_error:
        err_lower = pipeline_error.lower()
        if "absent from the srs" in err_lower or "selector" in err_lower:
            diagnoses.append(
                RcaDiagnosis(
                    failureCategory=FailureCategory.TEST_SCRIPT_ERROR,
                    rootCauseHypothesis="UI automation generator produced selectors not declared in the approved SRS specification.",
                    supportingEvidence=[
                        f"Pipeline error trace: {pipeline_error[:200]}",
                        "Strict SRS selector validation blocked execution to prevent ungrounded UI automation.",
                    ],
                    artifactReferences=["agent_4_ui_script.py", "agent_1_requirements.txt"],
                    confidence="HIGH",
                    justification="Selector extraction directly verified discrepancy between generated script and declared SRS selectors.",
                    recommendedAction="Update the SRS document to declare the required element selectors or constrain generator prompt.",
                    retryEligible=False,
                    retryReason="Deterministic selector mismatch will not resolve on retry without updated requirements or prompts.",
                    isHypothesis=False,
                )
            )
        elif "security validation failed" in err_lower or "ssrf" in err_lower:
            diagnoses.append(
                RcaDiagnosis(
                    failureCategory=FailureCategory.SECURITY_VULNERABILITY,
                    rootCauseHypothesis="Target URL violated SSRF security policy by pointing to loopback, private subnet, or cloud metadata.",
                    supportingEvidence=[
                        f"Security rejection: {pipeline_error[:200]}",
                        "SSRF Destination Validator blocked request before transmission.",
                    ],
                    artifactReferences=[],
                    confidence="HIGH",
                    justification="IP destination analysis confirmed access violation to forbidden network perimeter.",
                    recommendedAction="Verify project target URL and ensure it points to an authorized public testing environment.",
                    retryEligible=False,
                    retryReason="SSRF security rejections must NEVER be retried.",
                    isHypothesis=False,
                )
            )
        elif "timeout" in err_lower:
            diagnoses.append(
                RcaDiagnosis(
                    failureCategory=FailureCategory.INFRASTRUCTURE_ISSUE,
                    rootCauseHypothesis="Pipeline stage exceeded execution timeout threshold.",
                    supportingEvidence=[f"Timeout message: {pipeline_error[:200]}"],
                    artifactReferences=[],
                    confidence="MEDIUM",
                    justification="Operation terminated prematurely before completing scheduled workload.",
                    recommendedAction="Check host CPU/GPU utilization, model service responsiveness, or network latency.",
                    retryEligible=True,
                    retryReason="Transient resource starvation or latency spike may resolve on subsequent attempt.",
                    isHypothesis=True,
                )
            )
        else:
            diagnoses.append(
                RcaDiagnosis(
                    failureCategory=FailureCategory.UNKNOWN_CAUSE,
                    rootCauseHypothesis=f"Pipeline error encountered during execution: {pipeline_error[:150]}",
                    supportingEvidence=[f"Raw trace excerpt: {pipeline_error[:300]}"],
                    artifactReferences=[],
                    confidence="LOW",
                    justification="Unclassified exception raised during pipeline orchestrator execution.",
                    recommendedAction="Inspect complete server logs for underlying exception trace.",
                    retryEligible=False,
                    retryReason="Unknown failures require root cause inspection before re-triggering.",
                    isHypothesis=True,
                )
            )

    # 2. UI Execution Evidence (Playwright)
    if ui_execution:
        ui_status = str(ui_execution.get("status", "")).upper()
        if ui_status == "FAILED":
            err_type = str(ui_execution.get("error_type", ""))
            err_msg = str(ui_execution.get("error_message", ""))
            err_combined = (err_type + " " + err_msg).lower()
            screenshot = ui_execution.get("screenshot")
            artifacts = [screenshot] if screenshot else []

            if "playwrighttimeouterror" in err_combined or "timeout" in err_combined:
                # Distinguish between element wait timeout vs network timeout
                if "waiting for locator" in err_combined or "wait_for" in err_combined:
                    diagnoses.append(
                        RcaDiagnosis(
                            failureCategory=FailureCategory.APPLICATION_DEFECT,
                            rootCauseHypothesis="Expected UI element was not rendered within timeout threshold (possible slow load or missing DOM node).",
                            supportingEvidence=[
                                f"Error type: {err_type}",
                                f"Error message: {err_msg[:250]}",
                            ],
                            artifactReferences=artifacts,
                            confidence="MEDIUM",
                            justification="Playwright timed out waiting for selector visibility on target page.",
                            recommendedAction="Check target application front-end state at failure screenshot and review element rendering latency.",
                            retryEligible=True,
                            retryReason="Transient rendering delay or network latency can be resolved with bounded retry.",
                            isHypothesis=True,
                        )
                    )
                else:
                    diagnoses.append(
                        RcaDiagnosis(
                            failureCategory=FailureCategory.INFRASTRUCTURE_ISSUE,
                            rootCauseHypothesis="Browser navigation or network request timed out reaching the target application.",
                            supportingEvidence=[
                                f"Timeout detail: {err_msg[:250]}",
                            ],
                            artifactReferences=artifacts,
                            confidence="MEDIUM",
                            justification="Target application did not respond to initial browser HTTP connection in time.",
                            recommendedAction="Confirm target server availability, DNS resolution, and network bandwidth.",
                            retryEligible=True,
                            retryReason="Transient network delay is eligible for single backoff retry.",
                            isHypothesis=True,
                        )
                    )
            elif "assertionerror" in err_combined or "assert" in err_combined:
                diagnoses.append(
                    RcaDiagnosis(
                        failureCategory=FailureCategory.APPLICATION_DEFECT,
                        rootCauseHypothesis="UI assertion failed: application state did not match expected value.",
                        supportingEvidence=[
                            f"Assertion error: {err_msg[:250]}",
                        ],
                        artifactReferences=artifacts,
                        confidence="HIGH",
                        justification="Explicit assert condition failed against live DOM inner text or attribute.",
                        recommendedAction="Verify whether application behavior changed intentionally or if a defect was introduced.",
                        retryEligible=False,
                        retryReason="Deterministic assertion discrepancy requires application code review or test expectation update.",
                        isHypothesis=False,
                    )
                )
            elif "auth" in err_combined or "401" in err_combined or "403" in err_combined or "login" in err_combined:
                diagnoses.append(
                    RcaDiagnosis(
                        failureCategory=FailureCategory.AUTHENTICATION_PROBLEM,
                        rootCauseHypothesis="Authentication failure during automated browser session.",
                        supportingEvidence=[
                            f"Auth failure details: {err_msg[:250]}",
                        ],
                        artifactReferences=artifacts,
                        confidence="HIGH",
                        justification="Login sequence failed to establish authenticated session.",
                        recommendedAction="Review target test user credentials configured in the SRS specification.",
                        retryEligible=False,
                        retryReason="Authentication rejections must NOT be retried with the same credentials.",
                        isHypothesis=False,
                    )
                )
            else:
                diagnoses.append(
                    RcaDiagnosis(
                        failureCategory=FailureCategory.TEST_SCRIPT_ERROR,
                        rootCauseHypothesis="Playwright script execution encountered an unhandled error.",
                        supportingEvidence=[
                            f"Script failure: {err_type}: {err_msg[:250]}",
                        ],
                        artifactReferences=artifacts,
                        confidence="MEDIUM",
                        justification="Exception occurred during execution of generated Playwright test script.",
                        recommendedAction="Review generated Python automation script syntax and target DOM structure.",
                        retryEligible=False,
                        retryReason="Script structure defects require regeneration or manual script correction.",
                        isHypothesis=True,
                    )
                )

    # 3. API Execution Evidence (HTTPX)
    if api_execution:
        tests = api_execution.get("tests", [])
        for t in tests:
            t_status = t.get("status")
            if t_status == "FAILED":
                act_status = t.get("actualStatus")
                exp_status = t.get("expectedStatus")
                endpoint = t.get("endpoint", "")
                method = t.get("method", "GET")
                error_msg = t.get("error", "")

                if act_status == 404:
                    diagnoses.append(
                        RcaDiagnosis(
                            failureCategory=FailureCategory.INCORRECT_EXPECTATIONS,
                            rootCauseHypothesis=f"API endpoint '{endpoint}' returned 404 Not Found (route does not exist on target).",
                            supportingEvidence=[
                                f"Request: {method} {endpoint}",
                                f"Actual status: {act_status} | Expected: {exp_status}",
                            ],
                            artifactReferences=["agent_5_api_execution.json"],
                            confidence="HIGH",
                            justification="Target HTTP server responded with 404 Not Found header.",
                            recommendedAction="Update API test specification with valid route paths from Swagger / OpenAPI spec.",
                            retryEligible=False,
                            retryReason="Non-existent endpoints will not become available on immediate retry.",
                            isHypothesis=False,
                        )
                    )
                elif act_status in (401, 403):
                    diagnoses.append(
                        RcaDiagnosis(
                            failureCategory=FailureCategory.AUTHENTICATION_PROBLEM,
                            rootCauseHypothesis=f"API endpoint '{endpoint}' returned HTTP {act_status} Unauthorized / Forbidden.",
                            supportingEvidence=[
                                f"Request: {method} {endpoint}",
                                f"Status: {act_status} (Access Denied)",
                            ],
                            artifactReferences=["agent_5_api_execution.json"],
                            confidence="HIGH",
                            justification="Endpoint requires valid authorization credentials or scopes.",
                            recommendedAction="Configure authorized test tokens or headers for secured endpoints.",
                            retryEligible=False,
                            retryReason="Authorization failures must not be retried without updated credentials.",
                            isHypothesis=False,
                        )
                    )
                elif act_status and act_status >= 500:
                    diagnoses.append(
                        RcaDiagnosis(
                            failureCategory=FailureCategory.APPLICATION_DEFECT,
                            rootCauseHypothesis=f"Target backend returned HTTP {act_status} Server Error on {method} {endpoint}.",
                            supportingEvidence=[
                                f"Request: {method} {endpoint}",
                                f"HTTP status code: {act_status}",
                                f"Response error: {error_msg[:150] if error_msg else 'Internal Server Error'}",
                            ],
                            artifactReferences=["agent_5_api_execution.json"],
                            confidence="HIGH",
                            justification="Server error response directly indicates an unhandled server-side exception or crash.",
                            recommendedAction="Investigate target application server logs for unhandled exception or 5xx crash.",
                            retryEligible=False,
                            retryReason="Deterministic server errors require backend code fix.",
                            isHypothesis=False,
                        )
                    )
                elif "timeout" in (error_msg or "").lower():
                    diagnoses.append(
                        RcaDiagnosis(
                            failureCategory=FailureCategory.INFRASTRUCTURE_ISSUE,
                            rootCauseHypothesis=f"API request to '{endpoint}' timed out reaching target server.",
                            supportingEvidence=[
                                f"Endpoint: {method} {endpoint}",
                                f"Error: {error_msg[:200]}",
                            ],
                            artifactReferences=["agent_5_api_execution.json"],
                            confidence="MEDIUM",
                            justification="HTTP client timed out waiting for socket response.",
                            recommendedAction="Check target API latency, server load, and gateway response times.",
                            retryEligible=True,
                            retryReason="Transient API timeout eligible for backoff retry.",
                            isHypothesis=True,
                        )
                    )
            elif t_status == "BLOCKED":
                diagnoses.append(
                    RcaDiagnosis(
                        failureCategory=FailureCategory.SECURITY_VULNERABILITY,
                        rootCauseHypothesis=f"API request to '{t.get('url')}' was blocked by SSRF protection filter.",
                        supportingEvidence=[
                            f"URL: {t.get('url')}",
                            f"Block reason: {t.get('error', 'Forbidden destination IP')}",
                        ],
                        artifactReferences=["agent_5_api_execution.json"],
                        confidence="HIGH",
                        justification="Target IP matched private/reserved subnet or loopback range.",
                        recommendedAction="Ensure target URL is an authorized public endpoint.",
                        retryEligible=False,
                        retryReason="SSRF blocks must NEVER be retried.",
                        isHypothesis=False,
                    )
                )

    # 4. Security Scanning Evidence (Bandit & pip-audit)
    if security_execution:
        findings = security_execution.get("findings", [])
        for f in findings:
            sev = f.get("severity", "LOW")
            if sev in ("HIGH", "CRITICAL"):
                diagnoses.append(
                    RcaDiagnosis(
                        failureCategory=FailureCategory.SECURITY_VULNERABILITY,
                        rootCauseHypothesis=f"Security vulnerability detected by {f.get('tool', 'scanner').upper()}: {f.get('ruleId')} ({sev}).",
                        supportingEvidence=[
                            f"Rule ID: {f.get('ruleId')}",
                            f"Description: {f.get('description', '')[:200]}",
                            f"Location: {f.get('file')}:{f.get('line')}",
                        ],
                        artifactReferences=[f"{f.get('tool')}_report.json"],
                        confidence="HIGH",
                        justification="Static analysis or dependency audit identified a known CVE or severe security flaw.",
                        recommendedAction=f"Apply remediation: {f.get('remediation', 'Upgrade dependency or remediate code flaw')}.",
                        retryEligible=False,
                        retryReason="Deterministic security vulnerabilities will not be resolved by retrying the test.",
                        isHypothesis=False,
                    )
                )

    # Summary tallies
    categories_count: Dict[str, int] = {}
    retryable = 0
    non_retryable = 0
    for d in diagnoses:
        cat = d.failureCategory.value
        categories_count[cat] = categories_count.get(cat, 0) + 1
        if d.retryEligible:
            retryable += 1
        else:
            non_retryable += 1

    return RcaSummary(
        hasFailures=len(diagnoses) > 0,
        diagnoses=diagnoses,
        totalDiagnoses=len(diagnoses),
        categoriesCount=categories_count,
        retryableCount=retryable,
        nonRetryableCount=non_retryable,
    )
