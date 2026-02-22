from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from src.core.config import OPENAI_API_KEY


def get_llm(model: str = "gpt-4o") -> ChatOpenAI:
    """Factory to get the LLM client."""
    if not OPENAI_API_KEY:
        msg = "OPENAI_API_KEY not set in environment variables."
        raise ValueError(msg)
    return ChatOpenAI(model=model, api_key=SecretStr(OPENAI_API_KEY))
