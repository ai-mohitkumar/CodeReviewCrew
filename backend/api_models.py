from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class RunRequest(TypedDict, total=False):
    requirement: str


class IterationReport(TypedDict, total=False):
    iteration: int
    code: str
    review: Any
    tests: str
    test_result: Dict[str, Any]


class RunReport(TypedDict, total=False):
    requirement: str
    initial_generated_code: str
    iterations: List[IterationReport]
    final_code: str
    final_passed: bool
    iterations_count: int
    quality_score: Optional[int]
    final_stdout: str
    final_stderr: str

