from __future__ import annotations

from types import SimpleNamespace

import backend.graph.workflow as workflow_module


def test_workflow_stops_at_max_iterations(monkeypatch):
    calls = {
        "coder": 0,
        "reviewer": 0,
        "tester": 0,
        "executor": 0,
    }

    def fake_generate_code(prompt, **kwargs):
        calls["coder"] += 1

        return "def solution():\n    return 0"

    def fake_review_code(*, requirement, code, generated_tests=None):
        calls["reviewer"] += 1

        return {
            "approved": False,
            "issues": ["Incorrect implementation"],
            "suggestions": ["Fix the implementation"],
            "quality_score": 40,
        }

    def fake_generate_pytests(*, requirement, code):
        calls["tester"] += 1

        return {
            "test_code": (
                "def test_solution():\n"
                "    assert solution() == 1"
            ),
            "summary": "Generated mocked tests.",
        }

    def fake_execute_tests(
        *,
        implementation_code,
        tests_code,
        timeout_seconds,
        workspace_subdir,
    ):
        calls["executor"] += 1

        return SimpleNamespace(
            passed=False,
            returncode=1,
            stdout="1 failed",
            stderr="AssertionError",
        )

    monkeypatch.setattr(
        workflow_module,
        "generate_code",
        fake_generate_code,
    )

    monkeypatch.setattr(
        workflow_module,
        "review_code",
        fake_review_code,
    )

    monkeypatch.setattr(
        workflow_module,
        "generate_pytests",
        fake_generate_pytests,
    )

    monkeypatch.setattr(
        workflow_module,
        "execute_tests",
        fake_execute_tests,
    )

    workflow = workflow_module.build_workflow()

    initial_state = {
        "prompt": "Create a solution function.",
        "iteration": 0,
        "max_iterations": 3,
        "code": None,
        "review": None,
        "tests": None,
        "test_result": None,
        "agent_history": [],
        "review_struct": None,
        "termination_reason": "",
        "final_report": {},
    }

    final_state = workflow.invoke(initial_state)

    assert final_state["test_result"]["passed"] is False
    assert final_state["iteration"] == 3

    assert calls["coder"] == 3
    assert calls["reviewer"] == 3
    assert calls["tester"] == 3
    assert calls["executor"] == 3

    report = final_state["final_report"]

    assert report["tests_passed"] is False
    assert report["status"] == "failed"
    assert report["termination_reason"] == "max_iterations_reached"
    assert report["iterations_used"] == 3

    assert len(final_state["agent_history"]) == 12


def test_final_report_contains_required_fields(monkeypatch):
    def fake_generate_code(prompt, **kwargs):
        return "def solution():\n    return 1"

    def fake_review_code(*, requirement, code, generated_tests=None):
        return {
            "approved": True,
            "issues": [],
            "suggestions": [],
            "quality_score": 95,
        }

    def fake_generate_pytests(*, requirement, code):
        return {
            "test_code": (
                "def test_solution():\n"
                "    assert solution() == 1"
            ),
            "summary": "Generated mocked tests.",
        }

    def fake_execute_tests(
        *,
        implementation_code,
        tests_code,
        timeout_seconds,
        workspace_subdir,
    ):
        return SimpleNamespace(
            passed=True,
            returncode=0,
            stdout="1 passed",
            stderr="",
        )

    monkeypatch.setattr(
        workflow_module,
        "generate_code",
        fake_generate_code,
    )

    monkeypatch.setattr(
        workflow_module,
        "review_code",
        fake_review_code,
    )

    monkeypatch.setattr(
        workflow_module,
        "generate_pytests",
        fake_generate_pytests,
    )

    monkeypatch.setattr(
        workflow_module,
        "execute_tests",
        fake_execute_tests,
    )

    workflow = workflow_module.build_workflow()

    initial_state = {
        "prompt": "Create a solution function.",
        "iteration": 0,
        "max_iterations": 3,
        "code": None,
        "review": None,
        "tests": None,
        "test_result": None,
        "agent_history": [],
        "review_struct": None,
        "termination_reason": "",
        "final_report": {},
    }

    final_state = workflow.invoke(initial_state)

    report = final_state["final_report"]

    required_fields = {
        "requirement",
        "status",
        "tests_passed",
        "iterations_used",
        "max_iterations",
        "final_code",
        "review_feedback",
        "generated_tests",
        "test_output",
        "agent_summary",
        "termination_reason",
    }

    assert required_fields.issubset(report.keys())

    assert report["requirement"] == "Create a solution function."
    assert report["status"] == "completed"
    assert report["tests_passed"] is True
    assert report["iterations_used"] == 1
    assert report["max_iterations"] == 3
    assert report["termination_reason"] == "tests_passed"

    assert report["final_code"]
    assert report["review_feedback"]
    assert report["generated_tests"]
    assert report["test_output"]

    assert set(report["agent_summary"].keys()) == {
        "coder",
        "reviewer",
        "tester",
        "executor",
    }


