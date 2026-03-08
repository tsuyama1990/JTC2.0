import os
import re
from typing import TYPE_CHECKING

from pydantic import SecretStr

from src.core.constants import (
    ERR_INVALID_COLOR,
    ERR_INVALID_DIMENSIONS,
    ERR_INVALID_FPS,
    ERR_INVALID_RESOLUTION,
)

if TYPE_CHECKING:
    from src.core.config import Settings


class ApiKeyValidator:
    """Validates API keys from settings."""

    @staticmethod
    def validate(settings: "Settings") -> None:
        """Validate API keys are present and have correct format."""
        from src.core.constants import ERR_CONFIG_MISSING_OPENAI_KEY

        # Enforce that keys come from environment
        if not os.getenv("OPENAI_API_KEY") and not settings.openai_api_key:
            raise ValueError(ERR_CONFIG_MISSING_OPENAI_KEY)

        key_pattern = re.compile(r"^[A-Za-z0-9_\-\.]+$")

        if not settings.openai_api_key or not settings.openai_api_key.get_secret_value():
            raise ValueError(ERR_CONFIG_MISSING_OPENAI_KEY)
        if not key_pattern.match(settings.openai_api_key.get_secret_value()):
            msg = "OpenAI API Key format is invalid. Keys must be strictly formatted."
            raise ValueError(msg)

        if not settings.tavily_api_key or not settings.tavily_api_key.get_secret_value():
            msg = "Tavily API Key is missing or empty."
            raise ValueError(msg)
        if not key_pattern.match(settings.tavily_api_key.get_secret_value()):
            msg = "Tavily API Key format is invalid."
            raise ValueError(msg)



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
        secret = v.get_secret_value()
        if not secret.startswith("sk-"):
            msg = "OpenAI API Key must start with 'sk-'."
            raise ValueError(msg)
        if len(secret) < 20:
            msg = "OpenAI API Key is too short."
            raise ValueError(msg)
        return v

    @staticmethod
    def validate_tavily_key(v: SecretStr | None) -> SecretStr | None:
        """Validate Tavily API Key format."""
        if v is None:
            return None
        secret = v.get_secret_value()
        if not secret.startswith("tvly-"):
            msg = "Tavily API Key must start with 'tvly-'."
            raise ValueError(msg)
        if len(secret) < 20:
            msg = "Tavily API Key is too short."
            raise ValueError(msg)
        return v
