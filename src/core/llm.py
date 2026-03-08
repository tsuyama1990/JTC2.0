from functools import lru_cache

import httpx
from langchain_openai import ChatOpenAI

from src.core.config import get_settings
from src.core.constants import ERR_LLM_CONFIG_MISSING


@lru_cache(maxsize=4)
def get_llm(model: str | None = None) -> ChatOpenAI:
    """
    Factory to get the LLM client with built-in connection pooling and retries.
    Cached to prevent resource waste (Architecture constraint).

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

    # Use httpx.Client with explicit limits to prevent connection leaking
    limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
    timeout = httpx.Timeout(60.0, connect=10.0)
    http_client = httpx.Client(limits=limits, timeout=timeout)

    return ChatOpenAI(
        model=model or settings.llm_model,
        api_key=settings.openai_api_key,
        max_retries=settings.resiliency.circuit_breaker_fail_max,
        http_client=http_client
    )

def clear_llm_cache() -> None:
    """Clear the LLM client cache to release resources or rotate keys."""
    get_llm.cache_clear()
