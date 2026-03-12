from src.core.config import get_settings
from src.core.constants import ERR_LLM_CONFIG_MISSING
from src.core.interfaces import ILLMClient


class LLMFactory:
    """Provides LLM clients via dependency injection."""

    def __init__(self, client: ILLMClient | None = None) -> None:
        self._client = client

    def get_client(self, model: str | None = None) -> ILLMClient:
        if self._client is not None and model is None:
            return self._client

        from langchain_openai import ChatOpenAI

        settings = get_settings()
        if not settings.openai_api_key:
            raise ValueError(ERR_LLM_CONFIG_MISSING)

        client = ChatOpenAI(
            model=model or settings.llm_model, api_key=settings.openai_api_key.get_secret_value()
        )
        if model is None:
            self._client = client  # type: ignore
        return client  # type: ignore


_default_factory = LLMFactory()


def get_llm(model: str | None = None) -> ILLMClient:
    """
    Backward compatible getter, preferring DI.
    """
    return _default_factory.get_client(model)
