import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


# Load .env reliably even if the process working directory is different.
_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"  # CodeReviewCrew/.env
load_dotenv(dotenv_path=str(_ENV_PATH))


@dataclass
class LLMConfig:
    model: str


class LLMService:
    def __init__(self, model: str | None = None):
        self.config = LLMConfig(model=model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
        self.client = None
        self.error_message = None

        try:
            from google import genai  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            self.error_message = f"google-genai is not available: {exc}"
            return

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            self.error_message = "GEMINI_API_KEY is not set in .env"
            return

        self.client = genai.Client(api_key=api_key)

    def is_available(self) -> bool:
        return self.client is not None

    def generate(self, prompt: str) -> str:
        if not self.is_available():
            raise RuntimeError(self.error_message or "LLM service is unavailable")

        resp = self.client.models.generate_content(
            model=self.config.model,
            contents=prompt,
        )

        try:
            return resp.text
        except Exception:
            return str(resp)

