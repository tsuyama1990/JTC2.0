from collections.abc import Iterator
from functools import lru_cache
from typing import Any

from langchain_openai import ChatOpenAI

from src.core.config import get_settings
from src.core.constants import ERR_LLM_CONFIG_MISSING
from src.core.interfaces import LLMClient, LLMClientStructured


class LangChainStructuredOutput(LLMClientStructured):
    """Wrapper for LangChain's structured output."""

    def __init__(self, chain: Any) -> None:
        self.chain = chain

    def invoke(self, prompt: str | list[Any] | dict[str, Any]) -> Any:
        """Invoke the structured output chain."""
        return self.chain.invoke(prompt)


class LangChainLLM(LLMClient):
    """Wrapper for LangChain LLM to implement LLMClient protocol."""

    def __init__(self, llm: ChatOpenAI) -> None:
        self.llm = llm

    def invoke(self, prompt: str | list[Any]) -> Any:
        return self.llm.invoke(prompt)

    def stream(self, prompt: str | list[Any]) -> Iterator[Any]:
        return self.llm.stream(prompt)

    def with_structured_output(self, schema: Any) -> LLMClientStructured:
        chain = self.llm.with_structured_output(schema)
        return LangChainStructuredOutput(chain)


@lru_cache
def get_llm(model: str | None = None) -> LLMClient:
    """
    Factory to get the LLM client.
    Cached to prevent resource waste (Architecture constraint).

    Args:
        model: Optional model name override. Defaults to config settings.

    Returns:
        LLMClient instance.

    Raises:
        ValueError: If OpenAI API key is missing.
    """
    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError(ERR_LLM_CONFIG_MISSING)

    chat_model = ChatOpenAI(model=model or settings.llm_model, api_key=settings.openai_api_key)
    return LangChainLLM(chat_model)
