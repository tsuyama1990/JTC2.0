import atexit
import threading

import httpx
from langchain_openai import ChatOpenAI

from src.core.config import get_settings
from src.core.constants import ERR_LLM_CONFIG_MISSING


# Global thread-safe HTTP client pool manager
class HTTPClientManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls) -> "HTTPClientManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init()
        return cls._instance

    def _init(self) -> None:
        settings = get_settings()
        limits = httpx.Limits(max_keepalive_connections=settings.resiliency.max_keepalive_connections, max_connections=settings.resiliency.max_connections)
        timeout = httpx.Timeout(60.0, connect=10.0)
        self.client = httpx.Client(limits=limits, timeout=timeout)
        atexit.register(self.close)

    def get_client(self) -> httpx.Client:
        return self.client

    def close(self) -> None:
        if hasattr(self, "client") and not self.client.is_closed:
            self.client.close()


from functools import cache  # noqa: E402


@cache
def get_llm(model: str | None = None, http_client: httpx.Client | None = None) -> ChatOpenAI:
    """
    Factory to get a cached LLM client instance.
    Uses a properly pooled and managed global HTTP client instance unless one is injected.
    The ChatOpenAI instance itself is cached to prevent connection exhaustion.
    """
    settings = get_settings()
    from src.core.validators import ApiKeyValidator

    # Strictly validate key formatting and readiness before creating the client
    ApiKeyValidator.validate(settings)

    if getattr(settings, "openai_api_key", None) is None:
        raise ValueError(ERR_LLM_CONFIG_MISSING)

    target_model = model or settings.llm_model

    # Use provided client or global pooled client to prevent connection leaking
    client_to_use = http_client if http_client is not None else HTTPClientManager().get_client()

    return ChatOpenAI(
        model=target_model,
        api_key=settings.openai_api_key,
        max_retries=settings.resiliency.circuit_breaker_fail_max,
        http_client=client_to_use,
    )


def clear_llm_cache() -> None:
    """Helper for testing to reset the LLM cache and HTTP client pool."""
    get_llm.cache_clear()
    manager = HTTPClientManager()
    with manager._lock:
        manager.close()
        HTTPClientManager._instance = None
