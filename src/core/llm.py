import threading

import httpx
from langchain_openai import ChatOpenAI

from src.core.config import get_settings
from src.core.constants import ERR_LLM_CONFIG_MISSING

# Use thread-local storage for httpx.Client to be thread safe
_local_storage = threading.local()


def get_llm(model: str | None = None, http_client: httpx.Client | None = None) -> ChatOpenAI:
    """
    Factory to get a new LLM client instance.
    Uses explicit connection limits and thread-local storage for the HTTP client.
    """
    settings = get_settings()
    from src.core.validators import ApiKeyValidator

    # Strictly validate key formatting and readiness before creating the client
    ApiKeyValidator.validate(settings)

    if not settings.openai_api_key:
        raise ValueError(ERR_LLM_CONFIG_MISSING)

    target_model = model or settings.llm_model

    # Use provided client or thread-local client to prevent connection leaking
    if http_client is None:
        if not hasattr(_local_storage, "http_client"):
            limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
            timeout = httpx.Timeout(60.0, connect=10.0)
            _local_storage.http_client = httpx.Client(limits=limits, timeout=timeout)
        http_client = _local_storage.http_client

    return ChatOpenAI(
        model=target_model,
        api_key=settings.openai_api_key,
        max_retries=settings.resiliency.circuit_breaker_fail_max,
        http_client=http_client,
    )


def clear_llm_cache() -> None:
    """No-op placeholder for tests. Caching has been removed in favor of Dependency Injection."""
