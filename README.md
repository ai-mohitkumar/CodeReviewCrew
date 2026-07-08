# CodeReviewCrew

**Multi-Agent Code Generation, Review & Testing Platform**

CodeReviewCrew is a Python-based multi-agent software engineering platform that converts a programming requirement into generated code, reviews the implementation, generates semantic tests, executes those tests, automatically retries failed implementations, and produces a structured final report.

The project demonstrates agent orchestration, conditional workflow routing, automated testing, execution feedback, iterative code repair, REST API development, and an interactive Streamlit interface.

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

* All generated tests pass, or
* The configured maximum number of iterations is reached.

---

## Key Features

* Multi-agent workflow orchestration using LangGraph
* Deterministic Python code generation for demonstration tasks
* Automated code review
* Semantic pytest generation
* Isolated generated-code execution through a subprocess
* Conditional retry routing
* Automatic code repair demonstration
* Maximum-iteration termination protection
* Agent execution history
* Structured final reports
* FastAPI REST API
* Interactive Streamlit frontend
* Five built-in demonstration cases
* Unit tests with mocked external operations
* No real external API calls during automated tests

---

## Multi-Agent Architecture

CodeReviewCrew contains four primary agents and one reporting stage.

### Coder

The Coder generates Python implementations from programming requirements.

During retry iterations, it can receive:

* Previous implementation
* Review feedback
* Failed test output
* Current iteration number

This enables the workflow to demonstrate iterative code repair.

### Reviewer

The Reviewer analyzes generated code and produces findings such as:

* Approval status
* Issues
* Suggestions
* Quality score

### Tester

The Tester generates pytest tests based on the requirement and generated implementation.

The supported demonstration cases use meaningful behavioral assertions rather than only checking whether a function exists.

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

* Requirement
* Completion status
* Test status
* Iterations used
* Maximum iterations
* Final generated code
* Review feedback
* Generated tests
* Test output
* Agent summaries
* Termination reason
* Iteration history
* Quality score

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

---

## Automatic Repair Demonstration

The modulo demonstration case intentionally shows the repair loop.

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

The Tester generates behavioral tests such as:

```python
assert modulo(10, 3) == 1
assert modulo(10, 5) == 0
```

The tests fail.

The Executor captures the failure and the workflow routes execution back to the Coder.

### Iteration 2

The Coder uses the previous implementation and failed test output to repair the implementation:

```python
def modulo(a, b):
    return a % b
```

The tests pass.

The workflow then routes to the Report stage.

Final repair sequence:

```text
FAILED -> CODER REPAIR -> PASSED
```

---

## Demonstration Cases

The Streamlit interface provides at least five programming demonstrations.

| Demonstration                    | Expected Behavior                                |
| -------------------------------- | ------------------------------------------------ |
| Addition                         | Passes in the first iteration                    |
| Prime Number                     | Passes in the first iteration                    |
| Odd or Even                      | Passes in the first iteration                    |
| Palindrome                       | Passes in the first iteration                    |
| Bug Detection + Automatic Repair | Fails first, repairs implementation, then passes |

Additional deterministic cases supported by the Coder may include:

* Safe division
* Duplicate removal
* Binary search

---

## Streamlit Interface

The frontend provides separate views for:

* Workflow Progress
* Generated Code
* Review Findings
* Generated Tests
* Test Output
* Repair Iterations
* Final Report

The Repair Iterations view displays each workflow attempt independently.

For the automatic repair demonstration, the interface clearly shows:

```text
Iteration 1 - FAILED
        |
        v
Coder Repair
        |
        v
Iteration 2 - PASSED
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
  "requirement": "Create a Python function named is_prime that checks whether a number is prime."
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
  "review_feedback": "Reviewer findings",
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
|-- frontend/
|   |-- app.py
|
|-- tests/
|   |-- test_health.py
|   |-- test_workflow.py
|
|-- .env.example
|-- .gitignore
|-- pytest.ini
|-- requirements.txt
|-- README.md
```

The generated `workspace/` directory is excluded from Git and pytest test discovery.

---

## Technology Stack

* Python 3.12
* FastAPI
* LangGraph
* Pydantic
* pytest
* Streamlit
* Requests
* Python subprocess execution

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/ai-mohitkumar/CodeReviewCrew.git
cd CodeReviewCrew
```

### 2. Create a Virtual Environment

Windows:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Linux or macOS:

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

Create `.env` from `.env.example` when external LLM functionality is configured.

Never commit real API keys or secrets.

---

## Running the Application

### Start the FastAPI Backend

From the project root:

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

The backend is available locally on port `8000`.

Interactive API documentation is available through FastAPI's `/docs` endpoint.

### Start the Streamlit Frontend

Open another terminal, activate the same virtual environment, and run:

```bash
python -m streamlit run frontend/app.py
```

Select a demonstration case or enter a custom programming requirement, then click **Run Agents**.

---

## Running Tests

Run the complete project test suite:

```bash
python -m pytest -q --cache-clear
```

Verify dependency consistency:

```bash
python -m pip check
```

Current verified development checkpoint:

```text
6 passed, 1 non-blocking StarletteDeprecationWarning
No broken requirements found.
```

The Starlette warning is dependency-related and does not affect project behavior.

---

## Testing Strategy

The automated test suite verifies:

* Health endpoint behavior
* API request validation
* Successful workflow termination
* Retry routing after failed tests
* Maximum-iteration termination
* Required final-report fields
* Automatic repair behavior

LLM calls and code execution are mocked where required.

Automated unit tests do not call real external APIs.

---

## Safety Note

The Executor runs generated Python code through a subprocess.

This implementation is intended for controlled educational and demonstration use.

Process isolation is not equivalent to a production-grade security sandbox.

Running untrusted arbitrary code requires stronger isolation such as containers, restricted operating-system permissions, resource limits, and dedicated sandboxing infrastructure.

---

## Current Limitations

* Code generation is deterministic for supported demonstration tasks.
* Generic programming requirements may fall back to placeholder implementations.
* The Reviewer and Tester use heuristic logic in the current MVP.
* Generated-code execution is not protected by a production-grade sandbox.
* No persistent database is implemented.
* No authentication or user management is implemented.
* No deployment configuration is included yet.

---

## Future Improvements

* Production LLM integration for dynamic code generation
* More advanced reviewer reasoning
* Requirement-aware test generation
* Secure container-based code execution
* Parallel agent execution
* Persistent workflow history
* Human-in-the-loop approval
* Authentication and authorization
* Observability and tracing
* Code coverage reporting
* Support for additional programming languages
* Deployment automation

---

## Development Status

The current MVP includes:

```text
Requirement Input
        |
        v
Code Generation
        |
        v
Automated Review
        |
        v
Semantic Test Generation
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
Interactive Streamlit Visualization
```

The project demonstrates the complete multi-agent software engineering workflow required for the current development milestone.

---

## Author

Mohit Kumar

GitHub: ai-mohitkumar
