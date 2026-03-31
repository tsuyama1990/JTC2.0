from abc import abstractmethod
from collections.abc import Iterator
from typing import Any, Protocol

from src.domain_models.transcript import Transcript


class LLMClient(Protocol):
    """Protocol for interacting with Large Language Models."""

    @abstractmethod
    def invoke(self, prompt: str | list[Any]) -> Any:
        """Invoke the LLM and get a response."""
        ...

    @abstractmethod
    def stream(self, prompt: str | list[Any]) -> Iterator[Any]:
        """Stream chunks from the LLM."""
        ...

    @abstractmethod
    def with_structured_output(self, schema: Any) -> "LLMClientStructured":
        """Return a structured output chain for the schema."""
        ...


class LLMClientStructured(Protocol):
    """Protocol for structured output invocation."""

    @abstractmethod
    def invoke(self, prompt: str | list[Any] | dict[str, Any]) -> Any:
        """Invoke and return parsed Pydantic model."""
        ...


class PromptTemplate(Protocol):
    """Protocol for formatting prompts."""

    @abstractmethod
    def format(self, **kwargs: Any) -> str | list[Any]:
        """Format the prompt template."""
        ...


class RAGInterface(Protocol):
    """Protocol for RAG data ingestion and querying."""

    @abstractmethod
    def ingest_text(self, text: str | Iterator[str], source: str) -> None:
        """Ingest text chunks into vector store."""
        ...

    @abstractmethod
    def ingest_transcript(self, transcript: Transcript) -> None:
        """Ingest transcript object into vector store."""
        ...

    @abstractmethod
    def persist_index(self) -> None:
        """Persist the index."""
        ...

    @abstractmethod
    def query(self, question: str) -> str:
        """Query the index."""
        ...


class HttpClient(Protocol):
    """Protocol for making HTTP requests."""

    @abstractmethod
    def post(
        self, url: str, headers: dict[str, str], json: dict[str, Any], timeout: float = 60.0
    ) -> Any:
        """Make a POST request and return a response object with status_code, json() and text."""
        ...
