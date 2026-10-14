import json
import re
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import httpx
from pydantic import BaseModel, Field

from ..security.url_validator import is_safe_target_url
from ..config import settings


SENSITIVE_HEADER_KEYS = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "api-key",
    "token",
    "x-auth-token",
    "secret",
}

SENSITIVE_BODY_KEYS = {
    "password",
    "pass",
    "secret",
    "token",
    "key",
    "credentials",
    "access_token",
    "refresh_token",
}


def sanitize_headers(headers: Dict[str, Any]) -> Dict[str, str]:
    """Redacts sensitive headers like Authorization and Cookies."""
    sanitized = {}
    for k, v in headers.items():
        if k.lower() in SENSITIVE_HEADER_KEYS:
            sanitized[k] = "[REDACTED]"
        else:
            sanitized[k] = str(v)
    return sanitized


def sanitize_data(data: Any) -> Any:
    """Recursively redacts sensitive keys from request/response JSON objects."""
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            if any(s in k.lower() for s in SENSITIVE_BODY_KEYS):
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = sanitize_data(v)
        return cleaned
    elif isinstance(data, list):
        return [sanitize_data(item) for item in data]
    return data


class ApiTestCase(BaseModel):
    name: str = "API Test"
    method: str = "GET"
    endpoint: str = "/"
    headers: Dict[str, str] = Field(default_factory=dict)
    params: Dict[str, str] = Field(default_factory=dict)
    body: Optional[Any] = None
    expectedStatus: int = 200
    expectedContentType: Optional[str] = None
    maxResponseTimeMs: float = 5000.0


class ApiAssertionResult(BaseModel):
    name: str
    passed: bool
    expected: Any
    actual: Any
    message: Optional[str] = None


class ApiTestResult(BaseModel):
    name: str
    method: str
    url: str
    status: str  # "PASSED", "FAILED", "SKIPPED", "BLOCKED"
    actualStatus: Optional[int] = None
    responseTimeMs: Optional[float] = None
    assertions: List[ApiAssertionResult] = Field(default_factory=list)
    requestHeaders: Dict[str, str] = Field(default_factory=dict)
    responseSnippet: Optional[str] = None
    error: Optional[str] = None


class ApiExecutionSummary(BaseModel):
    total: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    blocked: int = 0
    tests: List[ApiTestResult] = Field(default_factory=list)
    durationSeconds: float = 0.0
    limitation: Optional[str] = None
    targetBaseUrl: str = ""


def extract_api_test_cases(raw_text: str, base_url: str) -> List[ApiTestCase]:
    """
    Safely extracts and validates structured API test cases from Agent 5 text or JSON.
    Returns an empty list if no valid structured format is found.
    """
    if not raw_text or not isinstance(raw_text, str):
        return []

    # 1. Try finding JSON code block ```json ... ```
    json_str = None
    if "```json" in raw_text:
        match = re.search(r"```json\s*(.*?)\s*```", raw_text, re.DOTALL)
        if match:
            json_str = match.group(1).strip()
    elif raw_text.strip().startswith("[") or raw_text.strip().startswith("{"):
        json_str = raw_text.strip()

    parsed_cases: List[ApiTestCase] = []
    if json_str:
        try:
            data = json.loads(json_str)
            if isinstance(data, dict) and "test_cases" in data:
                data = data["test_cases"]
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        # Normalize method and endpoint
                        method = (item.get("method") or item.get("http_method") or "GET").upper()
                        endpoint = item.get("endpoint") or item.get("url") or item.get("path") or "/"
                        name = item.get("name") or item.get("title") or f"{method} {endpoint}"
                        expected_status = item.get("expected_status") or item.get("expectedStatus") or 200
                        try:
                            expected_status = int(expected_status)
                        except (ValueError, TypeError):
                            expected_status = 200

                        parsed_cases.append(
                            ApiTestCase(
                                name=name,
                                method=method,
                                endpoint=endpoint,
                                headers=item.get("headers") or {},
                                params=item.get("params") or item.get("query_params") or {},
                                body=item.get("body") or item.get("payload"),
                                expectedStatus=expected_status,
                                maxResponseTimeMs=float(item.get("max_response_time_ms") or 5000.0),
                            )
                        )
        except Exception:
            pass

    return parsed_cases


