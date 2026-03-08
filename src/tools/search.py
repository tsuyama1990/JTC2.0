import logging

from src.adapters.search_adapter import TavilySearchAdapter
from src.core.interfaces import SearchInterface

logger = logging.getLogger(__name__)


class TavilySearch(SearchInterface):
    """
    Wrapper for Tavily Search API using adapter.
    """

    def __init__(self, api_key: str | None = None) -> None:
        self.adapter = TavilySearchAdapter(api_key=api_key)

    def safe_search(self, query: str, include_raw_content: bool = False) -> str:
        """Execute a search safely, catching exceptions."""
        try:
            return self.adapter.safe_search(query, include_raw_content)
        except Exception:
            logger.exception("Search failed")
            from src.core.constants import ERR_SEARCH_FAILED

            return ERR_SEARCH_FAILED
