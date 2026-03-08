from typing import Literal

from tavily import InvalidAPIKeyError, MissingAPIKeyError, TavilyClient

from src.core.config import get_settings
from src.core.constants import ERR_SEARCH_CONFIG_MISSING
from src.core.interfaces import SearchInterface


class TavilySearchAdapter(SearchInterface):
    """Adapter for Tavily Search."""

    def __init__(self, api_key: str | None = None) -> None:
        self.settings = get_settings()
        key = api_key or (
            self.settings.tavily_api_key.get_secret_value()
            if self.settings.tavily_api_key
            else None
        )
        if not key:
            raise ValueError(ERR_SEARCH_CONFIG_MISSING)

        try:
            self.client = TavilyClient(api_key=key)
        except (MissingAPIKeyError, InvalidAPIKeyError) as e:
            msg = f"Invalid Tavily configuration: {e}"
            raise ValueError(msg) from e

    def safe_search(self, query: str, include_raw_content: bool = False) -> str:
        """Execute a search query."""
        search_depth: Literal["basic", "advanced"] = "advanced"
        max_results = self.settings.search_max_results

        response = self.client.search(
            query=query,
            search_depth=search_depth,
            max_results=max_results,
            include_raw_content=include_raw_content,
        )

        results = response.get("results", [])
        if not results:
            return "No results found."

        formatted_results = []
        for r in results:
            content = r.get("raw_content") if include_raw_content else r.get("content")
            formatted_results.append(f"Title: {r.get('title')}\nContent: {content}\n")

        return "\n".join(formatted_results)