async def execute_single_api_test(
    test_case: ApiTestCase,
    base_url: str,
    client: httpx.AsyncClient,
    allow_local: Optional[bool] = None,
    max_response_bytes: int = 1024 * 1024,  # 1MB limit
) -> ApiTestResult:
    """
    Executes a single validated API test case with strict SSRF and assertion verification.
    """
    method = test_case.method.upper()
    endpoint = test_case.endpoint

    # Build destination URL
    if endpoint.startswith("http://") or endpoint.startswith("https://"):
        full_url = endpoint
    else:
        full_url = urljoin(base_url.rstrip("/") + "/", endpoint.lstrip("/"))

    sanitized_req_headers = sanitize_headers(test_case.headers)

    # 1. SSRF Validation on destination
    is_safe, ssrf_err = is_safe_target_url(full_url, allow_local=allow_local)
    if not is_safe:
        return ApiTestResult(
            name=test_case.name,
            method=method,
            url=full_url,
            status="BLOCKED",
            error=f"Blocked by SSRF policy: {ssrf_err}",
            requestHeaders=sanitized_req_headers,
        )

    assertions: List[ApiAssertionResult] = []
    start_time = time.time()

    try:
        req_headers = dict(test_case.headers)
        # Ensure a standard User-Agent identifying our platform
        if "user-agent" not in [k.lower() for k in req_headers]:
            req_headers["User-Agent"] = "AgentQA-ApiTester/1.0"

        # Execute request without auto-following redirects so we can validate redirect destinations
        response = await client.request(
            method=method,
            url=full_url,
            headers=req_headers,
            params=test_case.params or None,
            json=test_case.body if test_case.body is not None and method in ("POST", "PUT", "PATCH") else None,
        )

        response_time_ms = round((time.time() - start_time) * 1000, 2)

        # 2. Redirect destination SSRF validation if 3xx
        if response.status_code in (301, 302, 303, 307, 308) and "location" in response.headers:
            redirect_target = urljoin(full_url, response.headers["location"])
            is_redirect_safe, redir_err = is_safe_target_url(redirect_target, allow_local=allow_local)
            if not is_redirect_safe:
                return ApiTestResult(
                    name=test_case.name,
                    method=method,
                    url=full_url,
                    status="BLOCKED",
                    actualStatus=response.status_code,
                    responseTimeMs=response_time_ms,
                    error=f"Redirect destination blocked by SSRF policy: {redir_err}",
                    requestHeaders=sanitized_req_headers,
                )

        # 3. Assertions
        # Status code assertion
        status_passed = (response.status_code == test_case.expectedStatus)
        assertions.append(
            ApiAssertionResult(
                name="Status Code Check",
                passed=status_passed,
                expected=test_case.expectedStatus,
                actual=response.status_code,
                message=None if status_passed else f"Expected status {test_case.expectedStatus}, got {response.status_code}",
            )
        )

        # Response time threshold assertion
        time_passed = (response_time_ms <= test_case.maxResponseTimeMs)
        assertions.append(
            ApiAssertionResult(
                name="Response Time Threshold",
                passed=time_passed,
                expected=f"<={test_case.maxResponseTimeMs}ms",
                actual=f"{response_time_ms}ms",
                message=None if time_passed else f"Response time {response_time_ms}ms exceeded limit {test_case.maxResponseTimeMs}ms",
            )
        )

        # Expected content-type assertion (if configured)
        if test_case.expectedContentType:
            actual_ct = response.headers.get("content-type", "")
            ct_passed = test_case.expectedContentType.lower() in actual_ct.lower()
            assertions.append(
                ApiAssertionResult(
                    name="Content-Type Check",
                    passed=ct_passed,
                    expected=test_case.expectedContentType,
                    actual=actual_ct,
                    message=None if ct_passed else f"Content-Type '{actual_ct}' did not match '{test_case.expectedContentType}'",
                )
            )

        # Capture response snippet safely (size limited and sanitized)
        resp_bytes = response.content[:max_response_bytes]
        try:
            resp_json = response.json()
            cleaned_json = sanitize_data(resp_json)
            snippet = json.dumps(cleaned_json)[:1000]
        except Exception:
            snippet = resp_bytes.decode("utf-8", errors="replace")[:500]

        all_assertions_passed = all(a.passed for a in assertions)

        return ApiTestResult(
            name=test_case.name,
            method=method,
            url=full_url,
            status="PASSED" if all_assertions_passed else "FAILED",
            actualStatus=response.status_code,
            responseTimeMs=response_time_ms,
            assertions=assertions,
            requestHeaders=sanitized_req_headers,
            responseSnippet=snippet,
        )

    except httpx.TimeoutException:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        return ApiTestResult(
            name=test_case.name,
            method=method,
            url=full_url,
            status="FAILED",
            responseTimeMs=duration_ms,
            error=f"Request timed out after {duration_ms}ms",
            requestHeaders=sanitized_req_headers,
        )
    except Exception as e:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        return ApiTestResult(
            name=test_case.name,
            method=method,
            url=full_url,
            status="FAILED",
            responseTimeMs=duration_ms,
            error=f"Network error: {str(e)}",
            requestHeaders=sanitized_req_headers,
        )


