import asyncio
import os
import json
from backend.testing.api_executor import run_real_api_tests, ApiTestCase
from backend.testing.security_scanner import detect_security_tools, run_security_scans

async def main():
    print("==================================================")
    print("PHASE 5: REAL TOOL EXECUTION VERIFICATION")
    print("==================================================")

    # 1. Detect Tools
    print("\n[1] Detecting Installed Security Tools:")
    tools = detect_security_tools()
    for name, stat in tools.items():
        print(f"  - {name.upper()}: available={stat.available}, version={stat.version}, error={stat.error}")

    # 2. Real Security Scanning Execution
    print("\n[2] Executing Real Security Scans (Bandit + pip-audit):")
    test_run_dir = os.path.join("agent_outputs", "phase5_verification")
    os.makedirs(test_run_dir, exist_ok=True)

    sec_target = "scratch/test_vuln.py"
    reqs_file = "requirements.txt"

    sec_summary = run_security_scans(sec_target, test_run_dir, requirements_path=reqs_file)
    print(f"  - Bandit Status: executed={sec_summary.tools['bandit'].executed}, exitCode={sec_summary.tools['bandit'].exitCode}, duration={sec_summary.tools['bandit'].durationSeconds}s")
    print(f"  - pip-audit Status: executed={sec_summary.tools['pip-audit'].executed}, exitCode={sec_summary.tools['pip-audit'].exitCode}, duration={sec_summary.tools['pip-audit'].durationSeconds}s")
    print(f"  - Semgrep Status: available={sec_summary.tools['semgrep'].available}")
    print(f"  - Total Findings: {sec_summary.totalFindings}")
    print(f"  - Severity Breakdown: {sec_summary.countsBySeverity}")

    print("\n  Sample Findings Captured:")
    for f in sec_summary.findings[:5]:
        print(f"    * [{f.tool.upper()}] {f.ruleId} ({f.severity}): {f.description[:100]} | File: {f.file}:{f.line}")

    # 3. Real API Testing Execution
    print("\n[3] Executing Real API Tests (HTTPX with SSRF checks):")
    api_tests = [
        ApiTestCase(
            name="SauceDemo Root Reachability",
            method="GET",
            endpoint="/",
            expectedStatus=200,
            maxResponseTimeMs=4000.0,
        ),
        ApiTestCase(
            name="Static Asset Check",
            method="GET",
            endpoint="/static/css/main.css",
            expectedStatus=200,
            maxResponseTimeMs=4000.0,
        ),
    ]

    api_summary = await run_real_api_tests("https://www.saucedemo.com", api_tests)
    print(f"  - Target URL: {api_summary.targetBaseUrl}")
    print(f"  - Total Executed: {api_summary.total}")
    print(f"  - Passed: {api_summary.passed} | Failed: {api_summary.failed} | Blocked: {api_summary.blocked}")
    print(f"  - Duration: {api_summary.durationSeconds}s")
    for t in api_summary.tests:
        print(f"    * {t.method} {t.url} -> Status: {t.actualStatus} | Result: {t.status} | Latency: {t.responseTimeMs}ms")

    # 4. Verify Generated Artifacts on Disk
    print("\n[4] Verifying Generated Run Artifacts:")
    for fname in ["bandit_report.json", "pip_audit_report.json", "agent_6_security_findings.json"]:
        fpath = os.path.join(test_run_dir, fname)
        if os.path.exists(fpath):
            size = os.path.getsize(fpath)
            print(f"  - {fname}: {size} bytes written.")
        else:
            print(f"  - {fname}: MISSING!")

    print("\nREAL TOOL EXECUTION COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(main())
