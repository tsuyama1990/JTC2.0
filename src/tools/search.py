import logging
from typing import Literal

from tavily import TavilyClient
from tenacity import (
    after_log,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.core.config import settings

logger = logging.getLogger(__name__)


class TavilySearch:
    """Wrapper for Tavily Search API with retry logic."""

    def __init__(self, api_key: str | None = None) -> None:
        """
        Initialize Tavily Search client.

        Args:
            api_key: Optional API key override. Defaults to config settings.

        Raises:
            ValueError: If API key is missing.
        """
        self.api_key = api_key or (
            settings.tavily_api_key.get_secret_value() if settings.tavily_api_key else None
        )
        if not self.api_key:
            msg = "Search configuration error: API key is missing. Please check your .env file."
            raise ValueError(msg)
        self.client = TavilyClient(api_key=self.api_key)

    @retry(
        retry=retry_if_exception_type(Exception),  # Retry on generic exceptions for now
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
        Perform a search and return a formatted string of results.

        Args:
            query: The search query.
            max_results: Maximum number of results to return. Defaults to config.
            search_depth: "basic" or "advanced". Defaults to config.

        Returns:
            A string containing the search results or error message.
        """
        # search_depth="advanced" is generally better for research
        response = self.client.search(
            query=query,
            max_results=max_results or settings.search_max_results,
            search_depth=search_depth or settings.search_depth,
        )

        results = response.get("results", [])
        if not results:
            return "No results found."

        # Use list comprehension for efficient string concatenation
        summary_list = [
            f"Title: {result.get('title', 'No Title')}\n"
            f"URL: {result.get('url', 'No URL')}\n"
            f"Content: {result.get('content', 'No Content')}\n"
            for result in results
        ]

        return "\n".join(summary_list)

    def safe_search(self, query: str) -> str:
        """
        Perform a search with safety wrapper (no exceptions raised).

        Args:
            query: The search query.

        Returns:
            Search results or error message.
        """
        try:
            return self.search(query)
        except Exception:
            logger.exception("Tavily search failed after retries")
            return "Search service unavailable."
