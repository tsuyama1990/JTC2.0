from pathlib import Path
from typing import Protocol, runtime_checkable

from langchain_openai import ChatOpenAI
from pydantic import SecretStr


@runtime_checkable
class IConfigValidator(Protocol):
    def validate_openai_key(self, v: SecretStr | None) -> SecretStr | None:
        ...

    def validate_tavily_key(self, v: SecretStr | None) -> SecretStr | None:
        ...


@runtime_checkable
class IFileRepository(Protocol):
    def scan_directory_size(self, path: str, depth_limit: int | None = None) -> int:
        """Calculate directory size."""
        ...

    def get_directory_mtime(self, path: str) -> float:
        """Get the maximum modification time for files in the directory."""
        ...

    def is_directory_empty(self, path: str) -> bool:
        """Check if directory is empty."""
        ...

    def ensure_directory(self, path: str) -> None:
        """Ensure a directory exists."""
        ...

    def file_exists(self, path: str) -> bool:
        """Check if a file exists."""
        ...




@runtime_checkable
class IFileWriter(Protocol):
    def save_text_async(self, content: str, path: str | Path) -> None:
        """Save text to a file asynchronously."""
        ...




@runtime_checkable
class IOpenAIProvider(Protocol):
    def get_llm(self, model: str | None = None) -> ChatOpenAI:
        """Retrieve the managed ChatOpenAI instance."""
        ...
