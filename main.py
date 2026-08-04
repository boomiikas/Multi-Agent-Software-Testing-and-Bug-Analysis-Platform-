import os
import json
import asyncio
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END

# Import agents
from agent1_requirement import requirement_analysis_agent
from agent2_planner import test_planning_agent
from agent3_generator import test_case_generation_agent
from agent4_ui_automation import ui_automation_agent, execute_playwright_test
from agent5_api_testing import api_testing_agent
from agent6_security_testing import security_testing_agent
from agent7_rca import rca_agent
from agent8_report import report_generation_agent

# Configuration
SRS_FILE_PATH = "srs_document.txt"
TARGET_WEBSITE_URL = "https://www.saucedemo.com"  #https://www.saucedemo.com/
OUTPUT_DIR = "agent_outputs"


class TestingState(TypedDict):
    srs_document: str
    target_url: str
    output_dir: str
    requirements: List[str]
    test_plan: str
    test_cases: List[Dict[str, Any]]
    ui_script: str
    execution_result: Dict[str, Any]
    api_test_cases: str
    security_report: str
    rca_report: str
    final_report: str


# =====================================================================
# Wrapped Agents Writing File Artifacts
# =====================================================================

def step_agent_1(state: TestingState) -> Dict[str, Any]:
    print("[+] Step 1: Running Requirement Analysis Agent...")
    res = requirement_analysis_agent(state)
    reqs = res.get("requirements", [])
    
    # Save Agent 1 output to individual file
    filepath = os.path.join(state["output_dir"], "agent_1_requirements.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("=== EXTRACTED REQUIREMENTS ===\n\n")
        f.write("\n".join([f"- {r}" for r in reqs]))
    print(f"    [OK] Output saved to: {filepath}")
    
    return res


def step_agent_2(state: TestingState) -> Dict[str, Any]:
    print("[+] Step 2: Running Test Planning Agent...")
    res = test_planning_agent(state)
    plan = res.get("test_plan", "")
    
    # Save Agent 2 output to individual file
    filepath = os.path.join(state["output_dir"], "agent_2_test_plan.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("=== TEST PLAN SUMMARY ===\n\n")
        f.write(plan)
    print(f"    [OK] Output saved to: {filepath}")
    
    return res


def step_agent_3(state: TestingState) -> Dict[str, Any]:
    print("[+] Step 3: Running Test Case Generation Agent...")
    res = test_case_generation_agent(state)
    cases = res.get("test_cases", [])
    
    # Save Agent 3 output to individual file
    filepath = os.path.join(state["output_dir"], "agent_3_test_cases.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(cases, f, indent=4)
    print(f"    [OK] Output saved to: {filepath}")
    
    return res


def step_agent_4_generator(state: TestingState) -> Dict[str, Any]:
    print("[+] Step 4: Running UI Automation Agent...")
    res = ui_automation_agent(state)
    script = res.get("ui_script", "")
    
    # Save Agent 4 Python script to individual file
    filepath = os.path.join(state["output_dir"], "agent_4_ui_script.py")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(script)
    print(f"    [OK] Output saved to: {filepath}")
    
    return res


async def step_agent_4_executor(state: TestingState) -> Dict[str, Any]:
    print("[+] Step 5: Executing Playwright UI Test...")
    res = await execute_playwright_test(state)
    exec_result = res.get("execution_result", {})
    
    # Save Playwright execution metadata to individual file
    filepath = os.path.join(state["output_dir"], "agent_4_execution.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(exec_result, f, indent=4)
    print(f"    [OK] Execution status saved to: {filepath}")
    
    return res


def step_agent_5_api(state: TestingState) -> Dict[str, Any]:
    print("[+] Step 6: Running API Testing Agent...")
    res = api_testing_agent(state)
    api_cases = res.get("api_test_cases", "")
    
    filepath = os.path.join(state["output_dir"], "agent_5_api_test_cases.json")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(api_cases)
    print(f"    [OK] Output saved to: {filepath}")
    
    return res


def step_agent_6_security(state: TestingState) -> Dict[str, Any]:
    print("[+] Step 7: Running Security Testing Agent...")
    res = security_testing_agent(state)
    sec_report = res.get("security_report", "")
    
    filepath = os.path.join(state["output_dir"], "agent_6_security_report.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(sec_report)
    print(f"    [OK] Output saved to: {filepath}")
    
    return res


def step_agent_7_rca(state: TestingState) -> Dict[str, Any]:
    print("[+] Step 8: Running Root Cause Analysis Agent...")
    res = rca_agent(state)
    rca_rep = res.get("rca_report", "")
    
    filepath = os.path.join(state["output_dir"], "agent_7_rca_report.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(rca_rep)
    print(f"    [OK] Output saved to: {filepath}")
    
    return res


def step_agent_8_report(state: TestingState) -> Dict[str, Any]:
    print("[+] Step 9: Running Report Generation Agent...")
    res = report_generation_agent(state)
    final_rep = res.get("final_report", "")
    
    filepath = os.path.join(state["output_dir"], "agent_8_test_report.md")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(final_rep)
    print(f"    [OK] Output saved to: {filepath}")
    
    return res


# =====================================================================
# LangGraph Workflow Construction
# =====================================================================

builder = StateGraph(TestingState)

builder.add_node("agent_1", step_agent_1)
builder.add_node("agent_2", step_agent_2)
builder.add_node("agent_3", step_agent_3)
builder.add_node("agent_4_gen", step_agent_4_generator)
builder.add_node("agent_4_exec", step_agent_4_executor)
builder.add_node("agent_5_api", step_agent_5_api)
builder.add_node("agent_6_security", step_agent_6_security)
builder.add_node("agent_7_rca", step_agent_7_rca)
builder.add_node("agent_8_report", step_agent_8_report)

builder.set_entry_point("agent_1")
builder.add_edge("agent_1", "agent_2")
builder.add_edge("agent_2", "agent_3")
builder.add_edge("agent_3", "agent_4_gen")
builder.add_edge("agent_4_gen", "agent_4_exec")
builder.add_edge("agent_4_exec", "agent_5_api")
builder.add_edge("agent_5_api", "agent_6_security")
builder.add_edge("agent_6_security", "agent_7_rca")
builder.add_edge("agent_7_rca", "agent_8_report")
builder.add_edge("agent_8_report", END)

workflow = builder.compile()


async def main():
    # Ensure target output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if not os.path.exists(SRS_FILE_PATH):
        with open(SRS_FILE_PATH, "w", encoding="utf-8") as f:
            f.write("The software must render the main homepage, verify page header, and check responsiveness.")

    with open(SRS_FILE_PATH, "r", encoding="utf-8") as f:
        srs_content = f.read()

    initial_state: TestingState = {
        "srs_document": srs_content,
        "target_url": TARGET_WEBSITE_URL,
        "output_dir": OUTPUT_DIR,
        "requirements": [],
        "test_plan": "",
        "test_cases": [],
        "ui_script": "",
        "execution_result": {},
        "api_test_cases": "",
        "security_report": "",
        "rca_report": "",
        "final_report": ""
    }

    print("=" * 60)
    print("STARTING MULTI-AGENT EXECUTION PIPELINE")
    print("=" * 60)
    
    await workflow.ainvoke(initial_state)
    
    print("\n" + "=" * 60)
    print(f"ALL AGENT ARTIFACTS GENERATED IN: ./{OUTPUT_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())