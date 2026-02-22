from langchain_openai import ChatOpenAI

from src.core.config import settings


def get_llm(model: str = "gpt-4o") -> ChatOpenAI:
    """Factory to get the LLM client."""
    if not settings.openai_api_key:
        msg = "LLM configuration error: API key is missing. Please check your .env file."
        raise ValueError(msg)

    return ChatOpenAI(model=model, api_key=settings.openai_api_key)
