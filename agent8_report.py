from langchain_ollama import OllamaLLM

# Model specification: Gemma 3 4B
llm_rep = OllamaLLM(model="gemma3:4b")

def report_generation_agent(state: dict) -> dict:
    """
    Agent 8: Compiles a unified report detailing functional requirements,
    test plan, API cases, UI test results, security findings, and RCA reports.
    """
    requirements = state.get("requirements", [])
    test_plan = state.get("test_plan", "")
    test_cases = state.get("test_cases", [])
    execution_result = state.get("execution_result", {})
    api_test_cases = state.get("api_test_cases", "")
    security_report = state.get("security_report", "")
    rca_report = state.get("rca_report", "")
    
    reqs_str = "\n".join([f"- {r}" for r in requirements]) if isinstance(requirements, list) else str(requirements)
    tc_str = str(test_cases[0].get("details", test_cases)) if (isinstance(test_cases, list) and test_cases) else str(test_cases)
    
    prompt = f"""
    You are an expert Test Lead and Report Generation Agent.
    Your task is to synthesize all artifacts and results from this test cycle into a professional, comprehensive testing summary report.
    
    [Artifacts & Results collected]:
    - Extracted Functional Requirements:
    {reqs_str}
    
    - Test Planning & Strategy:
    {test_plan}
    
    - Generated UI Test Cases:
    {tc_str}
    
    - UI Test Execution Result:
    {execution_result}
    
    - API Test Cases:
    {api_test_cases}
    
    - Static Security Analysis Report:
    {security_report}
    
    - Root Cause Analysis (RCA) Report:
    {rca_report}
    
    TASK:
    Compile a unified Test Summary Report in Markdown. Your report should contain:
    1. Executive Summary: Overall status (PASSED/FAILED), description, and run metrics.
    2. Functional Requirements Coverage: Requirements analyzed and covered.
    3. UI Test Automation Report: Executed Playwright steps, status, error trace (if failed), and confirmation of screenshot capture.
    4. REST API Test Scenarios: Summary of generated API test cases.
    5. Security Vulnerability Scan: Overview of risk findings and remediations.
    6. Root Cause Analysis (RCA) Summary: For failures, detail what went wrong and how to fix it.
    7. Overall QA Recommendations.
    
    Output ONLY the markdown report.
    """
    response = llm_rep.invoke(prompt)
    return {"final_report": response}
