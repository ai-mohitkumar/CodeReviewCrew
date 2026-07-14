# CodeReviewCrew

**Multi-Agent Code Generation, Review & Testing Platform**

CodeReviewCrew is a Python-based multi-agent software engineering platform that converts a programming requirement into generated code, reviews the implementation, generates semantic tests, executes those tests, automatically retries failed implementations, and produces a structured final report.

The project supports both deterministic execution for reliable demonstrations and automated testing, and Gemini-powered LLM execution for dynamic code generation, review, and test generation.

The project demonstrates agent orchestration, conditional workflow routing, LLM integration, automated testing, execution feedback, iterative code repair, REST API development, cloud deployment, and an interactive Streamlit interface.

---

## Live Deployment

CodeReviewCrew is deployed as a full-stack multi-agent software engineering application.

- **Live Frontend:** https://codereviewcrew.streamlit.app/
- **Backend API:** https://codereviewcrew.onrender.com
- **API Documentation:** https://codereviewcrew.onrender.com/docs

The public deployment currently uses deterministic execution mode for stable demonstrations, reproducible workflow results, and independence from external LLM API availability.

### Deployment Architecture

```text
User
  |
  v
Streamlit Community Cloud
  |
  v
FastAPI Backend on Render
  |
  v
LangGraph Multi-Agent Workflow
  |
  v
Coder -> Reviewer -> Tester -> Executor
                              |
                              v
                            Report
                              |
                              v
                             End
```

---

## Overview

Traditional code-generation systems often stop after producing code.

CodeReviewCrew implements a complete iterative software engineering workflow:

```text
User Requirement
        |
        v
      CODER
        |
        v
    REVIEWER
        |
        v
      TESTER
        |
        v
    EXECUTOR
        |
        +---------------- Tests Failed ----------------+
        |                                              |
        | iteration < max_iterations                   |
        v                                              |
      CODER <------------------------------------------+
        |
        | Tests Passed
        |
        v
      REPORT
        |
        v
       END
```

If the generated implementation fails testing, execution feedback is sent back through the workflow and the Coder receives another opportunity to repair the implementation.

The workflow terminates when:

- All generated tests pass, or
- The configured maximum number of iterations is reached.

---

## Key Features

- Multi-agent workflow orchestration using LangGraph
- Gemini-powered dynamic code generation
- LLM-assisted code review
- LLM-assisted pytest generation
- Deterministic execution mode for reliable demonstrations and automated testing
- Automated code review with structured findings
- Semantic pytest generation
- Generated-code execution through an isolated subprocess workspace
- Conditional retry routing
- Automatic code repair demonstration
- Maximum-iteration termination protection
- Agent execution history
- Structured final reports
- FastAPI REST API
- Professional Streamlit dashboard
- Five built-in demonstration cases
- Custom programming requirement support
- Automated test suite
- External LLM calls disabled during deterministic automated tests
- Render backend deployment
- Streamlit Community Cloud frontend deployment
- Environment-based frontend/backend configuration

---

## Execution Modes

CodeReviewCrew supports two execution modes.

### Deterministic Mode

```text
AGENT_MODE=deterministic
```

Deterministic mode provides predictable implementations, reviews, and generated tests for supported demonstration cases.

This mode is recommended for:

- Automated testing
- Reliable project demonstrations
- Automatic repair workflow demonstrations
- Development without external API usage
- Reproducible workflow behavior
- Stable cloud deployment demonstrations

Automated tests should run in deterministic mode so they do not depend on network connectivity, external API availability, model behavior, or API quotas.

The current public deployment uses deterministic mode.

### LLM Mode

```text
AGENT_MODE=llm
```

LLM mode uses the Google Gemini API to dynamically process programming requirements.

In this mode:

```text
Programming Requirement
        |
        v
Gemini-Powered Coder
        |
        v
Gemini-Powered Reviewer
        |
        v
Gemini-Powered Tester
        |
        v
Executor
        |
        +---- Tests Failed ----> Coder Repair
        |
        v
Structured Final Report
```

