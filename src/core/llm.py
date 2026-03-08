import httpx
from langchain_openai import ChatOpenAI

from src.core.config import get_settings
from src.core.constants import ERR_LLM_CONFIG_MISSING

# Global HTTP client to prevent connection leaks
_global_http_client: httpx.Client | None = None


def get_llm(model: str | None = None) -> ChatOpenAI:
    """
    Factory to get a new LLM client instance.
    Uses explicit connection limits. Callers should inject the client to avoid repeated instantiations.
    """
    global _global_http_client

    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError(ERR_LLM_CONFIG_MISSING)

    target_model = model or settings.llm_model

    # Use httpx.Client with explicit limits to prevent connection leaking
    if _global_http_client is None:
        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
        timeout = httpx.Timeout(60.0, connect=10.0)
        _global_http_client = httpx.Client(limits=limits, timeout=timeout)

    return ChatOpenAI(
        model=target_model,
        api_key=settings.openai_api_key,
        max_retries=settings.resiliency.circuit_breaker_fail_max,
        http_client=_global_http_client,
    )


def clear_llm_cache() -> None:
    """No-op placeholder for tests. Caching has been removed in favor of Dependency Injection."""
