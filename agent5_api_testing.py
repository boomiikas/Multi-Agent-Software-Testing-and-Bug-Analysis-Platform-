from langchain_ollama import OllamaLLM

# Model specification: DeepSeek-R1 Distill 7B
llm_api = OllamaLLM(model="deepseek-r1:7b")

def api_testing_agent(state: dict) -> dict:
    """
    Agent 5: Generates and validates REST API test cases based on
    endpoints implied or specified in the SRS document.
    """
    srs_text = state.get("srs_document", "")
    target_url = state.get("target_url", "")
    
    prompt = f"""
    You are an expert API Testing Agent.
    Based on the following Software Requirement Specification (SRS) for the application at {target_url},
    generate a comprehensive set of REST API test cases for the backend services supporting these UI flows.
    
    [SRS SPECIFICATIONS]:
    {srs_text}
    
    TASK:
    Identify mock or expected API endpoints (such as Auth/Login, Product Catalogue, Cart Actions, and Checkout Workflow).
    For each endpoint, define:
    - HTTP Method (GET, POST, PUT, DELETE)
    - Request URL (relative to API base)
    - Headers & Content-Type
    - Request payload example (JSON)
    - Expected successful response (JSON code + status code)
    - Expected validation/error response (JSON code + status code)
    
    Provide the API test cases in a clear structured format.
    """
    response = llm_api.invoke(prompt)
    return {"api_test_cases": response}
