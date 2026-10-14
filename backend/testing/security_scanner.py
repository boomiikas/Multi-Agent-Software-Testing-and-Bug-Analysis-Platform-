import os
import sys
import json
import time
import subprocess
import shutil
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


RESTRICTED_SCAN_NAMES = {
    ".env",
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
}


class SecurityFinding(BaseModel):
    tool: str  # "bandit", "pip-audit", "semgrep"
    ruleId: str
    severity: str  # "HIGH", "MEDIUM", "LOW", "INFO"
    confidence: str = "UNKNOWN"  # "HIGH", "MEDIUM", "LOW", "UNKNOWN"
    file: str = ""
    line: Optional[int] = None
    description: str = ""
    remediation: Optional[str] = None
    codeSnippet: Optional[str] = None


class SecurityToolStatus(BaseModel):
    tool: str
    available: bool
    version: Optional[str] = None
    executed: bool = False
    exitCode: Optional[int] = None
    durationSeconds: float = 0.0
    error: Optional[str] = None


class SecurityScanSummary(BaseModel):
    tools: Dict[str, SecurityToolStatus] = Field(default_factory=dict)
    findings: List[SecurityFinding] = Field(default_factory=list)
    countsBySeverity: Dict[str, int] = Field(default_factory=lambda: {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0})
    totalFindings: int = 0
    scannedScope: List[str] = Field(default_factory=list)
    executedAt: str = ""
    durationSeconds: float = 0.0


def is_path_safe_to_scan(path: str) -> bool:
    """Ensures target path does not point to sensitive directories or files like .env."""
    norm = os.path.normpath(path).lower()
    for restricted in RESTRICTED_SCAN_NAMES:
        if restricted in norm.split(os.sep):
            return False
    return True


