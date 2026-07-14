from __future__ import annotations

import os
import re

from backend.services.llm_service import LLMService


def _llm_mode_enabled() -> bool:
    return os.getenv("AGENT_MODE", "").strip().lower() == "llm"


def _build_llm_prompt(
    *,
    prompt: str,
    previous_code: str | None,
    review_feedback: str | None,
    test_output: str | None,
    iteration: int,
) -> str:
    parts = [
        "You are generating Python code for CodeReviewCrew.",
        f"Iteration: {iteration}",
        f"Requirement:\n{prompt}",
    ]

    if previous_code:
        parts.append(f"Previous implementation:\n{previous_code}")

    if review_feedback:
        parts.append(f"Review feedback:\n{review_feedback}")

    if test_output:
        parts.append(f"Test output:\n{test_output}")

    parts.append(
        "Return only the final Python implementation with no markdown fences."
    )

    return "\n\n".join(parts)


def _extract_function_name(prompt: str) -> str:
    """Extract an explicitly requested Python function name."""

    patterns = [
        r"function\s+named\s+([A-Za-z_][A-Za-z0-9_]*)",
        r"function\s+called\s+([A-Za-z_][A-Za-z0-9_]*)",
    ]

    for pattern in patterns:
        match = re.search(pattern, prompt, flags=re.IGNORECASE)

        if match:
            return match.group(1)

    return "solution"


def _generate_add_function(function_name: str) -> str:
    return (
        f"def {function_name}(a, b):\n"
        '    """Return the sum of two numbers."""\n'
        "    return a + b\n"
    )


def _generate_prime_function(function_name: str) -> str:
    return (
        f"def {function_name}(n):\n"
        '    """Return True when n is prime, otherwise False."""\n'
        "    if n < 2:\n"
        "        return False\n"
        "\n"
        "    divisor = 2\n"
        "\n"
        "    while divisor * divisor <= n:\n"
        "        if n % divisor == 0:\n"
        "            return False\n"
        "        divisor += 1\n"
        "\n"
        "    return True\n"
    )


def _generate_palindrome_function(function_name: str) -> str:
    return (
        f"def {function_name}(value):\n"
        '    """Return True when value is a palindrome."""\n'
        "    text = str(value)\n"
        "    return text == text[::-1]\n"
    )


def _generate_safe_division_function(function_name: str) -> str:
    return (
        f"def {function_name}(a, b):\n"
        '    """Divide a by b and reject division by zero."""\n'
        "    if b == 0:\n"
        '        raise ValueError("division by zero")\n'
        "    return a / b\n"
    )


def _generate_deduplicate_function(function_name: str) -> str:
    return (
        f"def {function_name}(values):\n"
        '    """Remove duplicates while preserving input order."""\n'
        "    result = []\n"
        "    seen = set()\n"
        "\n"
        "    for value in values:\n"
        "        if value not in seen:\n"
        "            seen.add(value)\n"
        "            result.append(value)\n"
        "\n"
        "    return result\n"
    )


def _generate_binary_search_function(function_name: str) -> str:
    return (
        f"def {function_name}(values, target):\n"
        '    """Return the index of target or -1 when not found."""\n'
        "    left = 0\n"
        "    right = len(values) - 1\n"
        "\n"
        "    while left <= right:\n"
        "        middle = (left + right) // 2\n"
        "\n"
        "        if values[middle] == target:\n"
        "            return middle\n"
        "\n"
        "        if values[middle] < target:\n"
        "            left = middle + 1\n"
        "        else:\n"
        "            right = middle - 1\n"
        "\n"
        "    return -1\n"
    )


def _generate_even_odd_function(function_name: str) -> str:
    return (
        f"def {function_name}(n):\n"
        '    """Return "even" when n is even, otherwise "odd"."""\n'
        "    if n % 2 == 0:\n"
        '        return "even"\n'
        '    return "odd"\n'
    )


def _generate_modulo_function(
    function_name: str,
    *,
    iteration: int = 1,
    previous_code: str | None = None,
    test_output: str | None = None,
) -> str:
    """Generate a buggy modulo implementation first, then repair it."""

    if iteration == 1:
        return (
            f"def {function_name}(a, b):\n"
            '    """Return the remainder of a divided by b."""\n'
            "    # Intentional demo bug: floor division instead of modulo.\n"
            "    return a // b\n"
        )

    if previous_code and test_output:
        return (
            f"def {function_name}(a, b):\n"
            '    """Return the remainder of a divided by b."""\n'
            "    # Repaired after semantic tests failed.\n"
            "    return a % b\n"
        )

    return (
        f"def {function_name}(a, b):\n"
        '    """Return the remainder of a divided by b."""\n'
        "    return a % b\n"
    )


def generate_code(
    prompt: str,
    previous_code: str | None = None,
    review_feedback: str | None = None,
    test_output: str | None = None,
    iteration: int = 1,
) -> str:
    """Generate deterministic Python code for supported demo requirements."""

    if _llm_mode_enabled():
        llm_prompt = _build_llm_prompt(
            prompt=prompt,
            previous_code=previous_code,
            review_feedback=review_feedback,
            test_output=test_output,
            iteration=iteration,
        )
        return LLMService().generate(llm_prompt)

    normalized_prompt = prompt.lower()
    function_name = _extract_function_name(prompt)

    # Assign meaningful names when no explicit function name was provided.
    if function_name == "solution":
        if "odd" in normalized_prompt and "even" in normalized_prompt:
            function_name = "check_even_odd"

        elif "prime" in normalized_prompt:
            function_name = "is_prime"

        elif "palindrome" in normalized_prompt:
            function_name = "is_palindrome"

        elif (
            "safe division" in normalized_prompt
            or "division by zero" in normalized_prompt
        ):
            function_name = "safe_divide"

        elif (
            "deduplicate" in normalized_prompt
            or "remove duplicates" in normalized_prompt
        ):
            function_name = "deduplicate"

        elif "binary search" in normalized_prompt:
            function_name = "binary_search"

        elif "modulo" in normalized_prompt or "remainder" in normalized_prompt:
            function_name = "modulo"

        elif (
            "sum" in normalized_prompt
            or "add two" in normalized_prompt
            or "addition" in normalized_prompt
        ):
            function_name = "add"

    # Generate implementation.

    if "odd" in normalized_prompt and "even" in normalized_prompt:
        return _generate_even_odd_function(function_name)

    if (
        "sum" in normalized_prompt
        or "add two" in normalized_prompt
        or "addition" in normalized_prompt
    ):
        return _generate_add_function(function_name)

    if "prime" in normalized_prompt:
        return _generate_prime_function(function_name)

    if "palindrome" in normalized_prompt:
        return _generate_palindrome_function(function_name)

    if (
        "safe division" in normalized_prompt
        or "division by zero" in normalized_prompt
    ):
        return _generate_safe_division_function(function_name)

    if (
        "deduplicate" in normalized_prompt
        or "remove duplicates" in normalized_prompt
    ):
        return _generate_deduplicate_function(function_name)

    if "binary search" in normalized_prompt:
        return _generate_binary_search_function(function_name)

    if "modulo" in normalized_prompt or "remainder" in normalized_prompt:
        return _generate_modulo_function(
            function_name,
            iteration=iteration,
            previous_code=previous_code,
            test_output=test_output,
        )

    return (
        f"def {function_name}():\n"
        '    """Generated implementation placeholder."""\n'
        "    return None\n"
    )

