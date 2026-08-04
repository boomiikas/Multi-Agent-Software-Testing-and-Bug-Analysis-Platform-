from langchain_ollama import OllamaLLM

# Model specification from project report: Qwen2.5-7B-Instruct
llm_req = OllamaLLM(model="qwen2.5:7b")

def requirement_analysis_agent(state: dict) -> dict:
    """Agent 1: Reads SRS document and extracts structured functional requirements."""
    srs_text = state.get("srs_document", "")
    
    prompt = f"""
    You are an expert Requirement Analysis Agent.
    Analyze the following Software Requirement Specification (SRS) text and extract a clear list of core functional requirements.
    
    SRS Document:
    {srs_text}
    
    Output ONLY a clean bulleted list of extracted functional requirements.
    """
    response = llm_req.invoke(prompt)
    reqs = [line.strip("- ").strip() for line in response.strip().split("\n") if line.strip()]
    return {"requirements": reqs}