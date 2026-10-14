import os
import tempfile
import pytest

from backend.testing.security_scanner import (
    detect_security_tools,
    is_path_safe_to_scan,
    run_bandit_scan,
    run_pip_audit_scan,
    run_security_scans,
)


# =====================================================================
# 1. TOOL DETECTION TESTS
# =====================================================================

def test_detect_security_tools():
    tools = detect_security_tools()

    # Bandit must be detected
    assert "bandit" in tools
    assert tools["bandit"].available is True
    assert tools["bandit"].version is not None

    # pip-audit must be detected
    assert "pip-audit" in tools
    assert tools["pip-audit"].available is True
    assert tools["pip-audit"].version is not None

    # Semgrep must report unavailable cleanly without throwing unhandled exceptions
    assert "semgrep" in tools
    assert tools["semgrep"].available is False
    assert "not installed" in tools["semgrep"].error.lower()


# =====================================================================
# 2. PATH SAFETY TESTS
# =====================================================================

def test_is_path_safe_to_scan():
    # Sensitive and restricted paths must be rejected
    assert not is_path_safe_to_scan(".env")
    assert not is_path_safe_to_scan("project/.env")
    assert not is_path_safe_to_scan(".git/config")
    assert not is_path_safe_to_scan("node_modules/package/index.js")
    assert not is_path_safe_to_scan(".venv/lib/python3.13/site-packages")
    assert not is_path_safe_to_scan("venv/bin/activate")

    # Safe project files must be accepted
    assert is_path_safe_to_scan("agent_4_ui_script.py")
    assert is_path_safe_to_scan("src/components/App.jsx")
    assert is_path_safe_to_scan("backend/main.py")


def test_bandit_scan_rejects_restricted_path():
    findings, status = run_bandit_scan(".env")
    assert len(findings) == 0
    assert status.executed is False
    assert "restricted" in status.error.lower()


# =====================================================================
# 3. BANDIT EXECUTION ON CONTROLLED TEST FILES
# =====================================================================

def test_bandit_scan_detects_known_issues():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        # B101: assert_used
        f.write("def check():\n    assert True\n")
        temp_path = f.name

    try:
        findings, status = run_bandit_scan(temp_path)
        assert status.executed is True
        assert status.exitCode == 1  # 1 indicates issues found
        assert len(findings) >= 1
        rule_ids = [find.ruleId for find in findings]
        assert "B101" in rule_ids
        b101_issue = next(f for f in findings if f.ruleId == "B101")
        assert b101_issue.tool == "bandit"
        assert b101_issue.severity == "LOW"
        assert b101_issue.confidence == "HIGH"
        assert b101_issue.line == 2
        assert "assert" in b101_issue.description.lower()
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_bandit_scan_clean_code():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("def add(a: int, b: int) -> int:\n    return a + b\n")
        temp_path = f.name

    try:
        findings, status = run_bandit_scan(temp_path)
        assert status.executed is True
        assert status.exitCode == 0  # 0 indicates clean
        assert len(findings) == 0
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# =====================================================================
# 4. PIP-AUDIT EXECUTION TESTS
# =====================================================================

def test_pip_audit_scan_clean_requirements():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        # Secure, modern package with no known CVEs
        f.write("certifi==2024.12.14\n")
        req_path = f.name

    try:
        findings, status = run_pip_audit_scan(requirements_path=req_path, timeout=60)
        assert status.executed is True
        assert status.exitCode == 0
        assert len(findings) == 0
    finally:
        if os.path.exists(req_path):
            os.remove(req_path)


def test_pip_audit_scan_vulnerable_package():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        # Older package with known CVEs
        f.write("aiohttp==3.8.0\n")
        req_path = f.name

    try:
        findings, status = run_pip_audit_scan(requirements_path=req_path, timeout=60)
        assert status.executed is True
        assert status.exitCode == 1  # 1 indicates CVEs found
        assert len(findings) >= 1
        assert any("CVE-" in f.ruleId or "PYSEC-" in f.ruleId for f in findings)
        assert findings[0].tool == "pip-audit"
        assert findings[0].severity == "HIGH"
        assert "aiohttp" in findings[0].description.lower()
    finally:
        if os.path.exists(req_path):
            os.remove(req_path)


# =====================================================================
# 5. FULL SECURITY SCAN ORCHESTRATION TESTS
# =====================================================================

def test_run_security_scans_summary_generation():
    with tempfile.TemporaryDirectory() as temp_dir:
        test_py = os.path.join(temp_dir, "test_script.py")
        with open(test_py, "w") as f:
            f.write("def run():\n    assert 1 == 1\n")

        test_req = os.path.join(temp_dir, "requirements.txt")
        with open(test_req, "w") as f:
            f.write("certifi==2024.12.14\n")

        summary = run_security_scans(
            target_source_path=test_py,
            run_output_dir=temp_dir,
            requirements_path=test_req,
        )

        assert summary.tools["bandit"].executed is True
        assert summary.tools["pip-audit"].executed is True
        assert summary.tools["semgrep"].available is False
        assert summary.totalFindings >= 1
        assert summary.countsBySeverity["LOW"] >= 1
        assert os.path.exists(os.path.join(temp_dir, "agent_6_security_findings.json"))
        assert os.path.exists(os.path.join(temp_dir, "bandit_report.json"))
        assert os.path.exists(os.path.join(temp_dir, "pip_audit_report.json"))
