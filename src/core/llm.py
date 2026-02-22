from langchain_openai import ChatOpenAI

from src.core.config import settings


def get_llm(model: str | None = None) -> ChatOpenAI:
    """
    Factory to get the LLM client.

    Args:
        model: Optional model name override. Defaults to config settings.

    Returns:
        ChatOpenAI instance.

    Raises:
        ValueError: If OpenAI API key is missing.
    """
    if not settings.openai_api_key:
        msg = "LLM configuration error: API key is missing. Please check your .env file."
        raise ValueError(msg)

    return ChatOpenAI(model=model or settings.llm_model, api_key=settings.openai_api_key)
