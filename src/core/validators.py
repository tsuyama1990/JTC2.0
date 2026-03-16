import re
from collections.abc import Iterable
from pathlib import Path

from pydantic import SecretStr

from src.core.exceptions import ConfigurationError


class ConfigValidators:
    """Centralized validation service for application configuration."""

    @staticmethod
    def validate_openai_key(key: SecretStr) -> None:
        """Validate OpenAI API key format."""
        val = key.get_secret_value()
        if not val or not val.strip():
            raise ValueError("OpenAI API key cannot be empty or whitespace-only.")
        if len(val) < 20:
            raise ValueError("OpenAI API key is too short.")
        if len(val) > 128:
            raise ValueError("OpenAI API key is too long.")
        if not val.startswith("sk-"):
            raise ValueError("OpenAI API key must start with 'sk-'.")

    @staticmethod
    def validate_tavily_key(key: SecretStr) -> None:
        """Validate Tavily API key format."""
        val = key.get_secret_value()
        if not val or not val.strip():
            raise ValueError("Tavily API key cannot be empty or whitespace-only.")
        if len(val) < 20:
            raise ValueError("Tavily API key is too short.")
        if len(val) > 128:
            raise ValueError("Tavily API key is too long.")
        if not val.startswith("tvly-"):
            raise ValueError("Tavily API key must start with 'tvly-'.")

    @staticmethod
    def validate_v0_key(key: SecretStr) -> None:
        import re
        val = key.get_secret_value()
        if not val or not val.strip():
            raise ValueError("v0 API key cannot be empty or whitespace-only.")
        if not (20 <= len(val) <= 128):
            raise ValueError("v0 API key must be between 20 and 128 characters long.")
        if not re.match(r"^v0-[a-zA-Z0-9_\-]+$", val):
            raise ValueError("v0 API key must start with 'v0-' and contain only alphanumeric characters, dashes, or underscores.")

    @staticmethod
    def validate_resolution(val: int) -> int:
        if val <= 0:
            raise ValueError("Resolution must be strictly positive.")
        return val

    @staticmethod
    def validate_fps(val: int) -> int:
        if val <= 0:
            raise ValueError("FPS must be strictly positive.")
        return val

    @staticmethod
    def validate_color(val: int) -> int:
        if not (0 <= val <= 15):
            raise ValueError("Color must be between 0 and 15 (Pyxel palette).")
        return val

    @staticmethod
    def validate_dimension(val: int) -> int:
        if val <= 0:
            raise ValueError("Dimension must be positive.")
        return val

    @staticmethod
    def is_safe_path(base_dir: str | Path, target_path: str | Path) -> bool:
        """
        Validates if a target path is safely contained within a base directory,
        preventing directory traversal attacks (LFI).
        """
        try:
            base_dir_resolved = Path(base_dir).resolve(strict=True)
            target_path_resolved = Path(target_path).resolve()

            # Check for null bytes to prevent poisoning
            if '\x00' in str(target_path):
                return False

            # Explicit prefix check
            return str(target_path_resolved).startswith(str(base_dir_resolved))
        except RuntimeError:
            # Strict resolving failed meaning base_dir might not exist
            return False
        except Exception:
            return False

    @staticmethod
    def validate_allowed_directories(target_path: str | Path, allowed_paths: Iterable[str | Path]) -> bool:
        """
        Validates if a target path is safely contained within ANY of the allowed directories.
        """
        for allowed_dir in allowed_paths:
            if ConfigValidators.is_safe_path(allowed_dir, target_path):
                return True
        return False
