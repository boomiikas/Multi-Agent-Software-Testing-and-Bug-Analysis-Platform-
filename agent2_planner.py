from langchain_ollama import OllamaLLM

# Model specification from project report: Qwen2.5-7B-Instruct
llm_plan = OllamaLLM(model="qwen2.5:7b")

def test_planning_agent(state: dict) -> dict:
    """Agent 2: Selects appropriate testing strategy (Smoke, Regression, Integration)."""
    requirements = state.get("requirements", [])
    reqs_str = "\n".join([f"- {r}" for r in requirements])
    
    prompt = f"""
    You are a Test Planning Agent.
    Based on the following functional requirements, outline a high-level test strategy (Smoke, Functional, Regression scope) and key testing objectives.
    
    Requirements:
    {reqs_str}
    
    Provide a concise test plan summary.
    """
    response = llm_plan.invoke(prompt)
    return {"test_plan": response}