async def run_real_api_tests(
    target_url: str,
    test_cases_or_text: Any,
    allow_local: Optional[bool] = None,
    max_requests: int = 20,
    timeout_seconds: float = 10.0,
) -> ApiExecutionSummary:
    """
    Main entry point for Agent 5 real API testing.
    Executes actual, controlled HTTP requests against verified endpoints.
    """
    start_total = time.time()

    # 1. SSRF check on base target URL
    is_safe, err = is_safe_target_url(target_url, allow_local=allow_local)
    if not is_safe:
        return ApiExecutionSummary(
            total=0,
            blocked=1,
            limitation=f"Target URL rejected by SSRF security policy: {err}",
            targetBaseUrl=target_url,
        )

    # 2. Extract or parse test cases
    if isinstance(test_cases_or_text, list):
        cases: List[ApiTestCase] = []
        for item in test_cases_or_text:
            if isinstance(item, ApiTestCase):
                cases.append(item)
            elif isinstance(item, dict):
                cases.append(ApiTestCase(**item))
    elif isinstance(test_cases_or_text, str):
        cases = extract_api_test_cases(test_cases_or_text, target_url)
    else:
        cases = []

    # If no structured test cases could be parsed from Agent 5 LLM output,
    # generate a safe basic probe (e.g. GET base URL / health / root) so we test live
    if not cases:
        # Check if root endpoint can be probed safely
        parsed = urlparse(target_url)
        root_path = parsed.path if parsed.path else "/"
        cases = [
            ApiTestCase(
                name="Application Root Endpoint Reachability",
                method="GET",
                endpoint=root_path,
                expectedStatus=200,
                maxResponseTimeMs=5000.0,
            )
        ]
        limitation_note = (
            "No structured API specification was extracted from SRS text. "
            "Executed baseline reachability check only; aggressive endpoint crawling was omitted."
        )
    else:
        limitation_note = None

    # Apply request cap to prevent flooding
    capped_cases = cases[:max_requests]

    results: List[ApiTestResult] = []
    async with httpx.AsyncClient(timeout=timeout_seconds, follow_redirects=False) as client:
        for case in capped_cases:
            res = await execute_single_api_test(case, target_url, client, allow_local=allow_local)
            results.append(res)

    duration = round(time.time() - start_total, 2)
    passed_count = sum(1 for r in results if r.status == "PASSED")
    failed_count = sum(1 for r in results if r.status == "FAILED")
    skipped_count = sum(1 for r in results if r.status == "SKIPPED")
    blocked_count = sum(1 for r in results if r.status == "BLOCKED")

    return ApiExecutionSummary(
        total=len(results),
        passed=passed_count,
        failed=failed_count,
        skipped=skipped_count,
        blocked=blocked_count,
        tests=results,
        durationSeconds=duration,
        limitation=limitation_note,
        targetBaseUrl=target_url,
    )