LLM mode enables CodeReviewCrew to process programming requirements beyond the built-in deterministic demonstration cases.

External LLM workflows may take longer than deterministic workflows because multiple model requests can occur during a single execution.

---

## Multi-Agent Architecture

CodeReviewCrew contains four primary workflow agents and one reporting stage.

### Coder

The Coder generates Python implementations from programming requirements.

Depending on the configured execution mode, code generation can use deterministic demonstration logic or Gemini-powered dynamic generation.

During retry iterations, the Coder can receive:

- Previous implementation
- Review feedback
- Failed test output
- Current iteration number

This enables the workflow to perform iterative code repair.

### Reviewer

The Reviewer analyzes generated code and produces structured findings such as:

- Approval status
- Issues
- Suggestions
- Quality score

In LLM mode, Gemini can dynamically review implementations according to the programming requirement and generated code.

### Tester

The Tester generates pytest tests based on the programming requirement and generated implementation.

In deterministic mode, supported demonstrations use meaningful behavioral assertions.

In LLM mode, Gemini dynamically generates requirement-aware pytest tests.

### Executor

The Executor:

1. Writes generated implementation code into a temporary workspace.
2. Writes generated tests into the workspace.
3. Adds the workspace to `PYTHONPATH`.
4. Runs pytest in a subprocess.
5. Captures stdout, stderr, return code, and pass/fail status.
6. Returns execution feedback to the workflow.

### Report

The Report stage builds the structured final result containing:

- Requirement
- Completion status
- Test status
- Iterations used
- Maximum iterations
- Final generated code
- Review feedback
- Generated tests
- Test output
- Agent summaries
- Termination reason
- Iteration history
- Quality score

---

## Workflow Routing

The workflow follows this route:

```text
START
  |
  v
CODER
  |
  v
REVIEWER
  |
  v
TESTER
  |
  v
EXECUTOR
  |
  +---- Tests Passed -----------------> REPORT
  |
  +---- Tests Failed
           |
           +---- iteration < max_iterations ----> CODER
           |
           +---- iteration >= max_iterations ---> REPORT

REPORT
  |
  v
END
```

The default maximum number of iterations is:

```text
3
```

The maximum-iteration stopping condition prevents infinite repair loops.

---

## Automatic Repair Demonstration

The modulo demonstration case intentionally shows the repair loop in deterministic mode.

### Requirement

```text
Create a Python function named modulo that returns the remainder of two numbers.
```

### Iteration 1

The Coder intentionally produces an incorrect implementation:

```python
def modulo(a, b):
    return a // b
```

The Tester generates behavioral tests:

```python
assert modulo(10, 3) == 1
assert modulo(10, 5) == 0
```

The tests fail.

The Executor captures the failure and routes execution back to the Coder.

### Iteration 2

The Coder receives the previous implementation, review feedback, and failed test output.

The implementation is repaired:

```python
def modulo(a, b):
    return a % b
```

The tests pass.

Final repair sequence:

```text
FAILED -> CODER REPAIR -> PASSED
```

This demonstration shows the review and testing loop detecting and fixing an implementation bug.

---

## Demonstration Cases

The Streamlit interface provides five built-in programming demonstrations.

| Demonstration | Expected Behavior |
| --- | --- |
| Addition | Passes in the first iteration |
| Prime Number | Passes in the first iteration |
| Odd or Even | Passes in the first iteration |
| Palindrome | Passes in the first iteration |
| Bug Detection + Automatic Repair | Fails first, repairs the implementation, then passes |

LLM mode also supports custom programming requirements.

---

## Streamlit Interface

The professional Streamlit dashboard provides separate views for:

- Workflow Progress
- Generated Code
- Review Findings
- Generated Tests
- Test Output
- Repair Iterations
- Final Report

The dashboard displays workflow status, test results, iterations used, quality score, termination reason, generated implementation, reviewer feedback, generated pytest tests, execution output, repair history, agent summaries, and the structured final report.

The frontend reads the deployed backend API URL from Streamlit Community Cloud Secrets.

