import logging
from typing import Literal

from tavily import InvalidAPIKeyError, MissingAPIKeyError, TavilyClient
from tenacity import (
    after_log,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    retry_unless_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.core.config import get_settings
from src.core.constants import ERR_SEARCH_CONFIG_MISSING, ERR_SEARCH_FAILED

logger = logging.getLogger(__name__)


class TavilySearch:
    """Wrapper for Tavily Search API with retry logic."""

    def __init__(self, api_key: str | None = None) -> None:
        """
        Initialize Tavily Search client.

        Args:
            api_key: Optional API key override.
        """
        settings = get_settings()

        # Prioritize explicit key, then config
        if api_key:
            self.api_key = api_key
        elif settings.tavily_api_key:
            self.api_key = settings.tavily_api_key.get_secret_value()
        else:
            raise ValueError(ERR_SEARCH_CONFIG_MISSING)

        self.client = TavilyClient(api_key=self.api_key)

    @retry(
        retry=retry_if_exception_type(Exception)
        & retry_unless_exception_type((MissingAPIKeyError, InvalidAPIKeyError, ValueError)),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
    )
    def search(
        self,
        query: str,
        max_results: int | None = None,
        search_depth: Literal["basic", "advanced"] | None = None,
    ) -> str:
        """
        Execute a search query.

        Note: While we could return an iterator of results, the downstream LLM
        expects a string block. We optimize by building the string efficiently,
        but ultimately we must return a single string for the prompt.
        """
        settings = get_settings()
        depth: Literal["basic", "advanced"] = search_depth or settings.search_depth  # type: ignore[assignment]

        response = self.client.search(
            query=query,
            max_results=max_results or settings.search_max_results,
            search_depth=depth,
        )

        results = response.get("results", [])
        if not results:
            return "No results found."

        # Use generator expression within join for memory efficiency during string construction
        return "\n".join(
            f"Title: {result.get('title', 'No Title')}\n"
            f"URL: {result.get('url', 'No URL')}\n"
            f"Content: {result.get('content', 'No Content')}\n"
            for result in results
        )

    def safe_search(self, query: str) -> str:
        """Execute a search safely, catching exceptions."""
        try:
            return self.search(query)
        except (MissingAPIKeyError, InvalidAPIKeyError, ValueError):
            logger.exception("Tavily search failed: Invalid Configuration/Auth")
            return ERR_SEARCH_FAILED
        except Exception:
            logger.exception("Tavily search failed after retries")
            return ERR_SEARCH_FAILED
