import os
from dataclasses import dataclass

from dotenv import load_dotenv


# Load .env reliably even if the process working directory is different.
from pathlib import Path

_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"  # CodeReviewCrew/.env
load_dotenv(dotenv_path=str(_ENV_PATH))



@dataclass
class LLMConfig:
    model: str


class LLMService:
    def __init__(self, model: str | None = None):
        self.config = LLMConfig(model=model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))

        # Gemini SDK
        from google import genai  # type: ignore

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set in .env")

        self.client = genai.Client(api_key=api_key)

    def generate(self, prompt: str) -> str:
        # Minimal single call; expanded later.
        resp = self.client.models.generate_content(
            model=self.config.model,
            contents=prompt,
        )
        # google-genai returns a rich object; best-effort extraction
        try:
            return resp.text
        except Exception:
            return str(resp)