Example:

```toml
API_URL = "https://codereviewcrew.onrender.com/api/run"
```

For local development, the frontend falls back to:

```text
http://127.0.0.1:8000/api/run
```

---

## REST API

The backend is implemented using FastAPI.

### Health Check

```text
GET /health
```

Example response:

```json
{
  "status": "ok"
}
```

### Run Workflow

```text
POST /api/run
```

Example request:

```json
{
  "requirement": "Create a Python function named count_vowels that returns the number of vowels in a string."
}
```

The endpoint executes the complete LangGraph workflow and returns the structured final report.

### Example Response Structure

```json
{
  "requirement": "Programming requirement",
  "status": "completed",
  "tests_passed": true,
  "iterations_used": 1,
  "max_iterations": 3,
  "final_code": "Generated Python implementation",
  "review_feedback": {
    "approved": true,
    "issues": [],
    "suggestions": [],
    "quality_score": 85
  },
  "generated_tests": "Generated pytest tests",
  "test_output": "pytest execution output",
  "agent_summary": {
    "coder": "Coder summary",
    "reviewer": "Reviewer summary",
    "tester": "Tester summary",
    "executor": "Executor summary"
  },
  "termination_reason": "tests_passed",
  "iterations": [],
  "quality_score": 85
}
```

---

## Project Structure

```text
CodeReviewCrew/
|
|-- .streamlit/
|   |-- config.toml
|
|-- backend/
|   |-- agents/
|   |   |-- coder.py
|   |   |-- reviewer.py
|   |   |-- tester.py
|   |
|   |-- graph/
|   |   |-- state.py
|   |   |-- workflow.py
|   |
|   |-- services/
|   |   |-- executor.py
|   |   |-- llm_service.py
|   |   |-- report_service.py
|   |
|   |-- api_models.py
|   |-- main.py
|   |-- smoke_test_llm.py
|
|-- docs/
|   |-- screenshots/
|       |-- 01-main-interface.png
|       |-- 02-successful-workflow.png
|       |-- 03-generated-code.png
|       |-- 04-generated-review.pdf
|
|-- frontend/
|   |-- app.py
|
|-- tests/
|   |-- test_health.py
|   |-- test_llm_mode.py
|   |-- test_workflow.py
|
|-- .env.example
|-- .gitignore
|-- pytest.ini
|-- render.yaml
|-- requirements.txt
|-- runtime.txt
|-- README.md
```

The generated `workspace/` directory is excluded from Git and pytest test discovery.

---

## Technology Stack

