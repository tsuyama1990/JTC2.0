import logging
from typing import Any

import httpx

from src.core.config import get_settings
from src.core.constants import (
    ERR_V0_API_KEY_MISSING,
    ERR_V0_GENERATION_FAILED,
    ERR_V0_NETWORK_ERROR,
    ERR_V0_NO_URL,
)
from src.core.exceptions import V0GenerationError

logger = logging.getLogger(__name__)


class V0Client:
    """
    Client for interacting with the v0.dev API to generate UIs.
    """

    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or (
            settings.v0_api_key.get_secret_value() if settings.v0_api_key else None
        )
        self.base_url = settings.v0_api_url

    def generate_ui(self, prompt: str) -> str:
        """
        Generate a UI based on the prompt.

        Args:
            prompt: The description of the UI to generate.

        Returns:
            The URL of the generated UI.

        Raises:
            V0GenerationError: If the API call fails or configuration is missing.
        """
        if not self.api_key:
            logger.error(ERR_V0_API_KEY_MISSING)
            raise V0GenerationError(ERR_V0_API_KEY_MISSING)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Structure payload for v0.dev (assuming OpenAI-compatible chat format)
        payload = {
            "model": "v0-preview", # or similar model name
            "messages": [
                {
                    "role": "system",
                    "content": "You are a UI generator. Generate a React component using Tailwind CSS."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False
        }

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(self.base_url, headers=headers, json=payload)

                if response.status_code != 200:
                    msg = ERR_V0_GENERATION_FAILED.format(status_code=response.status_code)
                    logger.error(f"v0.dev API error: {response.status_code} - {response.text}")
                    raise V0GenerationError(msg)

                data = response.json()

                if "url" in data:
                    return str(data["url"])

                msg = ERR_V0_NO_URL.format(keys=list(data.keys()))
                logger.error(msg)
                raise V0GenerationError(msg)

        except httpx.RequestError as e:
            msg = ERR_V0_NETWORK_ERROR.format(e=e)
            logger.exception(msg)
            raise V0GenerationError(msg) from e