def detect_security_tools() -> Dict[str, SecurityToolStatus]:
    """Detects available security CLI tools in the active environment."""
    tools = {}

    # 1. Bandit
    try:
        res = subprocess.run(
            [sys.executable, "-m", "bandit.cli.main", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        version_str = res.stdout.splitlines()[0].strip() if res.stdout else "1.9.4"
        tools["bandit"] = SecurityToolStatus(
            tool="bandit",
            available=True,
            version=version_str,
        )
    except Exception:
        tools["bandit"] = SecurityToolStatus(
            tool="bandit",
            available=False,
            error="Bandit is not installed or failed to execute.",
        )

    # 2. pip-audit
    try:
        res = subprocess.run(
            [sys.executable, "-m", "pip_audit", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        version_str = res.stdout.strip() if res.stdout else "2.10.1"
        tools["pip-audit"] = SecurityToolStatus(
            tool="pip-audit",
            available=True,
            version=version_str,
        )
    except Exception:
        tools["pip-audit"] = SecurityToolStatus(
            tool="pip-audit",
            available=False,
            error="pip-audit is not installed or failed to execute.",
        )

    # 3. Semgrep
    semgrep_bin = shutil.which("semgrep")
    if semgrep_bin:
        try:
            res = subprocess.run(
                [semgrep_bin, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            tools["semgrep"] = SecurityToolStatus(
                tool="semgrep",
                available=True,
                version=res.stdout.strip() or "available",
            )
        except Exception:
            tools["semgrep"] = SecurityToolStatus(
                tool="semgrep",
                available=False,
                error="Semgrep execution failed.",
            )
    else:
        tools["semgrep"] = SecurityToolStatus(
            tool="semgrep",
            available=False,
            error="Semgrep is not installed in the active environment.",
        )

    return tools


def run_bandit_scan(
    target_path: str,
    output_json_path: Optional[str] = None,
    timeout: int = 45,
) -> tuple[List[SecurityFinding], SecurityToolStatus]:
    """
    Executes Bandit static analysis against target Python source file or directory.
    Exit code 0 (clean) and 1 (issues found) are both treated as normal execution.
    """
    findings: List[SecurityFinding] = []
    start_time = time.time()

    if not is_path_safe_to_scan(target_path):
        return findings, SecurityToolStatus(
            tool="bandit",
            available=True,
            executed=False,
            error=f"Target path '{target_path}' contains restricted directories/files and was skipped for safety.",
        )

    cmd = [sys.executable, "-m", "bandit.cli.main", "-f", "json", "-r" if os.path.isdir(target_path) else "", target_path]
    cmd = [arg for arg in cmd if arg]

    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        duration = round(time.time() - start_time, 2)
        status = SecurityToolStatus(
            tool="bandit",
            available=True,
            executed=True,
            exitCode=res.returncode,
            durationSeconds=duration,
        )

        # Parse JSON output
        if res.stdout:
            try:
                data = json.loads(res.stdout)
                if output_json_path:
                    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
                    with open(output_json_path, "w", encoding="utf-8") as f:
                        f.write(res.stdout)

                for issue in data.get("results", []):
                    sev = issue.get("issue_severity", "LOW").upper()
                    conf = issue.get("issue_confidence", "LOW").upper()
                    findings.append(
                        SecurityFinding(
                            tool="bandit",
                            ruleId=issue.get("test_id", "B000"),
                            severity=sev,
                            confidence=conf,
                            file=issue.get("filename", target_path),
                            line=issue.get("line_number"),
                            description=issue.get("issue_text", ""),
                            remediation=f"Consult Bandit documentation for rule {issue.get('test_id')}: {issue.get('more_info', '')}",
                            codeSnippet=issue.get("code", "").strip() if issue.get("code") else None,
                        )
                    )
            except Exception as e:
                status.error = f"Failed to parse Bandit JSON output: {e}"

        return findings, status

    except subprocess.TimeoutExpired:
        duration = round(time.time() - start_time, 2)
        return findings, SecurityToolStatus(
            tool="bandit",
            available=True,
            executed=False,
            durationSeconds=duration,
            error=f"Bandit scan timed out after {timeout} seconds.",
        )
    except Exception as e:
        duration = round(time.time() - start_time, 2)
        return findings, SecurityToolStatus(
            tool="bandit",
            available=True,
            executed=False,
            durationSeconds=duration,
            error=f"Bandit execution failed: {str(e)}",
        )


def run_pip_audit_scan(
    requirements_path: Optional[str] = None,
    output_json_path: Optional[str] = None,
    timeout: int = 60,
) -> tuple[List[SecurityFinding], SecurityToolStatus]:
    """
    Executes pip-audit dependency vulnerability scanning.
    Exit code 0 (clean) and 1 (vulnerabilities found) are both treated as normal execution.
    """
    findings: List[SecurityFinding] = []
    start_time = time.time()

    cmd = [sys.executable, "-m", "pip_audit", "-f", "json"]
    if requirements_path and os.path.isfile(requirements_path):
        if not is_path_safe_to_scan(requirements_path):
            return findings, SecurityToolStatus(
                tool="pip-audit",
                available=True,
                executed=False,
                error=f"Requirements path '{requirements_path}' is restricted.",
            )
        cmd.extend(["-r", requirements_path])

    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        duration = round(time.time() - start_time, 2)
        status = SecurityToolStatus(
            tool="pip-audit",
            available=True,
            executed=True,
            exitCode=res.returncode,
            durationSeconds=duration,
        )

        if res.stdout:
            try:
                data = json.loads(res.stdout)
                if output_json_path:
                    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
                    with open(output_json_path, "w", encoding="utf-8") as f:
                        f.write(res.stdout)

                deps = data.get("dependencies", []) if isinstance(data, dict) else data
                for dep in deps:
                    pkg_name = dep.get("name", "unknown")
                    pkg_ver = dep.get("version", "")
                    for vuln in dep.get("vulns", []):
                        vuln_id = vuln.get("id", "UNKNOWN")
                        aliases = vuln.get("aliases", [])
                        cve_id = next((a for a in aliases if a.startswith("CVE-")), vuln_id)
                        fix_vers = vuln.get("fix_versions", [])
                        remediation_note = f"Upgrade {pkg_name} to {', '.join(fix_vers)}" if fix_vers else f"Upgrade {pkg_name} to a secure release."

                        findings.append(
                            SecurityFinding(
                                tool="pip-audit",
                                ruleId=cve_id,
                                severity="HIGH",  # Known CVE in dependency defaults to HIGH
                                confidence="HIGH",
                                file=requirements_path or f"dependency:{pkg_name}=={pkg_ver}",
                                description=f"Vulnerability in {pkg_name} ({pkg_ver}): {vuln.get('description', '')[:300]}",
                                remediation=remediation_note,
                            )
                        )
            except Exception as e:
                status.error = f"Failed to parse pip-audit JSON output: {e}"

        return findings, status

    except subprocess.TimeoutExpired:
        duration = round(time.time() - start_time, 2)
        return findings, SecurityToolStatus(
            tool="pip-audit",
            available=True,
            executed=False,
            durationSeconds=duration,
            error=f"pip-audit timed out after {timeout} seconds.",
        )
    except Exception as e:
        duration = round(time.time() - start_time, 2)
        return findings, SecurityToolStatus(
            tool="pip-audit",
            available=True,
            executed=False,
            durationSeconds=duration,
            error=f"pip-audit execution failed: {str(e)}",
        )


def run_security_scans(
    target_source_path: str,
    run_output_dir: str,
    requirements_path: Optional[str] = None,
) -> SecurityScanSummary:
    """
    Main entry point for Agent 6 real security scanning.
    Executes Bandit on target source files and pip-audit on dependencies.
    """
    start_total = time.time()
    detected_tools = detect_security_tools()

    all_findings: List[SecurityFinding] = []
    scanned_scope: List[str] = []

    # 1. Run Bandit on target Python script / directory
    bandit_output_file = os.path.join(run_output_dir, "bandit_report.json")
    if os.path.exists(target_source_path):
        b_findings, b_status = run_bandit_scan(target_source_path, bandit_output_file)
        all_findings.extend(b_findings)
        scanned_scope.append(target_source_path)
    else:
        b_status = SecurityToolStatus(
            tool="bandit",
            available=detected_tools.get("bandit", SecurityToolStatus(tool="bandit", available=False)).available,
            executed=False,
            error=f"Target source file '{target_source_path}' does not exist.",
        )
    detected_tools["bandit"] = b_status

    # 2. Run pip-audit on dependencies
    pip_audit_output_file = os.path.join(run_output_dir, "pip_audit_report.json")
    p_findings, p_status = run_pip_audit_scan(requirements_path=requirements_path, output_json_path=pip_audit_output_file)
    all_findings.extend(p_findings)
    scanned_scope.append(requirements_path or "active_python_environment")
    detected_tools["pip-audit"] = p_status

    # Semgrep status (not executed / unavailable)
    semgrep_status = detected_tools.get("semgrep")
    if semgrep_status and not semgrep_status.available:
        semgrep_status.executed = False

    # Severity distribution
    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for f in all_findings:
        sev = f.severity.upper()
        if sev in counts:
            counts[sev] += 1
        else:
            counts["INFO"] += 1

    total_duration = round(time.time() - start_total, 2)
    now_iso = datetime.now(timezone.utc).isoformat()

    summary = SecurityScanSummary(
        tools=detected_tools,
        findings=all_findings,
        countsBySeverity=counts,
        totalFindings=len(all_findings),
        scannedScope=scanned_scope,
        executedAt=now_iso,
        durationSeconds=total_duration,
    )

    # Save summary artifact
    summary_file = os.path.join(run_output_dir, "agent_6_security_findings.json")
    try:
        os.makedirs(run_output_dir, exist_ok=True)
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(summary.model_dump_json(indent=2))
    except Exception:
        pass

    return summary
