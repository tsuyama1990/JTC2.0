from collections.abc import Iterator
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.core.config import get_settings
from src.core.interfaces import LLMInterface


class LangChainLLMAdapter(LLMInterface):
    """Adapter for LangChain ChatOpenAI."""

    def __init__(self, model: str | None = None) -> None:
        settings = get_settings()
        api_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else ""
        self.llm = ChatOpenAI(model=model or settings.llm_model, api_key=api_key)

    def generate(self, prompt: str, system_message: str = "") -> str:
        messages = []
        if system_message:
            messages.append(("system", system_message))
        messages.append(("user", prompt))

        chat_prompt = ChatPromptTemplate.from_messages(messages)
        chain = chat_prompt | self.llm
        result = chain.invoke({})
        return str(result.content)

    def generate_structured(self, prompt: str, schema: Any, system_message: str = "") -> Any:
        messages = []
        if system_message:
            messages.append(("system", system_message))
        messages.append(("user", prompt))

        chat_prompt = ChatPromptTemplate.from_messages(messages)
        chain = chat_prompt | self.llm.with_structured_output(schema)
        return chain.invoke({})

    def stream(self, prompt: str, system_message: str = "") -> Iterator[Any]:
        messages = []
        if system_message:
            messages.append(("system", system_message))
        messages.append(("user", prompt))

        chat_prompt = ChatPromptTemplate.from_messages(messages)
        chain = chat_prompt | self.llm
        yield from chain.stream({})