- Python 3.12
- LangGraph
- Google Gemini API
- google-genai Python SDK
- FastAPI
- Streamlit
- Pydantic
- pytest
- Requests
- python-dotenv
- Python subprocess execution
- Render
- Streamlit Community Cloud
- GitHub

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/ai-mohitkumar/CodeReviewCrew.git
cd CodeReviewCrew
```

### 2. Create a Virtual Environment

#### Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

#### Linux or macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root.

Example:

```text
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-flash-latest
AGENT_MODE=llm
```

Never commit real API keys or secrets.

The `.env` file must remain excluded through `.gitignore`.

A safe `.env.example` file should contain placeholder values only:

```text
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-flash-latest
AGENT_MODE=deterministic
```

---

## Running the Application Locally

### Start the FastAPI Backend

From the project root:

#### Deterministic Mode

```powershell
$env:AGENT_MODE="deterministic"
python -m uvicorn backend.main:app --reload --port 8000
```

#### LLM Mode

```powershell
$env:AGENT_MODE="llm"
python -m uvicorn backend.main:app --port 8000
```

### Start the Streamlit Frontend

Open another terminal, activate the virtual environment, and run:

```bash
python -m streamlit run frontend/app.py
```

Select a built-in demonstration case or enter a custom programming requirement, then click **Run agents**.

---

## Cloud Deployment

The project uses separate cloud services for the backend and frontend.

### Backend Deployment on Render

The FastAPI backend is deployed as a Render Web Service.

Deployment configuration:

```text
Environment: Python 3
Branch: main
Build Command: pip install -r requirements.txt
Start Command: python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT
Instance Type: Free
AGENT_MODE: deterministic
```

The repository contains `render.yaml` and `runtime.txt` for backend deployment configuration.

### Frontend Deployment on Streamlit Community Cloud

Deployment configuration:

```text
Repository: ai-mohitkumar/CodeReviewCrew
Branch: main
Main file path: frontend/app.py
```

The deployed backend URL is configured through Streamlit Secrets:

```toml
API_URL = "https://codereviewcrew.onrender.com/api/run"
```

This architecture allows the Streamlit frontend and FastAPI backend to be deployed and managed independently.

---

## Running Tests

Automated tests should be executed in deterministic mode.

```powershell
$env:AGENT_MODE="deterministic"
python -m pytest -q --cache-clear
```

Verify dependency consistency:

```bash
python -m pip check
```

Current verified development checkpoint:

```text
8 passed, 1 non-blocking Starlette deprecation warning
No broken requirements found.
```

---

## Testing Strategy

The automated test suite verifies:

- Health endpoint behavior
- API request validation
- Successful workflow termination
- Retry routing after failed tests
- Maximum-iteration termination
- Required final-report fields
- Automatic repair behavior
- LLM-mode agent behavior with mocked external calls

LLM calls and generated-code execution are mocked where required.

Automated tests do not call real external APIs.

Deterministic test execution makes the automated test suite stable, reproducible, and independent of external model availability.

---

## LLM Integration

CodeReviewCrew uses the Google Gemini API through the `google-genai` Python SDK.

The `LLMService`:

- Loads configuration from environment variables
- Initializes the Gemini client only when an API key is available
- Uses a configurable Gemini model
- Sends prompts to the Gemini Generate Content API
- Returns generated model text to the requesting agent

The Gemini model can be changed without modifying source code:

```text
GEMINI_MODEL=gemini-flash-latest
```

The API key must never be hardcoded into source files or committed to Git.

---

## Security and Safety

The Executor runs generated Python code through a subprocess.

This implementation is intended for controlled educational and demonstration use.

Process isolation is not equivalent to a production-grade security sandbox.

Running untrusted arbitrary code requires stronger isolation, such as:

- Containers
- Restricted operating-system permissions
- Resource limits
- Network restrictions
- Dedicated sandboxing infrastructure

API keys and other sensitive configuration values must be stored in environment variables or cloud secret-management systems.

---

## Current Limitations

- Deterministic mode supports a limited set of demonstration-oriented programming requirements.
- LLM output quality and latency depend on external model availability and API behavior.
- LLM workflows may take longer because Coder, Reviewer, and Tester can each make external model requests.
- Generated-code execution is not protected by a production-grade security sandbox.
- No persistent database is implemented.
- No authentication or user management is implemented.
- Workflow history is not persisted after application restart.
- Render free-tier services may experience cold-start delays after inactivity.

---

## Future Improvements

- Secure container-based code execution
- Parallel or asynchronous agent execution
- Persistent workflow history
- Human-in-the-loop approval
- Authentication and authorization
- Observability and distributed tracing
- Code coverage reporting
- Additional programming-language support
- LLM response caching
- Per-agent timeout and retry configuration
- Streaming workflow progress
- CI/CD deployment automation and production monitoring

---

## Development Status

The current project includes:

```text
Requirement Input
        |
        v
Deterministic or Gemini-Powered Code Generation
        |
        v
Automated / Gemini-Powered Review
        |
        v
Semantic / Gemini-Powered Test Generation
        |
        v
Test Execution
        |
        +---- Failure ---> Automatic Repair Loop
        |
        v
Structured Final Report
        |
        v
Professional Streamlit Dashboard
        |
        v
Cloud Deployment
```

The project demonstrates a complete multi-agent software engineering workflow, automated testing, iterative repair, LLM integration, REST API development, frontend/backend cloud deployment, and professional project documentation.

---

## Author

**Mohit Kumar**

GitHub: ai-mohitkumar