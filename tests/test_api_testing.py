import pytest
import httpx
from unittest.mock import AsyncMock, patch

from backend.testing.api_executor import (
    sanitize_headers,
    sanitize_data,
    extract_api_test_cases,
    execute_single_api_test,
    run_real_api_tests,
    ApiTestCase,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


# =====================================================================
# 1. SANITIZATION TESTS
# =====================================================================

def test_sanitize_headers():
    headers = {
        "Authorization": "Bearer super-secret-jwt-token",
        "Cookie": "session_id=xyz123",
        "X-Api-Key": "secret-api-key-999",
        "Content-Type": "application/json",
        "User-Agent": "TestClient/1.0",
    }
    cleaned = sanitize_headers(headers)
    assert cleaned["Authorization"] == "[REDACTED]"
    assert cleaned["Cookie"] == "[REDACTED]"
    assert cleaned["X-Api-Key"] == "[REDACTED]"
    assert cleaned["Content-Type"] == "application/json"
    assert cleaned["User-Agent"] == "TestClient/1.0"


def test_sanitize_data():
    payload = {
        "user": {
            "username": "alice",
            "password": "Password@123",
            "accessToken": "secret-jwt-456",
        },
        "meta": [
            {"token": "xyz", "active": True},
            {"role": "admin"}
        ]
    }
    cleaned = sanitize_data(payload)
    assert cleaned["user"]["username"] == "alice"
    assert cleaned["user"]["password"] == "[REDACTED]"
    assert cleaned["user"]["accessToken"] == "[REDACTED]"
    assert cleaned["meta"][0]["token"] == "[REDACTED]"
    assert cleaned["meta"][0]["active"] is True
    assert cleaned["meta"][1]["role"] == "admin"


# =====================================================================
# 2. TEST CASE EXTRACTION TESTS
# =====================================================================

def test_extract_api_test_cases_from_markdown():
    markdown_text = """
Here are the extracted test cases:
```json
[
  {
    "name": "User Login",
    "method": "POST",
    "endpoint": "/api/v1/auth/login",
    "expected_status": 200,
    "body": {"username": "standard_user"}
  },
  {
    "name": "Get Inventory",
    "method": "GET",
    "endpoint": "/api/v1/inventory",
    "expected_status": 200
  }
]
```
These cover the main flows.
"""
    cases = extract_api_test_cases(markdown_text, "https://api.example.com")
    assert len(cases) == 2
    assert cases[0].name == "User Login"
    assert cases[0].method == "POST"
    assert cases[0].endpoint == "/api/v1/auth/login"
    assert cases[0].expectedStatus == 200
    assert cases[1].name == "Get Inventory"
    assert cases[1].method == "GET"


def test_extract_api_test_cases_empty_or_invalid():
    assert extract_api_test_cases("", "https://example.com") == []
    assert extract_api_test_cases("No json code block here", "https://example.com") == []
    assert extract_api_test_cases("```json\ninvalid json\n```", "https://example.com") == []


# =====================================================================
# 3. HTTP EXECUTION AND ASSERTION TESTS
# =====================================================================

@pytest.mark.anyio
async def test_execute_single_api_test_passed():
    case = ApiTestCase(
        name="Get User Profile",
        method="GET",
        endpoint="/api/profile",
        expectedStatus=200,
        expectedContentType="application/json",
    )

    mock_response = httpx.Response(
        status_code=200,
        headers={"content-type": "application/json; charset=utf-8"},
        json={"id": 1, "username": "alice", "password": "supersecret"},
        request=httpx.Request("GET", "https://example.com/api/profile"),
    )

    client = AsyncMock()
    client.request.return_value = mock_response

    result = await execute_single_api_test(case, "https://example.com", client)

    assert result.status == "PASSED"
    assert result.actualStatus == 200
    assert len(result.assertions) >= 2
    assert all(a.passed for a in result.assertions)
    # Check that sensitive fields were redacted in snippet
    assert "[REDACTED]" in result.responseSnippet


@pytest.mark.anyio
async def test_execute_single_api_test_failed_status():
    case = ApiTestCase(
        name="Missing Endpoint",
        method="GET",
        endpoint="/api/nonexistent",
        expectedStatus=200,
    )

    mock_response = httpx.Response(
        status_code=404,
        text="Not Found",
        request=httpx.Request("GET", "https://example.com/api/nonexistent"),
    )

    client = AsyncMock()
    client.request.return_value = mock_response

    result = await execute_single_api_test(case, "https://example.com", client)

    assert result.status == "FAILED"
    assert result.actualStatus == 404
    assert any(a.name == "Status Code Check" and not a.passed for a in result.assertions)


@pytest.mark.anyio
async def test_execute_single_api_test_ssrf_blocked():
    case = ApiTestCase(
        name="Internal Cloud Metadata Exploit",
        method="GET",
        endpoint="http://169.254.169.254/latest/meta-data/",
    )
    client = AsyncMock()

    result = await execute_single_api_test(case, "https://example.com", client, allow_local=False)

    assert result.status == "BLOCKED"
    assert "Blocked by SSRF policy" in result.error
    # Client request must not have been executed
    client.request.assert_not_called()


@pytest.mark.anyio
async def test_execute_single_api_test_redirect_ssrf_blocked():
    case = ApiTestCase(
        name="SSRF via Open Redirect",
        method="GET",
        endpoint="/redirect-me",
        expectedStatus=200,
    )

    # Server responds with 302 pointing to cloud metadata IP
    mock_redirect = httpx.Response(
        status_code=302,
        headers={"location": "http://169.254.169.254/latest/meta-data/"},
        request=httpx.Request("GET", "https://example.com/redirect-me"),
    )
    client = AsyncMock()
    client.request.return_value = mock_redirect

    result = await execute_single_api_test(case, "https://example.com", client, allow_local=False)

    assert result.status == "BLOCKED"
    assert "Redirect destination blocked by SSRF policy" in result.error


@pytest.mark.anyio
async def test_execute_single_api_test_timeout():
    case = ApiTestCase(
        name="Slow Endpoint Timeout",
        method="GET",
        endpoint="/slow",
    )
    client = AsyncMock()
    client.request.side_effect = httpx.TimeoutException("Read timed out")

    result = await execute_single_api_test(case, "https://example.com", client)

    assert result.status == "FAILED"
    assert "timed out" in result.error.lower()


# =====================================================================
# 4. FULL SUITE ORCHESTRATION TESTS
# =====================================================================

@pytest.mark.anyio
async def test_run_real_api_tests_summary():
    test_cases = [
        {"name": "Test 1", "method": "GET", "endpoint": "/t1", "expectedStatus": 200},
        {"name": "Test 2", "method": "POST", "endpoint": "/t2", "expectedStatus": 201},
        {"name": "Test 3", "method": "GET", "endpoint": "http://169.254.169.254", "expectedStatus": 200},
    ]

    with patch("backend.testing.api_executor.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client

        # Mock responses: t1 -> 200 (pass), t2 -> 500 (fail)
        def side_effect(method, url, **kwargs):
            if "/t1" in url:
                return httpx.Response(200, json={"ok": True}, request=httpx.Request(method, url))
            elif "/t2" in url:
                return httpx.Response(500, text="Server Error", request=httpx.Request(method, url))
            return httpx.Response(404, request=httpx.Request(method, url))

        mock_client.request.side_effect = side_effect

        summary = await run_real_api_tests("https://example.com", test_cases, allow_local=False)

        assert summary.total == 3
        assert summary.passed == 1
        assert summary.failed == 1
        assert summary.blocked == 1
        assert summary.durationSeconds >= 0.0
