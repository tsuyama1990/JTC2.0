from functools import lru_cache

from src.core.config import get_settings
from src.core.constants import ERR_LLM_CONFIG_MISSING
from src.core.interfaces import ILLMClient


@lru_cache
def get_llm(model: str | None = None) -> ILLMClient:
    """
    Factory to get the LLM client.
    Cached to prevent resource waste (Architecture constraint).

    Args:
        model: Optional model name override. Defaults to config settings.

    Returns:
        ILLMClient instance.

    Raises:
        ValueError: If OpenAI API key is missing.
    """
    # Local import to decouple from concrete classes
    from langchain_openai import ChatOpenAI

    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError(ERR_LLM_CONFIG_MISSING)

    # Returns an instance that structurally types ILLMClient
    return ChatOpenAI(model=model or settings.llm_model, api_key=settings.openai_api_key) # type: ignore
