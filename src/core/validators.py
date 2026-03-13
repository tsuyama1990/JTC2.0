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
        """Validate OpenAI API Key format."""
        import re

        if v is None:
            return None
        secret = v.get_secret_value()
        # OpenAI keys can be `sk-[a-zA-Z0-9]{32,100}` or `sk-proj-[a-zA-Z0-9_-]+`
        if not re.match(r"^sk-[a-zA-Z0-9_\\-]{20,128}$", secret):
            msg = "OpenAI API Key must start with 'sk-' and be 20-128 valid characters."
            raise ValueError(msg)
        return v

    @staticmethod
    def validate_tavily_key(v: SecretStr | None) -> SecretStr | None:
        """Validate Tavily API Key format."""
        import re

        if v is None:
            return None
        secret = v.get_secret_value()
        if not re.match(r"^tvly-[a-zA-Z0-9_\\-]{20,128}$", secret):
            msg = "Tavily API Key must start with 'tvly-' and be 20-128 valid characters."
            raise ValueError(msg)
        return v
