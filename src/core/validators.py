import re
from collections.abc import Iterable
from pathlib import Path

from pydantic import SecretStr


class ConfigValidators:
    """Centralized validation service for application configuration."""

    @staticmethod
    def validate_openai_key(key: SecretStr) -> None:
        """Validate OpenAI API key format."""
        val = key.get_secret_value()
        if not val or not val.strip():
            msg = "OpenAI API key cannot be empty or whitespace-only."
            raise ValueError(msg)
        if len(val) < 20:
            msg = "OpenAI API key is too short."
            raise ValueError(msg)
        if len(val) > 128:
            msg = "OpenAI API key is too long."
            raise ValueError(msg)
        if not val.startswith("sk-"):
            msg = "OpenAI API key must start with 'sk-'."
            raise ValueError(msg)

    @staticmethod
    def validate_tavily_key(key: SecretStr) -> None:
        """Validate Tavily API key format."""
        val = key.get_secret_value()
        if not val or not val.strip():
            msg = "Tavily API key cannot be empty or whitespace-only."
            raise ValueError(msg)
        if len(val) < 20:
            msg = "Tavily API key is too short."
            raise ValueError(msg)
        if len(val) > 128:
            msg = "Tavily API key is too long."
            raise ValueError(msg)
        if not val.startswith("tvly-"):
            msg = "Tavily API key must start with 'tvly-'."
            raise ValueError(msg)

    @staticmethod
    def validate_v0_key(key: SecretStr) -> None:
        val = key.get_secret_value()
        if not val or not val.strip():
            msg = "v0 API key cannot be empty or whitespace-only."
            raise ValueError(msg)
        if not (20 <= len(val) <= 128):
            msg = "v0 API key must be between 20 and 128 characters long."
            raise ValueError(msg)
        if not re.match(r"^v0-[a-zA-Z0-9_\-]+$", val):
            msg = "v0 API key must start with 'v0-' and contain only alphanumeric characters, dashes, or underscores."
            raise ValueError(msg)

    @staticmethod
    def validate_resolution(val: int) -> int:
        if val <= 0:
            msg = "Resolution must be strictly positive."
            raise ValueError(msg)
        return val

    @staticmethod
    def validate_fps(val: int) -> int:
        if val <= 0:
            msg = "FPS must be strictly positive."
            raise ValueError(msg)
        return val

    @staticmethod
    def validate_color(val: int) -> int:
        if not (0 <= val <= 15):
            msg = "Color must be between 0 and 15 (Pyxel palette)."
            raise ValueError(msg)
        return val

    @staticmethod
    def validate_dimension(val: int) -> int:
        if val <= 0:
            msg = "Dimension must be positive."
            raise ValueError(msg)
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
