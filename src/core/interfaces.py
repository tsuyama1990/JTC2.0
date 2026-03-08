import abc
from collections.abc import Iterator
from typing import Any


class LLMInterface(abc.ABC):
    @abc.abstractmethod
    def generate(self, prompt: str, system_message: str = "") -> str:
        """Generate text from prompt."""

    @abc.abstractmethod
    def generate_structured(self, prompt: str, schema: Any, system_message: str = "") -> Any:
        """Generate structured output conforming to a schema."""

    @abc.abstractmethod
    def stream(self, prompt: str, system_message: str = "") -> Iterator[Any]:
        """Stream generation."""


class RAGInterface(abc.ABC):
    @abc.abstractmethod
    def ingest_text(self, text: str | Iterator[str], source: str) -> None:
        """Ingest text into the RAG index."""

    @abc.abstractmethod
    def query(self, question: str) -> str:
        """Query the RAG index."""

    @abc.abstractmethod
    def persist_index(self) -> None:
        """Persist the index to disk."""


class SearchInterface(abc.ABC):
    @abc.abstractmethod
    def safe_search(self, query: str, include_raw_content: bool = False) -> str:
        """Search and return results as string."""
