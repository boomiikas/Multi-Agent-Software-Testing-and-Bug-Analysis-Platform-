from langchain_ollama import OllamaLLM

# Model specification: DeepSeek-R1 Distill 7B
llm_sec = OllamaLLM(model="deepseek-r1:7b")

def security_testing_agent(state: dict) -> dict:
    """
    Agent 6: Analyzes the generated Playwright automation script and the SRS
    to detect security issues and design weaknesses (hardcoded passwords, lack of SSL, injection).
    """
    srs_text = state.get("srs_document", "")
    ui_script = state.get("ui_script", "")
    
    prompt = f"""
    You are an expert Security Testing Agent.
    Perform static security analysis on the following generated UI automation script and the target requirements.
    
    [SRS SPECIFICATIONS]:
    {srs_text}
    
    [GENERATED UI AUTOMATION SCRIPT]:
    {ui_script}
    
    TASK:
    Analyze the script and specification for security flaws, configuration issues, and compliance gaps.
    Check specifically for:
    1. Hardcoded Credentials / Secrets (e.g., plain-text passwords or keys exposed in scripts).
    2. Protocol Security (use of insecure HTTP instead of HTTPS).
    3. Input Validation vulnerabilities (potential injection vectors in login/input text fields).
    4. Session & State Management (session persistence, lack of secure logout checks).
    5. Privilege Escalation or Bypass (validation of locked-out users and route protection).
    
    Output a structured security report containing:
    - Summary of Findings
    - Detailed list of vulnerabilities with Risk Levels (High, Medium, Low)
    - Recommended remediation/mitigation steps.
    """
    response = llm_sec.invoke(prompt)
    return {"security_report": response}
