from functools import lru_cache

from src.core.config import get_settings
from src.core.constants import ERR_LLM_CONFIG_MISSING
from src.core.interfaces import LLMInterface


@lru_cache
def get_llm(model: str | None = None) -> LLMInterface:
    """
    Factory to get the LLM client.
    Cached to prevent resource waste (Architecture constraint).

    Args:
        model: Optional model name override. Defaults to config settings.

    Returns:
        LLMInterface instance.

    Raises:
        ValueError: If OpenAI API key is missing.
    """
    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError(ERR_LLM_CONFIG_MISSING)

    from src.adapters.llm_adapter import LangChainLLMAdapter

    return LangChainLLMAdapter(model=model or settings.llm_model)
