from typing import Any

import httpx
from langchain_openai import ChatOpenAI

from src.core.constants import ERR_LLM_CONFIG_MISSING
from src.core.interfaces import IOpenAIProvider


class HTTPClientManager:
    """
    HTTP client manager handling connection pools.
    Designed for lifecycle management via dependency injection, avoiding atexit global locks.
    """

    def __init__(self, client: httpx.Client | None = None) -> None:
        if client:
            self.client = client
        else:
            limits = httpx.Limits(max_keepalive_connections=10, max_connections=50)
            timeout = httpx.Timeout(60.0, connect=10.0)
            self.client = httpx.Client(limits=limits, timeout=timeout)

    def get_client(self) -> httpx.Client:
        return self.client

    def close(self) -> None:
        if hasattr(self, "client") and not self.client.is_closed:
            self.client.close()


class LLMProvider(IOpenAIProvider):
    """
    Concrete implementation providing parameterized access to ChatOpenAI instances.
    """

    def __init__(self, settings: Any, http_client: httpx.Client | None = None) -> None:
        self.settings = settings
        self.http_client = http_client

    def get_llm(self, model: str | None = None) -> ChatOpenAI:
        from src.core.validators import ApiKeyValidator

        if getattr(self.settings, "openai_api_key", None) is None:
            raise ValueError(ERR_LLM_CONFIG_MISSING)

        val1 = self.settings.openai_api_key.get_secret_value()
        ApiKeyValidator.validate_openai(val1)

        target_model = model or self.settings.llm_model
        client_to_use = (
            self.http_client if self.http_client is not None else HTTPClientManager().get_client()
        )

        return ChatOpenAI(
            model=target_model,
            api_key=self.settings.openai_api_key,
            max_retries=self.settings.resiliency.circuit_breaker_fail_max,
            http_client=client_to_use,
        )


class LLMFactory:
    """
    Factory class for creating LLM instances.
    Accepts an abstract IOpenAIProvider to completely decouple ChatOpenAI bindings for mocks.
    """

    def __init__(self, provider: IOpenAIProvider) -> None:
        self.provider = provider

    def get_llm(self, model: str | None = None) -> ChatOpenAI:
        """Retrieve the LLM instance from the underlying provider."""
        return self.provider.get_llm(model)
