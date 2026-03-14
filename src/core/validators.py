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

        from src.core.config import ErrorMessages

        if v is None:
            return None
        secret = v.get_secret_value()
        errors = ErrorMessages()
        name = "OpenAI API Key"
        if not secret or not secret.strip():
            msg = errors.api_key_empty.format(key_name=name)
            raise ValueError(msg)
        if len(secret) < 23:
            msg = errors.api_key_too_short.format(key_name=name)
            raise ValueError(msg)
        if len(secret) > 131:
            msg = errors.api_key_too_long.format(key_name=name)
            raise ValueError(msg)
        if not secret.startswith("sk-"):
            msg = errors.api_key_invalid_prefix.format(key_name=name, prefix="sk-")
            raise ValueError(msg)
        # OpenAI keys can be `sk-[a-zA-Z0-9]{32,100}` or `sk-proj-[a-zA-Z0-9_-]+`
        if not re.match(r"^sk-[a-zA-Z0-9_\-]{20,128}$", secret):
            msg = errors.api_key_invalid_chars.format(key_name=name)
            raise ValueError(msg)
        return v

    @staticmethod
    def validate_tavily_key(v: SecretStr | None) -> SecretStr | None:
        """Validate Tavily API Key format."""
        import re

        from src.core.config import ErrorMessages

        if v is None:
            return None
        secret = v.get_secret_value()
        errors = ErrorMessages()
        name = "Tavily API Key"
        if not secret or not secret.strip():
            msg = errors.api_key_empty.format(key_name=name)
            raise ValueError(msg)
        if len(secret) < 25:
            msg = errors.api_key_too_short.format(key_name=name)
            raise ValueError(msg)
        if len(secret) > 133:
            msg = errors.api_key_too_long.format(key_name=name)
            raise ValueError(msg)
        if not secret.startswith("tvly-"):
            msg = errors.api_key_invalid_prefix.format(key_name=name, prefix="tvly-")
            raise ValueError(msg)
        if not re.match(r"^tvly-[a-zA-Z0-9_\-]{20,128}$", secret):
            msg = errors.api_key_invalid_chars.format(key_name=name)
            raise ValueError(msg)
        return v

    @staticmethod
    def validate_v0_api_key(v: SecretStr | None) -> SecretStr | None:
        """Validate the format of the V0 API Key."""
        import re

        from src.core.config import ErrorMessages

        if v is None:
            return None
        secret = v.get_secret_value()
        errors = ErrorMessages()
        name = "V0 API Key"
        if not secret or not secret.strip():
            msg = errors.api_key_empty.format(key_name=name)
            raise ValueError(msg)
        if len(secret) < 23:
            msg = errors.api_key_too_short.format(key_name=name)
            raise ValueError(msg)
        if len(secret) > 131:
            msg = errors.api_key_too_long.format(key_name=name)
            raise ValueError(msg)
        if not secret.startswith("v0_"):
            msg = errors.api_key_invalid_prefix.format(key_name=name, prefix="v0_")
            raise ValueError(msg)
        if not re.match(r"^v0_[A-Za-z0-9_\-]{20,128}$", secret):
            msg = errors.api_key_invalid_chars.format(key_name=name)
            raise ValueError(msg)
        return v
