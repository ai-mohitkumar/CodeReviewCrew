from fastapi import FastAPI
from pydantic import BaseModel

from backend.graph.workflow import build_workflow


app = FastAPI(title="CodeReviewCrew Backend")


@app.get("/health")
def health():
    return {"status": "ok"}


class RunRequest(BaseModel):
    requirement: str


@app.post("/api/run")
def run(req: RunRequest):
    """Run the LangGraph coder → reviewer → tester → executor loop."""

    workflow = build_workflow()

    initial_state = {
        "prompt": req.requirement,
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

    return final_state["final_report"]