from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_run_requires_requirement():
    response = client.post("/api/run", json={})

    assert response.status_code == 422


def test_run_rejects_wrong_requirement_type():
    response = client.post(
        "/api/run",
        json={"requirement": {"invalid": "value"}},
    )

    assert response.status_code == 422

def test_run_returns_successful_final_report(monkeypatch):
    class FakeWorkflow:
        def invoke(self, initial_state):
            return {
                "final_report": {
                    "requirement": initial_state["prompt"],
                    "status": "completed",
                    "tests_passed": True,
                    "iterations_used": 1,
                    "max_iterations": initial_state["max_iterations"],
                    "final_code": "def add(a, b): return a + b",
                    "review_feedback": "Code is correct.",
                    "generated_tests": "def test_add(): assert add(2, 3) == 5",
                    "test_output": "1 passed",
                    "agent_summary": {
                        "coder": "Generated implementation.",
                        "reviewer": "Reviewed implementation.",
                        "tester": "Generated tests.",
                        "executor": "Tests passed.",
                    },
                    "termination_reason": "tests_passed",
                    "iterations": [],
                    "quality_score": 90,
                }
            }

    monkeypatch.setattr(
        "backend.main.build_workflow",
        lambda: FakeWorkflow(),
    )

    response = client.post(
        "/api/run",
        json={
            "requirement": "Create a Python add function"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["requirement"] == "Create a Python add function"
    assert data["status"] == "completed"
    assert data["tests_passed"] is True
    assert data["termination_reason"] == "tests_passed"
    assert data["iterations_used"] == 1
    assert "final_code" in data
    assert "agent_summary" in data