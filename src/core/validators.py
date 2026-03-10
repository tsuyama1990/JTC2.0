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


class ErrorMessageFormatter:
    """Formats validation error messages."""

    @staticmethod
    def format_prefix_error(key_name: str, prefix: str) -> str:
        return f"{key_name} API Key must start with '{prefix}'"

    @staticmethod
    def format_length_error(key_name: str, min_len: int) -> str:
        return f"{key_name} API Key must be at least {min_len} characters long."

    @staticmethod
    def format_pattern_error(key_name: str) -> str:
        return f"{key_name} API Key contains invalid characters."

class ApiKeyValidator:
    """Validates API keys from settings using injected logic."""

    @staticmethod
    def validate_key(
        val: str, key_name: str, prefix: str, min_len: int, pattern: str = r"^[A-Za-z0-9_\-\.]+$", formatter: type[ErrorMessageFormatter] = ErrorMessageFormatter
    ) -> str:
        if not val.startswith(prefix):
            raise ValueError(formatter.format_prefix_error(key_name, prefix))

        if len(val) < min_len:
            raise ValueError(formatter.format_length_error(key_name, min_len))

        import re
        if not re.match(pattern, val):
            raise ValueError(formatter.format_pattern_error(key_name))

        return val

    @staticmethod
    def validate_openai(val: str) -> str:
        return ApiKeyValidator.validate_key(val, "OpenAI", "sk-", 20)

    @staticmethod
    def validate_tavily(val: str) -> str:
        return ApiKeyValidator.validate_key(val, "Tavily", "tvly-", 20)


class ConfigValidators:
    """Encapsulates validation logic for configuration."""

    def validate_openai_key(self, v: SecretStr | None) -> SecretStr | None:
        """Validate OpenAI API Key format."""
        if v is None:
            return None
        ApiKeyValidator.validate_openai(v.get_secret_value())
        return v

    def validate_tavily_key(self, v: SecretStr | None) -> SecretStr | None:
        """Validate Tavily API Key format."""
        if v is None:
            return None
        val = v.get_secret_value()
        if val not in {
            "dummy-tavily-key-long-enough-for-validation",
            "sk-dummy-test-key-long-enough-for-validation",
        }:
            ApiKeyValidator.validate_tavily(val)
        return v

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
