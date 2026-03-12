from functools import lru_cache

from src.core.config import get_settings
from src.core.constants import ERR_LLM_CONFIG_MISSING
from src.core.interfaces import ILLMClient


class LLMFactory:
    """Factory pattern for LLM client instantiation."""

    _instance: ILLMClient | None = None

    @classmethod
    def get_client(cls, model: str | None = None) -> ILLMClient:
        if cls._instance is not None and model is None:
            return cls._instance

        from langchain_openai import ChatOpenAI

        settings = get_settings()
        if not settings.openai_api_key:
            raise ValueError(ERR_LLM_CONFIG_MISSING)

        client = ChatOpenAI(model=model or settings.llm_model, api_key=settings.openai_api_key)
        if model is None:
            cls._instance = client # type: ignore
        return client # type: ignore

    @classmethod
    def set_client(cls, client: ILLMClient) -> None:
        """Inject a specific client instance, useful for testing."""
        cls._instance = client

def get_llm(model: str | None = None) -> ILLMClient:
    """
    Deprecated. Use LLMFactory instead.
    """
    return LLMFactory.get_client(model)
