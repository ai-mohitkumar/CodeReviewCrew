from __future__ import annotations

from typing import Any, Optional, TypedDict


class ReviewState(TypedDict, total=False):
    # user input
    prompt: str

    # iterative generation/execution artifacts
    code: Optional[str]
    review: Optional[str]
    tests: Optional[str]
    test_result: Optional[dict[str, Any]]

    # iteration tracking
    iteration: int
    max_iterations: int

    # execution history for timeline/report
    agent_history: list[dict[str, Any]]

    # optional structured review
    review_struct: Optional[dict[str, Any]]

    # workflow termination metadata
    termination_reason: str

    # final structured report
    final_report: dict[str, Any]
