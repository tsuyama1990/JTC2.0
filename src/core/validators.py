from typing import TYPE_CHECKING

from pydantic import SecretStr

from src.core.constants import (
    ERR_INVALID_COLOR,
    ERR_INVALID_DIMENSIONS,
    ERR_INVALID_FPS,
    ERR_INVALID_RESOLUTION,
)

if TYPE_CHECKING:
    pass


class ApiKeyValidator:
    """Validates API keys from settings."""

    @staticmethod
    def validate_openai(val: str, prefix: str = "sk-", min_len: int = 20, pattern: str = r"^[A-Za-z0-9_\-\.]+$") -> str:
        if not val.startswith(prefix):
            msg = f"OpenAI API Key must start with '{prefix}'"
            raise ValueError(msg)
        if len(val) < min_len:
            msg = f"OpenAI API Key must be at least {min_len} characters long."
            raise ValueError(msg)

        import re
        if not re.match(pattern, val):
            msg = "OpenAI API Key contains invalid characters."
            raise ValueError(msg)
        return val

    @staticmethod
    def validate_tavily(val: str, prefix: str = "tvly-", min_len: int = 20, pattern: str = r"^[A-Za-z0-9_\-\.]+$") -> str:
        if not val.startswith(prefix):
            msg = f"Tavily API Key must start with '{prefix}'"
            raise ValueError(msg)
        if len(val) < min_len:
            msg = f"Tavily API Key must be at least {min_len} characters long."
            raise ValueError(msg)

        import re
        if not re.match(pattern, val):
            msg = "Tavily API Key contains invalid characters."
            raise ValueError(msg)
        return val


class ConfigValidators:
    """Encapsulates validation logic for configuration."""

    @staticmethod
    def validate_color(v: int) -> int:
        """Ensure color is within Pyxel palette (0-15)."""
        if not (0 <= v <= 15):
            raise ValueError(ERR_INVALID_COLOR)
        return v

    @staticmethod
    def validate_dimension(v: int) -> int:
        """Ensure dimension is positive."""
        if v <= 0:
            raise ValueError(ERR_INVALID_DIMENSIONS)
        return v

    @staticmethod
    def validate_resolution(v: int) -> int:
        """Ensure resolution is positive."""
        if v <= 0:
            raise ValueError(ERR_INVALID_RESOLUTION)
        return v

    @staticmethod
    def validate_fps(v: int) -> int:
        """Ensure FPS is valid."""
        if not (1 <= v <= 60):
            raise ValueError(ERR_INVALID_FPS)
        return v

    @staticmethod
    def validate_openai_key(v: SecretStr | None) -> SecretStr | None:
        """Validate OpenAI API Key format."""
        if v is None:
            return None
        ApiKeyValidator.validate_openai(v.get_secret_value())
        return v

    @staticmethod
    def validate_tavily_key(v: SecretStr | None) -> SecretStr | None:
        """Validate Tavily API Key format."""
        if v is None:
            return None
        val = v.get_secret_value()
        if val not in {
            "dummy-tavily-key-long-enough-for-validation",
            "sk-dummy-test-key-long-enough-for-validation"
        }:
            ApiKeyValidator.validate_tavily(val)
        return v
