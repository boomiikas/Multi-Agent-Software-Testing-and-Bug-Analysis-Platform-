# Multi-Agent Software Testing and Bug Analysis Platform

A comprehensive, state-of-the-art automated testing and bug analysis web platform powered by **LangGraph** and local LLMs run via **Ollama**. The platform processes software requirements, compiles structured test suites, generates and executes UI automation tests using **Playwright**, designs REST API tests, performs static security audits, diagnoses failures using traceback logs/screenshots, and compiles a unified report.

---

## 1. Core Platform Features

- **Automated Requirement Mapping:** Parses high-level Software Requirement Specifications (SRS) documents to build requirement inventories.
- **Dynamic UI Code Generation & Execution:** Generates asynchronous Playwright Python code from natural language requirements and DOM tables, compiling them on-the-fly and executing them dynamically in a sandbox.
- **Context Dilution Prompt Architecture:** Prompt structures are optimized (placing selector reference tables at the very end of instructions) to counter context dilution, allowing small models like `gemma3:4b` to maintain strict adherence to element mappings.
- **Dynamic Selector Resolution Engine:** Utilizes Python's standard `difflib.get_close_matches` sequence matching to dynamically resolve minor selector typos or hallucinations in the LLM-generated script against valid elements in the SRS, preventing execution crashes without hardcoded mappings.
- **Robust Exception Handling & Failure Capturing:**
  - Nested context manager exception catches capture page screenshots *before* Playwright closes the browser connection.
  - Dynamically extracts the exact line of code that failed directly from the traceback frames and writes it as the `failure_reason` in output reports.
- **ASCII-Safe Logger:** Streamlined output formatting converts console checkmarks to ASCII representations, preventing CP1252/UnicodeEncodeErrors when running within piped terminal outputs on Windows.
- **API, Security, & Root Cause Auditing:** Incorporates deep-thinking models to compile backend test endpoints, audit code vulnerability vectors, and trace the structural origins of failed assertions.

---

## 2. Integrated LLM Model Matrix

The platform is designed to run locally using the following model stack:

| Agent Node | Model Name | Parameter Size | Ollama Target | Primary Role |
| :--- | :--- | :--- | :--- | :--- |
| **Agent 1: Requirement Analysis** | `Qwen2.5-7B-Instruct` | 7.2 Billion | `qwen2.5:7b` | Extracts clean functional requirements. |
| **Agent 2: Test Planning** | `Qwen2.5-7B-Instruct` | 7.2 Billion | `qwen2.5:7b` | Designs high-level test strategy and goals. |
| **Agent 3: Test Case Generation** | `DeepSeek-R1-Distill-7B` | 7.5 Billion | `deepseek-r1:7b` | Builds comprehensive structured test cases. |
| **Agent 4: UI Code Generator** | `Gemma 3 4B` | 4.2 Billion | `gemma3:4b` | Compiles Playwright test statements. |
| **Agent 5: API Testing** | `DeepSeek-R1-Distill-7B` | 7.5 Billion | `deepseek-r1:7b` | Designs API endpoint validation schemas. |
| **Agent 6: Security Auditing** | `DeepSeek-R1-Distill-7B` | 7.5 Billion | `deepseek-r1:7b` | Performs static scan on automation code. |
| **Agent 7: Root Cause Analysis** | `Qwen2.5-7B-Instruct` | 7.2 Billion | `qwen2.5:7b` | Diagnoses failed tracebacks and screenshots. |
| **Agent 8: Report Compiler** | `Gemma 3 4B` | 4.2 Billion | `gemma3:4b` | Formulates unified QA Markdown report. |

---

## 3. Installation & Setup

### Prerequisites
- **Python:** Version `3.11.x`
- **Ollama:** Installed and running on the local host.
- **System:** Windows / macOS / Linux (Windows execution includes automated CP1252 stdout encoding fixes).

### Step 1: Clone & Configure Python Environment
Initialize the environment inside the workspace directory:
```bash
# Create a virtual environment named "mini"
python -m venv mini

# Activate the virtual environment
# On Windows (PowerShell):
.\mini\Scripts\Activate.ps1
# On Windows (CMD):
.\mini\Scripts\activate.bat
# On macOS/Linux:
source mini/bin/activate
```

### Step 2: Install Libraries
Install packages within the active virtual environment:
```bash
pip install langgraph langchain-ollama playwright
```

### Step 3: Install Playwright Browsers
Install target headless browser engines:
```bash
playwright install chromium
```

### Step 4: Download Ollama Models
Pull the model configurations to local cache:
```bash
ollama pull gemma3:4b
ollama pull deepseek-r1:7b
ollama pull qwen2.5:7b
```

---

## 4. How to Execute

1. Review or customize the target specifications inside `srs_document.txt`.
2. Configure the target website endpoint in `main.py` (Default target: SwagLabs SauceDemo, `https://www.saucedemo.com`).
3. Execute the orchestrator script:
   ```bash
   python main.py
   ```

---

## 5. Output Deliverables (`agent_outputs/`)

Each successful run generates the following structured files in the outputs directory:

- **`agent_1_requirements.txt`**: Clear list of extracted requirements.
- **`agent_2_test_plan.txt`**: Outlines strategic goals, boundaries, and testing objectives.
- **`agent_3_test_cases.json`**: Structured array containing test cases, precondition requirements, and validation criteria.
- **`agent_4_ui_script.py`**: Clean, sanitized python script containing sequential Playwright actions.
- **`agent_4_execution.json`**: Runtime statistics, pass/fail status, console output histories, and metadata.
- **`agent_4_error_log.json`**: Created only on failure. Tracks the error type, exact traceback, failing line of code, and references the failure screenshot.
- **`agent_4_failure_screenshot.png`**: Taken only on failure. Captured page view at the exact frame of exception throw.
- **`agent_5_api_test_cases.json`**: Schema payloads, expected success/failure codes, and headers for mock backend endpoints.
- **`agent_6_security_report.txt`**: Risk findings covering hardcoded credentials, SSL verification, and route security.
- **`agent_7_rca_report.txt`**: Analysis indicating whether a failure is an application bug or a script error, with remediation steps.
- **`agent_8_test_report.md`**: Master Markdown report compiling requirements coverage, automation, API, security, and RCA audits.
