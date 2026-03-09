import atexit
import threading
from typing import Any

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
        limits = httpx.Limits(max_keepalive_connections=10, max_connections=50)
        timeout = httpx.Timeout(60.0, connect=10.0)
        self.client = httpx.Client(limits=limits, timeout=timeout)
        atexit.register(self.close)

    def get_client(self) -> httpx.Client:
        return self.client

    def close(self) -> None:
        if hasattr(self, "client") and not self.client.is_closed:
            self.client.close()


class LLMFactory:
    """
    Factory class for creating LLM instances.
    Provides methods to instantiate ChatOpenAI using dependency injection.
    """

    def __init__(self, settings: Any = None, http_client: httpx.Client | None = None) -> None:
        self.settings = settings or get_settings()
        self.http_client = http_client

    def create_llm(self, model: str | None = None) -> ChatOpenAI:
        """
        Creates and returns a ChatOpenAI instance using configured settings.
        """
        from src.core.validators import ApiKeyValidator

        # Strictly validate key formatting and readiness before creating the client
        if getattr(self.settings, "openai_api_key", None) is None:
            raise ValueError(ERR_LLM_CONFIG_MISSING)

        val1 = self.settings.openai_api_key.get_secret_value()
        ApiKeyValidator.validate_openai(val1)

        target_model = model or self.settings.llm_model

        # Use provided client or global pooled client to prevent connection leaking
        client_to_use = self.http_client if self.http_client is not None else HTTPClientManager().get_client()

        return ChatOpenAI(
            model=target_model,
            api_key=self.settings.openai_api_key,
            max_retries=self.settings.resiliency.circuit_breaker_fail_max,
            http_client=client_to_use,
        )


def get_llm(model: str | None = None, http_client: httpx.Client | None = None) -> ChatOpenAI:
    """
    Legacy helper function mapping to LLMFactory.create_llm().
    """
    factory = LLMFactory(http_client=http_client)
    return factory.create_llm(model)


def clear_llm_cache() -> None:
    """Helper for testing to reset the HTTP client pool."""
    manager = HTTPClientManager()
    with manager._lock:
        manager.close()
        HTTPClientManager._instance = None
