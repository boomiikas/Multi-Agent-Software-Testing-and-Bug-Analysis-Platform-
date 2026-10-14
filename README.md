# AgentQA: Multi-Agent Software Testing and Bug Analysis Platform

A modern, production-grade automated software quality assurance platform powered by a **LangGraph multi-agent AI pipeline**, **FastAPI backend**, **MongoDB Atlas persistence**, and a **React/Vite web dashboard**.

The platform ingests Software Requirement Specifications (SRS), coordinates eight specialized AI agents, executes real Playwright browser automation, performs live HTTPX API testing with strict SSRF controls, executes real Bandit and pip-audit security audits, conducts evidence-based Root Cause Analysis (RCA), executes controlled self-healing retries, and compiles executive quality reports exportable to Markdown, JSON, and PDF.

---

## 1. System Architecture

```
[ React / Vite UI ] <---> [ FastAPI Backend (Port 4000) ] <---> [ MongoDB Atlas ]
                                     |
                                     v
                       [ 9-Stage LangGraph Pipeline ]
 1. Requirement Analysis (Agent 1: Qwen2.5-7B)
 2. Test Planning        (Agent 2: Qwen2.5-7B)
 3. Test Generation      (Agent 3: DeepSeek-R1-Distill-7B / Qwen)
 4. UI Script Generation (Agent 4: Gemma 3 4B)
 5. Live UI Execution    (Playwright Chromium Engine)
 6. Live API Testing     (HTTPX Engine + SSRF Destination Filter)
 7. Security Auditing    (Bandit AST Scanner + pip-audit CVE DB)
 8. Root Cause Analysis  (Evidence-Based Classifier + Retry Controller)
 9. Report Lead          (Agent 8: Gemma 3 4B -> Markdown / JSON / PDF)
```

---

## 2. Core Capabilities

- **Multi-Agent Orchestration:** 8 specialized agents collaborating sequentially with isolated state management in LangGraph.
- **Real Browser Automation:** Headless Chromium execution via Playwright with automated screenshot capture on failure.
- **Real API Testing:** Live HTTP requests with configurable assertions, latency benchmarks, and strict SSRF destination validation (rejects private ranges, cloud metadata `169.254.169.254`, and malicious redirects).
- **Static Security Auditing:** Subprocess-isolated execution of **Bandit v1.9.4** (Python AST vulnerabilities) and **pip-audit v2.10.1** (PyPI dependency CVE database), with clean handling when Semgrep is unavailable.
- **Evidence-Based RCA:** Evaluates real execution evidence (tracebacks, HTTP codes, CVEs, DOM states) into 7 distinct failure categories. Transparently distinguishes verified facts from LLM hypotheses.
- **Controlled Self-Healing:** Dedicated retry controller with bounded retries (max 2), exponential backoff, before-and-after diff tracking, and strict non-retry rules for security, auth, and deterministic issues.
- **Production Hardening:** Password hashing via bcrypt, JWT authorization with expiration, cross-tenant project/run isolation, startup safeguards preventing default admin credentials in production, and path traversal protection on artifact retrieval.
- **Enterprise Reporting:** Run reports exportable in Markdown (`.md`), raw JSON, and printable HTML/PDF.

---

## 3. Local Development Setup (Windows / Linux / macOS)

### Prerequisites
- **Python:** 3.11, 3.12, or 3.13 (Python 3.13.5 supported)
- **Node.js:** v18+ and npm
- **Ollama:** Installed and running locally with models:
  ```bash
  ollama pull qwen2.5:7b
  ollama pull gemma3:4b
  ollama pull deepseek-r1:7b
  ```
- **MongoDB:** MongoDB Atlas connection string or local MongoDB instance on port 27017.

### Step 1: Clone and Configure Environment
Copy the configuration template and populate required variables:
```bash
cp .env.example .env
```
Ensure `.env` contains:
```env
PORT=4000
HOST=127.0.0.1
ENVIRONMENT=development
CLIENT_ORIGIN=http://localhost:5173
MONGODB_URL=your_mongodb_connection_string
MONGODB_DB_NAME=agentqa
JWT_SECRET=your_secure_random_jwt_secret_key
DEFAULT_ADMIN_EMAIL=admin@example.com
DEFAULT_ADMIN_PASSWORD=Admin@123
```

### Step 2: Install Python Dependencies & Playwright
```bash
# Install dependencies
pip install -r requirements.txt
pip install bandit pip-audit uvicorn

# Install Playwright browser engine
python -m playwright install chromium
```

### Step 3: Install Frontend Dependencies
```bash
npm install
```

### Step 4: Run the Application

**Terminal 1 — FastAPI Backend:**
```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 4000 --reload
```
Health check endpoint: `http://127.0.0.1:4000/api/health`

**Terminal 2 — React/Vite Frontend:**
```bash
npm run dev
```
Open web browser at `http://localhost:5173`. Default seeded admin: `admin@example.com` / `Admin@123`.

---

## 4. Automated Testing & Verification

Execute the complete test suite:
```bash
# Run all automated tests
python -m pytest

# Run dedicated feature test modules
python -m pytest tests/test_api_testing.py          # Real API testing & SSRF
python -m pytest tests/test_security_scanning.py    # Bandit & pip-audit scanning
python -m pytest tests/test_rca_and_healing.py      # RCA & Retry Controller
python -m pytest tests/test_pipeline_integration.py # Multi-agent pipeline & recovery
python -m pytest tests/test_production_security.py  # Auth isolation & startup guards

# Verify frontend build
npm run build
```

---

## 5. Docker & Containerized Deployment

To deploy the entire stack using Docker Compose:
```bash
# Build and run containers
docker-compose up --build -d

# Check service logs
docker-compose logs -f
```
The frontend will be available at `http://localhost` (port 80) and backend at `http://localhost:4000`.

---

## 6. Security & Safe Testing Guidelines

1. **SSRF Restrictions:** The platform strictly forbids testing targets pointing to loopback addresses (`127.0.0.1`, `localhost`), private RFC 1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), or cloud metadata endpoints (`169.254.169.254`).
2. **Credential Redaction:** All sensitive HTTP headers (`Authorization`, `Cookie`, `X-Api-Key`) and sensitive JSON payload fields (`password`, `token`, `secret`) are automatically redacted prior to logging and database persistence.
3. **Controlled Self-Healing:** The platform strictly prohibits autonomous code modification or weakening of security assertions. Retryable actions are bounded to a maximum of 2 attempts, and non-retryable failures (SSRF, Auth, CVEs) require human review.
4. **Production Deployment Safeguard:** When `ENVIRONMENT=production`, the platform will refuse to start if the default dev `JWT_SECRET` or default admin password (`Admin@123`) is detected.
