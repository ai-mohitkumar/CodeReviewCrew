
from __future__ import annotations

from typing import Any, Dict

from langgraph.graph import END, START, StateGraph

from backend.agents.coder import generate_code
from backend.agents.reviewer import review_code
from backend.agents.tester import generate_pytests
from backend.graph.state import ReviewState
from backend.services.executor import execute_tests
from backend.services.report_service import build_final_report


# Maximum number of coder -> reviewer -> tester -> executor attempts.
MAX_ITERATIONS = 3


def _get_iteration(state: Dict[str, Any]) -> int:
    """Return the current workflow iteration safely."""
    return int(state.get("iteration", 0) or 0)


def coder_node(state: ReviewState) -> ReviewState:
    prompt = state.get("prompt", "")

    previous_iteration = _get_iteration(state)
    current_iteration = previous_iteration + 1

    previous_code = state.get("code")
    review_feedback = state.get("review")

    test_result = state.get("test_result") or {}

    test_output_parts = []

    if test_result.get("stdout"):
        test_output_parts.append(str(test_result["stdout"]))

    if test_result.get("stderr"):
        test_output_parts.append(str(test_result["stderr"]))

    test_output = "\n".join(test_output_parts)

    state["iteration"] = current_iteration

    code = generate_code(
        prompt,
        previous_code=previous_code,
        review_feedback=review_feedback,
        test_output=test_output,
        iteration=current_iteration,
    )

    state["code"] = code

    state.setdefault("agent_history", [])
    state["agent_history"].append(
        {
            "agent_name": "CODER",
            "iteration": current_iteration,
            "status": "done",
            "summary": (
                "Generated the initial implementation."
                if current_iteration == 1
                else "Repaired the implementation using previous feedback."
            ),
            "code": code,
        }
    )

    return state



def reviewer_node(state: ReviewState) -> ReviewState:
    """Review the generated implementation."""

    prompt = state.get("prompt", "")
    code = state.get("code") or ""

    review = review_code(
        requirement=prompt,
        code=code,
        generated_tests=state.get("tests"),
    )

    state["review"] = str(review)
    state["review_struct"] = review

    state.setdefault("agent_history", [])

    state["agent_history"].append(
        {
            "agent_name": "REVIEWER",
            "iteration": state.get("iteration", 0),
            "status": "done",
            "summary": "Reviewed correctness and edge cases.",
            "review": review,
        }
    )

    return state


def tester_node(state: ReviewState) -> ReviewState:
    """Generate pytest tests for the current implementation."""

    requirement = state.get("prompt", "")
    code = state.get("code") or ""

    tests = generate_pytests(
        requirement=requirement,
        code=code,
    )

    state["tests"] = tests.get("test_code")
    state["test_summary"] = tests.get("summary")

    state.setdefault("agent_history", [])

    state["agent_history"].append(
        {
            "agent_name": "TESTER",
            "iteration": state.get("iteration", 0),
            "status": "done",
            "summary": "Generated pytest tests.",
            "tests": state.get("tests"),
        }
    )

    return state


def executor_node(state: ReviewState) -> ReviewState:
    """Execute the generated implementation against generated tests."""

    code = state.get("code") or ""
    tests_code = state.get("tests") or ""

    execution = execute_tests(
        implementation_code=code,
        tests_code=tests_code,
        timeout_seconds=15,
        workspace_subdir="workspace",
    )

    test_result = {
        "passed": execution.passed,
        "returncode": execution.returncode,
        "stdout": execution.stdout,
        "stderr": execution.stderr,
    }

    state["test_result"] = test_result

    state.setdefault("agent_history", [])

    state["agent_history"].append(
        {
            "agent_name": "EXECUTOR",
            "iteration": state.get("iteration", 0),
            "status": "passed" if execution.passed else "failed",
            "summary": "Executed generated code against generated tests.",
            "test_result": test_result,
            "code": code,
            "review": state.get("review"),
            "tests": tests_code,
            "stdout": execution.stdout,
            "stderr": execution.stderr,
        }
    )

    return state


def router(state: ReviewState) -> str:
    """Route to REPORT or retry CODER."""

    iteration = _get_iteration(state)

    max_iterations = int(
        state.get("max_iterations", MAX_ITERATIONS)
    )

    test_result = state.get("test_result") or {}

    passed = bool(test_result.get("passed"))

    if passed:
        return "report"

    if iteration >= max_iterations:
        return "report"

    return "failed"


def report_node(state: ReviewState) -> ReviewState:
    """Create the final structured workflow report."""

    max_iterations = int(
        state.get("max_iterations", MAX_ITERATIONS)
    )

    report = build_final_report(
        state=state,
        requirement=state.get("prompt", ""),
        max_iterations=max_iterations,
    )

    state["final_report"] = report

    if report["tests_passed"]:
        state["termination_reason"] = "tests_passed"
    else:
        state["termination_reason"] = "max_iterations_reached"

    return state


def build_workflow():
    """Build and compile the CodeReviewCrew LangGraph workflow."""

    graph = StateGraph(ReviewState)

    # Register workflow nodes.
    graph.add_node("CODER", coder_node)
    graph.add_node("REVIEWER", reviewer_node)
    graph.add_node("TESTER", tester_node)
    graph.add_node("EXECUTOR", executor_node)
    graph.add_node("REPORT", report_node)

    # Main workflow path.
    graph.add_edge(START, "CODER")
    graph.add_edge("CODER", "REVIEWER")
    graph.add_edge("REVIEWER", "TESTER")
    graph.add_edge("TESTER", "EXECUTOR")

    # Retry or terminate after test execution.
    graph.add_conditional_edges(
        "EXECUTOR",
        router,
        {
            "report": "REPORT",
            "failed": "CODER",
        },
    )

    # Final report terminates the workflow.
    graph.add_edge("REPORT", END)

    return graph.compile()
