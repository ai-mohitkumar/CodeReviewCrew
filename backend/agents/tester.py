from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class TestSpec:
    imports: str
    test_functions: List[str]

    def render(self) -> str:
        header = self.imports.rstrip() + "\n\n"
        return header + "\n\n".join(self.test_functions).rstrip() + "\n"


def _extract_callable_name(code: str) -> Optional[str]:
    """Return the first top-level function name from generated code."""

    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return node.name

    return None


def _guess_module_import(code: str) -> str:
    """Build the import used by generated pytest tests."""

    fn_name = _extract_callable_name(code)

    if not fn_name:
        return ""

    return f"from implementation import {fn_name}"


def _make_even_odd_tests(fn_name: str) -> List[str]:
    return [
        (
            f"def test_{fn_name}_even_number():\n"
            f'    assert {fn_name}(4) == "even"\n'
        ),
        (
            f"def test_{fn_name}_odd_number():\n"
            f'    assert {fn_name}(7) == "odd"\n'
        ),
        (
            f"def test_{fn_name}_zero():\n"
            f'    assert {fn_name}(0) == "even"\n'
        ),
        (
            f"def test_{fn_name}_negative_odd():\n"
            f'    assert {fn_name}(-3) == "odd"\n'
        ),
    ]


def _make_addition_tests(fn_name: str) -> List[str]:
    return [
        (
            f"def test_{fn_name}_positive_numbers():\n"
            f"    assert {fn_name}(2, 3) == 5\n"
        ),
        (
            f"def test_{fn_name}_negative_numbers():\n"
            f"    assert {fn_name}(-2, -3) == -5\n"
        ),
        (
            f"def test_{fn_name}_zero():\n"
            f"    assert {fn_name}(0, 0) == 0\n"
        ),
    ]


def _make_prime_tests(fn_name: str) -> List[str]:
    return [
        (
            f"def test_{fn_name}_prime_number():\n"
            f"    assert {fn_name}(7) is True\n"
        ),
        (
            f"def test_{fn_name}_composite_number():\n"
            f"    assert {fn_name}(9) is False\n"
        ),
        (
            f"def test_{fn_name}_one_is_not_prime():\n"
            f"    assert {fn_name}(1) is False\n"
        ),
        (
            f"def test_{fn_name}_two_is_prime():\n"
            f"    assert {fn_name}(2) is True\n"
        ),
    ]


def _make_palindrome_tests(fn_name: str) -> List[str]:
    return [
        (
            f"def test_{fn_name}_palindrome():\n"
            f'    assert {fn_name}("level") is True\n'
        ),
        (
            f"def test_{fn_name}_not_palindrome():\n"
            f'    assert {fn_name}("python") is False\n'
        ),
        (
            f"def test_{fn_name}_single_character():\n"
            f'    assert {fn_name}("a") is True\n'
        ),
    ]


def _make_safe_division_tests(fn_name: str) -> List[str]:
    return [
        (
            f"def test_{fn_name}_normal_division():\n"
            f"    assert {fn_name}(10, 2) == 5\n"
        ),
        (
            f"def test_{fn_name}_negative_division():\n"
            f"    assert {fn_name}(-10, 2) == -5\n"
        ),
        (
            f"def test_{fn_name}_division_by_zero():\n"
            f"    import pytest\n"
            f"    with pytest.raises(ValueError):\n"
            f"        {fn_name}(10, 0)\n"
        ),
    ]


def _make_deduplicate_tests(fn_name: str) -> List[str]:
    return [
        (
            f"def test_{fn_name}_removes_duplicates():\n"
            f"    assert {fn_name}([1, 2, 1, 3, 2]) == [1, 2, 3]\n"
        ),
        (
            f"def test_{fn_name}_preserves_order():\n"
            f'    assert {fn_name}(["b", "a", "b"]) == ["b", "a"]\n'
        ),
        (
            f"def test_{fn_name}_empty_list():\n"
            f"    assert {fn_name}([]) == []\n"
        ),
    ]


def _make_binary_search_tests(fn_name: str) -> List[str]:
    return [
        (
            f"def test_{fn_name}_finds_target():\n"
            f"    assert {fn_name}([1, 3, 5, 7, 9], 7) == 3\n"
        ),
        (
            f"def test_{fn_name}_missing_target():\n"
            f"    assert {fn_name}([1, 3, 5, 7, 9], 4) == -1\n"
        ),
        (
            f"def test_{fn_name}_empty_list():\n"
            f"    assert {fn_name}([], 4) == -1\n"
        ),
    ]


def _make_modulo_tests(fn_name: str) -> List[str]:
    return [
        (
            f"def test_{fn_name}_positive_numbers():\n"
            f"    assert {fn_name}(10, 3) == 1\n"
        ),
        (
            f"def test_{fn_name}_exact_division():\n"
            f"    assert {fn_name}(10, 5) == 0\n"
        ),
        (
            f"def test_{fn_name}_negative_dividend():\n"
            f"    assert {fn_name}(-10, 3) == 2\n"
        ),
    ]


def _make_fallback_tests(fn_name: str) -> List[str]:
    """Fallback smoke tests for unsupported requirements."""

    return [
        (
            f"def test_{fn_name}_callable_exists():\n"
            f"    assert callable({fn_name})\n"
        ),
    ]


def _select_tests(
    *,
    requirement: Optional[str],
    fn_name: str,
) -> tuple[List[str], str]:
    """Select semantic tests based on the programming requirement."""

    normalized = (requirement or "").lower()

    if "odd" in normalized and "even" in normalized:
        return _make_even_odd_tests(fn_name), "even_odd"

    if (
        "sum" in normalized
        or "add two" in normalized
        or "addition" in normalized
    ):
        return _make_addition_tests(fn_name), "addition"

    if "prime" in normalized:
        return _make_prime_tests(fn_name), "prime"

    if "palindrome" in normalized:
        return _make_palindrome_tests(fn_name), "palindrome"

    if (
        "safe division" in normalized
        or "division by zero" in normalized
    ):
        return _make_safe_division_tests(fn_name), "safe_division"

    if (
        "deduplicate" in normalized
        or "remove duplicates" in normalized
    ):
        return _make_deduplicate_tests(fn_name), "deduplicate"

    if "binary search" in normalized:
        return _make_binary_search_tests(fn_name), "binary_search"

    if "modulo" in normalized or "remainder" in normalized:
        return _make_modulo_tests(fn_name), "modulo"

    return _make_fallback_tests(fn_name), "fallback"


def generate_pytests(
    *,
    requirement: Optional[str] = None,
    code: str,
) -> Dict[str, Any]:
    """Generate deterministic semantic pytest tests."""

    fn_name = _extract_callable_name(code)

    if not fn_name:
        return {
            "test_code": (
                "import pytest\n\n\n"
                "def test_generated_implementation_exists():\n"
                "    pytest.fail("
                "'No top-level function found in generated code'"
                ")\n"
            ),
            "summary": {
                "callable_detected": False,
                "test_category": "invalid_implementation",
            },
        }

    imports = _guess_module_import(code)

    test_functions, test_category = _select_tests(
        requirement=requirement,
        fn_name=fn_name,
    )

    spec = TestSpec(
        imports=imports,
        test_functions=test_functions,
    )

    return {
        "test_code": spec.render(),
        "summary": {
            "callable_detected": True,
            "callable_name": fn_name,
            "test_category": test_category,
            "test_count": len(test_functions),
        },
    }


def save_tests(
    *,
    test_code: str,
    path: str = "tests/test_generated.py",
) -> None:
    with open(path, "w", encoding="utf-8") as file:
        file.write(test_code)