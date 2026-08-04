from langchain_ollama import OllamaLLM

# Model specification: Qwen2.5-7B-Instruct
llm_rca = OllamaLLM(model="qwen2.5:7b")

def rca_agent(state: dict) -> dict:
    """
    Agent 7: Evaluates execution failures. Analyzes status, error logs,
    and tracebacks to isolate the root cause and propose solutions.
    """
    execution_result = state.get("execution_result", {})
    
    prompt = f"""
    You are an expert QA and Root Cause Analysis (RCA) Agent.
    Evaluate the following UI automation execution results:
    
    [EXECUTION RESULT]:
    {execution_result}
    
    TASK:
    1. If the execution "status" is "PASSED":
       - Output a concise confirmation that the test run completed successfully and all requirements were met.
    
    2. If the execution "status" is "FAILED":
       - Examine the "error_type", "error_message", and traceback/logs.
       - Isolate the failing component (e.g., Selector issue, Assertion failure, Timeout, Network/HTTP status).
       - Classify the issue (e.g., Application Bug vs Test Automation Script Bug).
       - Propose exact, actionable remediation steps to resolve the issue.
       
    Provide a professional, clear Root Cause Analysis report.
    """
    response = llm_rca.invoke(prompt)
    return {"rca_report": response}
