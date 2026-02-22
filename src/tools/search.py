import logging

from tavily import TavilyClient

from src.core.config import settings

logger = logging.getLogger(__name__)


class TavilySearch:
    """Wrapper for Tavily Search API."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or (
            settings.tavily_api_key.get_secret_value() if settings.tavily_api_key else None
        )
        if not self.api_key:
            msg = "Search configuration error: API key is missing. Please check your .env file."
            raise ValueError(msg)
        self.client = TavilyClient(api_key=self.api_key)

    def search(self, query: str, max_results: int = 5) -> str:
        """
        Perform a search and return a formatted string of results.

        Args:
            query: The search query.
            max_results: Maximum number of results to return.

        Returns:
            A string containing the search results.
        """
        try:
            # search_depth="advanced" is generally better for research
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced",
            )

            summary = []
            results = response.get("results", [])
            if not results:
                return "No results found."

            for result in results:
                title = result.get("title", "No Title")
                content = result.get("content", "No Content")
                url = result.get("url", "No URL")
                summary.append(f"Title: {title}\nURL: {url}\nContent: {content}\n")

            return "\n".join(summary)
        except Exception:
            # Log the full error securely
            logger.exception("Tavily search failed")
            return "Search service unavailable."
