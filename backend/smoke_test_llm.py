import os
from pathlib import Path

from backend.services.llm_service import LLMService
from dotenv import load_dotenv

# Ensure .env is loaded when running this script directly.
_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"  # CodeReviewCrew/.env
load_dotenv(dotenv_path=str(_ENV_PATH))



def main() -> None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set in .env")


    llm = LLMService()
    prompt = "Give a one-sentence explanation of what unit testing is."
    out = llm.generate(prompt)
    print(out)


if __name__ == "__main__":
    main()

