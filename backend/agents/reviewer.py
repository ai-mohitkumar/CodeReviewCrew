from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import ast


@dataclass
class Review:
    approved: bool
    quality_score: int
    issues: List[Dict[str, Any]]
    suggestions: List[Dict[str, Any]]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "approved": self.approved,
            "quality_score": self.quality_score,
            "issues": self.issues,
            "suggestions": self.suggestions,
        }


def _try_parse_ast(code: str) -> Optional[ast.AST]:
    try:
        return ast.parse(code)
    except SyntaxError:
        return None


def _basic_security_checks(code: str) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []
    lowered = code.lower()

    # Very small, conservative set of heuristics.
    risky_substrings = [
        "eval(",
        "exec(",
        "subprocess.popen",
        "os.system(",
        "pickle.loads",
        "yaml.load",
    ]
    for s in risky_substrings:
        if s in lowered:
            issues.append(
                {
                    "type": "security",
                    "severity": "high" if s in ("eval(", "exec(") else "medium",
                    "message": f"Potentially unsafe pattern detected: `{s}`",
                    "hint": "Avoid dynamic execution / unsafe deserialization when possible.",
                }
            )
    return issues


def _edge_case_hints(requirement: Optional[str], code: str) -> List[Dict[str, Any]]:
    suggestions: List[Dict[str, Any]] = []
    if not requirement:
        return suggestions

    req = requirement.lower()
    # Heuristic: common boundary items.
    if any(k in req for k in ["empty", "none", "null"]):
        suggestions.append(
            {"type": "edge_case", "message": "Handle empty/None inputs explicitly.", "hint": "Add early returns / validation."}
        )
    if any(k in req for k in ["range", "between", "min", "max", "limit"]):
        suggestions.append(
            {
                "type": "edge_case",
                "message": "Validate boundary conditions (min/max/limits).",
                "hint": "Use inclusive/exclusive semantics consistent with requirement.",
            }
        )
    if any(k in req for k in ["invalid", "error", "raise", "exception"]):
        suggestions.append(
            {
                "type": "edge_case",
                "message": "Define behavior for invalid inputs (raise vs return sentinel).",
                "hint": "Document exception types/messages.",
            }
        )

    # If code contains no try/except but requirement mentions invalid inputs.
    if "raise" in req or "exception" in req:
        if "try:" not in code and "except" not in code:
            suggestions.append(
                {
                    "type": "maintainability",
                    "message": "Consider explicit error handling for invalid inputs.",
                    "hint": "Add try/except around parsing/conversion if applicable.",
                }
            )

    return suggestions


def review_code(*, requirement: Optional[str] = None, code: str, generated_tests: Optional[str] = None) -> Dict[str, Any]:
    """Review an implementation against a requirement.

    Heuristic reviewer meant to run without LLM access.

    Returns a structured dict:
      - approved: bool
      - quality_score: int (0-100)
      - issues: [{type, severity, message, hint?}]
      - suggestions: [{type, message, hint?}]
    """

    issues: List[Dict[str, Any]] = []
    suggestions: List[Dict[str, Any]] = []

    if not code.strip():
        return Review(
            approved=False,
            quality_score=0,
            issues=[{"type": "correctness", "severity": "high", "message": "Code is empty."}],
            suggestions=[{"type": "general", "message": "Provide an implementation."}],
        ).as_dict()

    tree = _try_parse_ast(code)
    if tree is None:
        return Review(
            approved=False,
            quality_score=5,
            issues=[{"type": "correctness", "severity": "high", "message": "Code has syntax errors; cannot parse."}],
            suggestions=[{"type": "general", "message": "Fix syntax errors."}],
        ).as_dict()

    # Security
    issues.extend(_basic_security_checks(code))

    # Maintainability heuristics
    # - function/class docstrings missing
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.body:
                first_stmt = node.body[0]
                if not (
                    isinstance(first_stmt, ast.Expr)
                    and isinstance(getattr(first_stmt, "value", None), ast.Constant)
                    and isinstance(getattr(first_stmt.value, "value", None), str)
                ):
                    suggestions.append(
                        {
                            "type": "readability",
                            "message": f"Missing docstring for `{getattr(node, 'name', 'item')}`.",
                            "hint": "Add a short docstring describing behavior, args, and return value.",
                        }
                    )

    # Performance heuristics: too many nested loops (very rough)
    loop_depth = 0

    class _LoopVisitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.max_depth = 0
            self._current = 0

        def visit_For(self, n: ast.For) -> Any:
            self._current += 1
            self.max_depth = max(self.max_depth, self._current)
            self.generic_visit(n)
            self._current -= 1

        def visit_AsyncFor(self, n: ast.AsyncFor) -> Any:
            self._current += 1
            self.max_depth = max(self.max_depth, self._current)
            self.generic_visit(n)
            self._current -= 1

    lv = _LoopVisitor()
    lv.visit(tree)
    if lv.max_depth >= 3:
        suggestions.append(
            {
                "type": "performance",
                "message": "Deeply nested loops detected; consider optimizing or reducing complexity.",
                "hint": "Look for opportunities to precompute, use sets/maps, or avoid O(n^3) patterns.",
            }
        )

    # Requirement alignment heuristics
    if requirement:
        suggestions.extend(_edge_case_hints(requirement, code))

        # Simple check: if requirement mentions pytest and there are no tests.
        if "pytest" in requirement.lower() and not generated_tests:
            suggestions.append(
                {
                    "type": "correctness",
                    "message": "Requirement suggests tests, but no generated_tests were provided to reviewer.",
                    "hint": "Generate tests and rerun review with them included.",
                }
            )

    # Compute quality score
    score = 85
    # Penalize security issues
    if issues:
        # high severity => heavier penalty
        high = sum(1 for i in issues if i.get("severity") == "high")
        med = sum(1 for i in issues if i.get("severity") == "medium")
        score -= 25 * high + 10 * med
    # Penalize docstring suggestions lightly
    score -= min(20, len([s for s in suggestions if s.get("type") == "readability"]) * 2)
    # Penalize overly deep loops
    score -= 10 if lv.max_depth >= 3 else 0

    approved = score >= 70 and not any(i.get("severity") == "high" for i in issues)
    score = max(0, min(100, int(score)))

    return Review(
        approved=approved,
        quality_score=score,
        issues=issues,
        suggestions=suggestions[:25],
    ).as_dict()

