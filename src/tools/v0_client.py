import logging
import re
import time

import httpx
import pybreaker

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
        self.settings = get_settings()
        self.api_key = api_key or (
            self.settings.v0_api_key.get_secret_value() if self.settings.v0_api_key else None
        )
        self.base_url = self.settings.v0_api_url

        # Circuit Breaker
        self.breaker = pybreaker.CircuitBreaker(
            fail_max=self.settings.circuit_breaker_fail_max,
            reset_timeout=self.settings.circuit_breaker_reset_timeout,
        )

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

        # Basic validation for API key format to prevent header injection or malformed keys
        # Assuming typical bearer token format (alphanumeric, dashes, underscores, dots)
        if not re.match(r"^[A-Za-z0-9\-\._]+$", self.api_key):
            msg = "Invalid API key format"
            logger.error(msg)
            raise V0GenerationError(msg)

        return self.breaker.call(self._generate_ui_impl, prompt)

    def _sanitize_header(self, value: str) -> str:
        """Prevent header injection by stripping newlines."""
        return value.replace("\n", "").replace("\r", "")

    def _generate_ui_impl(self, prompt: str) -> str:
        # Sanitize headers
        sanitized_api_key = self._sanitize_header(self.api_key)  # type: ignore # checked in public method

        headers = {
            "Authorization": f"Bearer {sanitized_api_key}",
            "Content-Type": "application/json",
        }

        # Structure payload for v0.dev (assuming OpenAI-compatible chat format)
        # Prompt is user content in JSON body, requests handles escaping, but strict hygiene is good.
        payload = {
            "model": "v0-preview",  # or similar model name
            "messages": [
                {
                    "role": "system",
                    "content": "You are a UI generator. Generate a React component using Tailwind CSS.",
                },
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        }

        max_retries = self.settings.v0.retry_max
        backoff_factor = self.settings.v0.retry_backoff

        try:
            with httpx.Client(timeout=60.0) as client:
                for attempt in range(max_retries + 1):
                    response = client.post(self.base_url, headers=headers, json=payload)

                    if response.status_code == 200:
                        data = response.json()
                        if "url" in data:
                            return str(data["url"])
                        msg = ERR_V0_NO_URL.format(keys=list(data.keys()))
                        logger.error(msg)
                        raise V0GenerationError(msg)

                    if response.status_code == 429:
                        if attempt < max_retries:
                            sleep_time = backoff_factor**attempt
                            logger.warning(f"Rate limited by v0.dev. Retrying in {sleep_time}s...")
                            time.sleep(sleep_time)
                            continue
                        msg = "v0.dev rate limit exceeded after retries."
                        logger.error(msg)
                        raise V0GenerationError(msg)

                    # Other non-200 errors
                    msg = ERR_V0_GENERATION_FAILED.format(status_code=response.status_code)
                    logger.error(f"v0.dev API error: {response.status_code} - {response.text}")
                    raise V0GenerationError(msg)

        except httpx.RequestError as e:
            msg = ERR_V0_NETWORK_ERROR.format(e=e)
            logger.exception(msg)
            raise V0GenerationError(msg) from e

        # Should be unreachable if logic is correct, but for safety
        msg = "Unknown error in v0 generation flow"
        raise V0GenerationError(msg)
