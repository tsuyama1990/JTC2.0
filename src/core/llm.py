from langchain_openai import ChatOpenAI

from src.core.config import get_settings
from src.core.constants import ERR_LLM_CONFIG_MISSING


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
    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError(ERR_LLM_CONFIG_MISSING)

    return ChatOpenAI(model=model or settings.llm_model, api_key=settings.openai_api_key)
