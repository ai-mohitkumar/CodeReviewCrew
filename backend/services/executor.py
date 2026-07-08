from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass
class ExecutionResult:
    passed: bool
    stdout: str
    stderr: str
    returncode: int


def _repo_root() -> Path:
    """Return the CodeReviewCrew repository root."""
    return Path(__file__).resolve().parents[2]


def execute_tests(
    *,
    implementation_code: str,
    tests_code: str,
    timeout_seconds: int = 15,
    workspace_subdir: str = "workspace",
) -> ExecutionResult:
    """Write generated code and tests to workspace and run pytest."""

    root = _repo_root()
    workspace = root / workspace_subdir

    workspace.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Generated tests import from implementation.
    implementation_path = workspace / "implementation.py"
    test_path = workspace / "test_solution.py"

    implementation_path.write_text(
        implementation_code,
        encoding="utf-8",
    )

    test_path.write_text(
        tests_code,
        encoding="utf-8",
    )

    # Run pytest from inside workspace.
    # This makes:
    #
    # from implementation import ...
    #
    # resolve correctly.
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "test_solution.py",
    ]

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(workspace),
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )

        return ExecutionResult(
            passed=proc.returncode == 0,
            stdout=proc.stdout,
            stderr=proc.stderr,
            returncode=proc.returncode,
        )

    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""

        if isinstance(stdout, bytes):
            stdout = stdout.decode(
                errors="replace",
            )

        if isinstance(stderr, bytes):
            stderr = stderr.decode(
                errors="replace",
            )

        timeout_message = (
            f"Timeout after {timeout_seconds}s"
        )

        if stderr:
            stderr = f"{stderr}\n{timeout_message}"
        else:
            stderr = timeout_message

        return ExecutionResult(
            passed=False,
            stdout=stdout,
            stderr=stderr,
            returncode=124,
        )


def build_feedback(
    *,
    execution: ExecutionResult,
) -> Dict[str, Any]:
    """Convert ExecutionResult into workflow feedback."""

    return {
        "passed": execution.passed,
        "returncode": execution.returncode,
        "stdout": execution.stdout,
        "stderr": execution.stderr,
    }