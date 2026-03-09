from pathlib import Path
from typing import Any, Protocol, runtime_checkable

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





@runtime_checkable
class IAgent(Protocol):
    def run(self, state: "Any") -> dict[str, Any]:
        """Execute agent logic returning a state update."""
        ...

@runtime_checkable
class IRemasteredAgent(Protocol):
    def generate_persona(self, state: "Any") -> dict[str, Any]:
        ...
    def generate_alternative_analysis(self, state: "Any") -> dict[str, Any]:
        ...
    def generate_vpc(self, state: "Any") -> dict[str, Any]:
        ...
    def generate_mental_model_and_journey(self, state: "Any") -> dict[str, Any]:
        ...
    def generate_sitemap_and_wireframe(self, state: "Any") -> dict[str, Any]:
        ...

@runtime_checkable
class IOutputGenerationAgent(Protocol):
    def generate_agent_prompt_spec(self, state: "Any") -> dict[str, Any]:
        ...
    def generate_experiment_plan(self, state: "Any") -> dict[str, Any]:
        ...
