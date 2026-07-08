
from __future__ import annotations

from typing import Any, Dict, List, Optional


def build_final_report(
    *,
    state: Dict[str, Any],
    requirement: str,
    max_iterations: int,
) -> Dict[str, Any]:
    agent_history: List[Dict[str, Any]] = (
        state.get("agent_history") or []
    )

    # Number of workflow attempts used.
    iterations_used = int(
        state.get("iteration", 0) or 0
    )

    # Final execution result.
    test_result = state.get("test_result") or {}
    passed = bool(test_result.get("passed"))

    # Final workflow artifacts.
    final_code = state.get("code") or ""
    review_feedback = state.get("review") or ""
    generated_tests = state.get("tests") or ""

    # Combine stdout and stderr into final test output.
    test_output_parts: List[str] = []

    if test_result.get("stdout"):
        test_output_parts.append(
            str(test_result["stdout"])
        )

    if test_result.get("stderr"):
        test_output_parts.append(
            str(test_result["stderr"])
        )

    test_output = "\n".join(test_output_parts)

    # Extract optional quality score.
    quality_score: Optional[int] = None

    review_struct = state.get("review_struct")

    if isinstance(review_struct, dict):
        quality_score = review_struct.get(
            "quality_score"
        )

    # Build latest summary for each agent.
    agent_summary: Dict[str, str] = {}

    for event in agent_history:
        name = event.get("agent_name")
        summary = event.get("summary")

        if name and summary:
            agent_summary[str(name).upper()] = str(summary)

    # Build one iteration report for every executor execution.
    iterations: List[Dict[str, Any]] = []

    for event in agent_history:
        if str(event.get("agent_name", "")).upper() == "EXECUTOR":
            iterations.append(
                {
                    "iteration": event.get("iteration"),
                    "code": event.get("code"),
                    "review": event.get("review"),
                    "tests": event.get("tests"),
                    "test_result": event.get("test_result") or {},
                }
            )

    # Determine workflow completion status.
    if passed:
        status = "completed"
        termination_reason = "tests_passed"

    elif iterations_used >= max_iterations:
        status = "failed"
        termination_reason = "max_iterations_reached"

    else:
        status = "incomplete"
        termination_reason = "workflow_stopped_before_completion"

    return {
        "requirement": requirement,
        "status": status,
        "tests_passed": passed,
        "iterations_used": iterations_used,
        "max_iterations": max_iterations,
        "final_code": final_code,
        "review_feedback": review_feedback,
        "generated_tests": generated_tests,
        "test_output": test_output,
        "agent_summary": {
            "coder": agent_summary.get("CODER", ""),
            "reviewer": agent_summary.get("REVIEWER", ""),
            "tester": agent_summary.get("TESTER", ""),
            "executor": agent_summary.get("EXECUTOR", ""),
        },
        "termination_reason": termination_reason,
        "iterations": iterations,
        "quality_score": quality_score,
    }
