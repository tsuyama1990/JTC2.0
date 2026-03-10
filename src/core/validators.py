import re

from pydantic import SecretStr

from src.core.constants import (
    ERR_INVALID_COLOR,
    ERR_INVALID_DIMENSIONS,
    ERR_INVALID_FPS,
    ERR_INVALID_RESOLUTION,
)


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
        """Validate OpenAI API Key format with a comprehensive regex pattern."""
        if v is None:
            return None
        secret = v.get_secret_value()

        # OpenAI keys are typically 'sk-' followed by 48+ alphanumeric characters
        # Sometimes 'sk-proj-' etc. The exact length varies, but generally > 32 chars.
        pattern = re.compile(r"^sk-[a-zA-Z0-9_\-]{32,}$")
        if not pattern.match(secret):
            msg = r"OpenAI API Key format is invalid. Must match pattern '^sk-[a-zA-Z0-9_\-]{32,}$'."
            raise ValueError(msg)
        return v

    @staticmethod
    def validate_tavily_key(v: SecretStr | None) -> SecretStr | None:
        """Validate Tavily API Key format with a comprehensive regex pattern."""
        if v is None:
            return None
        secret = v.get_secret_value()

        # Tavily keys typically start with tvly- and are followed by alphanumeric string.
        pattern = re.compile(r"^tvly-[a-zA-Z0-9]{20,}$")
        if not pattern.match(secret):
            msg = "Tavily API Key format is invalid. Must match pattern '^tvly-[a-zA-Z0-9]{20,}$'."
            raise ValueError(msg)
        return v

    @staticmethod
    def validate_v0_key(v: SecretStr | None) -> SecretStr | None:
        """Validate V0.dev API Key format with a comprehensive regex pattern."""
        if v is None:
            return None
        secret = v.get_secret_value()

        # V0 keys typically start with v0- or similar prefix based on context.
        pattern = re.compile(r"^v0-[a-zA-Z0-9_\-]{20,}$")
        if not pattern.match(secret):
            msg = r"V0 API Key format is invalid. Must match pattern '^v0-[a-zA-Z0-9_\-]{20,}$'."
            raise ValueError(msg)
        return v
