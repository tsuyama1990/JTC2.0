import logging
from typing import Any

import httpx

from src.core.config import get_settings
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
            msg = "V0_API_KEY is not configured."
            logger.error(msg)
            raise V0GenerationError(msg)

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
                    logger.error(f"v0.dev API error: {response.status_code} - {response.text}")
                    raise V0GenerationError(f"v0.dev generation failed: {response.status_code}")

                data = response.json()

                if "url" in data:
                    return str(data["url"])

                msg = f"No URL found in v0 response: {data.keys()}"
                logger.error(msg)
                raise V0GenerationError(msg)

        except httpx.RequestError as e:
            logger.exception(f"Network error calling v0.dev: {e}")
            raise V0GenerationError(f"Network error: {e}") from e
