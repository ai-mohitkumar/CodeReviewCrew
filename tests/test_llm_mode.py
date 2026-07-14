from __future__ import annotations

import backend.agents.coder as coder_module


def test_generate_code_uses_llm_when_enabled(monkeypatch):
    monkeypatch.setenv("AGENT_MODE", "llm")

    class FakeLLMService:
        def __init__(self, *args, **kwargs):
            self.calls = []

        def generate(self, prompt: str) -> str:
            self.calls.append(prompt)
            return "def add(a, b):\n    return a + b\n"

    monkeypatch.setattr(coder_module, "LLMService", FakeLLMService)

    code = coder_module.generate_code(
        "Create a Python function named add that accepts two numbers and returns their sum."
    )

    assert "def add(a, b):" in code
    assert "return a + b" in code