def test_workflow_repairs_modulo_after_failed_tests(monkeypatch):
    real_generate_code = workflow_module.generate_code

    calls = {
        "coder": 0,
        "executor": 0,
    }

    def tracked_generate_code(prompt, **kwargs):
        calls["coder"] += 1
        return real_generate_code(prompt, **kwargs)

    def fake_review_code(*, requirement, code, generated_tests=None):
        passed_review = "return a % b" in code

        return {
            "approved": passed_review,
            "issues": [] if passed_review else ["Incorrect modulo operator."],
            "suggestions": (
                []
                if passed_review
                else ["Use the modulo operator instead of floor division."]
            ),
            "quality_score": 95 if passed_review else 40,
        }

    def fake_generate_pytests(*, requirement, code):
        return {
            "test_code": (
                "from implementation import modulo\n\n"
                "def test_modulo_positive():\n"
                "    assert modulo(10, 3) == 1\n\n"
                "def test_modulo_exact_division():\n"
                "    assert modulo(10, 5) == 0\n"
            ),
            "summary": "Generated semantic modulo tests.",
        }

    def fake_execute_tests(
        *,
        implementation_code,
        tests_code,
        timeout_seconds,
        workspace_subdir,
    ):
        calls["executor"] += 1

        if "return a // b" in implementation_code:
            return SimpleNamespace(
                passed=False,
                returncode=1,
                stdout="2 failed",
                stderr="AssertionError",
            )

        return SimpleNamespace(
            passed=True,
            returncode=0,
            stdout="2 passed",
            stderr="",
        )

    monkeypatch.setattr(
        workflow_module,
        "generate_code",
        tracked_generate_code,
    )
    monkeypatch.setattr(
        workflow_module,
        "review_code",
        fake_review_code,
    )
    monkeypatch.setattr(
        workflow_module,
        "generate_pytests",
        fake_generate_pytests,
    )
    monkeypatch.setattr(
        workflow_module,
        "execute_tests",
        fake_execute_tests,
    )

    workflow = workflow_module.build_workflow()

    initial_state = {
        "prompt": "Create a Python function named modulo that returns the remainder.",
        "iteration": 0,
        "max_iterations": 3,
        "code": None,
        "review": None,
        "tests": None,
        "test_result": None,
        "agent_history": [],
        "review_struct": None,
        "termination_reason": "",
        "final_report": {},
    }

    final_state = workflow.invoke(initial_state)

    assert final_state["test_result"]["passed"] is True
    assert final_state["iteration"] == 2
    assert calls["coder"] == 2
    assert calls["executor"] == 2

    report = final_state["final_report"]

    assert report["status"] == "completed"
    assert report["tests_passed"] is True
    assert report["iterations_used"] == 2
    assert report["termination_reason"] == "tests_passed"

    assert "return a // b" in report["iterations"][0]["code"]
    assert report["iterations"][0]["test_result"]["passed"] is False

    assert "return a % b" in report["iterations"][1]["code"]
    assert report["iterations"][1]["test_result"]["passed"] is True

    assert len(final_state["agent_history"]) == 8

