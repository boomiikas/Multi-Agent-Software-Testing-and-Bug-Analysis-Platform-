from langchain_ollama import OllamaLLM

# Model specification: DeepSeek-R1 Distill 7B
llm_gen = OllamaLLM(model="deepseek-r1:7b")

def test_case_generation_agent(state: dict) -> dict:
    """
    Agent 3: Generates detailed test cases using outputs from BOTH 
    Agent 1 (Requirements) and Agent 2 (Test Plan).
    """
    # 1. Fetch requirements from Agent 1
    requirements = state.get("requirements", [])
    
    # 2. Fetch test strategy/plan from Agent 2
    test_plan = state.get("test_plan", "")
    
    target_url = state.get("target_url", "")
    
    reqs_str = "\n".join([f"- {r}" for r in requirements]) if isinstance(requirements, list) else str(requirements)
    
    # 3. Combine both outputs into the LLM prompt
    prompt = f"""
    You are an expert Test Case Generation Agent.
    
    [INPUT FROM AGENT 1 - FUNCTIONAL REQUIREMENTS]:
    {reqs_str}
    
    [INPUT FROM AGENT 2 - TEST PLAN & STRATEGY]:
    {test_plan}
    
    Target URL: {target_url}
    
    TASK:
    Based strictly on the extracted requirements AND the test strategy provided above, generate structured test cases.
    Include:
    - Test Case ID
    - Description
    - Pre-conditions
    - Action Steps
    - Expected Result
    
    Format the response as clear structured test scenarios.
    """
    
    response = llm_gen.invoke(prompt)
    
    # Return output to update shared state for Agent 4
    return {
        "test_cases": [
            {
                "id": "TC-01",
                "details": response
            }
        ]
    }