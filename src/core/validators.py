import os
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

        if getattr(settings, "openai_api_key", None) is None:
            raise ValueError(ERR_CONFIG_MISSING_OPENAI_KEY)

        openai_val = settings.openai_api_key.get_secret_value()
        if not openai_val:
            raise ValueError(ERR_CONFIG_MISSING_OPENAI_KEY)

        if getattr(settings, "tavily_api_key", None) is None:
            msg = "Tavily API Key is missing or empty."
            raise ValueError(msg)

        tavily_val = settings.tavily_api_key.get_secret_value()
        if not tavily_val:
            msg = "Tavily API Key is missing or empty."
            raise ValueError(msg)

    @staticmethod
    def _verify_openai_key(api_key: str) -> None:
        """Verify the OpenAI API Key by making a lightweight request."""
        import urllib.request
        from urllib.error import HTTPError, URLError

        req = urllib.request.Request(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            method="GET",
        )

        try:
            with urllib.request.urlopen(req, timeout=5) as response:  # noqa: S310
                if response.status != 200:
                    msg = "OpenAI API Key is invalid or unauthorized."
                    raise ValueError(msg)
        except HTTPError as e:
            if e.code == 401:
                msg = "OpenAI API Key is invalid."
                raise ValueError(msg) from e
            # Other HTTP errors (like 429 quota exceeded) might indicate the key is structurally valid but restricted
        except URLError:
            # Network issues, can't reliably validate, let it pass to fail at runtime
            pass

    @staticmethod
    def _verify_tavily_key(api_key: str) -> None:
        """Verify the Tavily API Key by making a lightweight request."""
        import json
        import urllib.request
        from urllib.error import HTTPError, URLError

        data = json.dumps({"query": "test"}).encode("utf-8")
        req = urllib.request.Request(
            "https://api.tavily.com/search",
            data=data,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=5) as response:  # noqa: S310
                if response.status != 200:
                    msg = "Tavily API Key is invalid or unauthorized."
                    raise ValueError(msg)
        except HTTPError as e:
            if e.code in {401, 403}:
                msg = "Tavily API Key is invalid."
                raise ValueError(msg) from e
        except URLError:
            pass


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
