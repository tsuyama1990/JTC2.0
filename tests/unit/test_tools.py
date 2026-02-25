from unittest.mock import MagicMock, patch

import pytest
from tenacity import RetryError

from src.tools.search import TavilySearch


@patch("src.tools.search.TavilyClient")
@patch("src.tools.search.get_settings")
def test_tavily_search_success(mock_get_settings: MagicMock, mock_client_cls: MagicMock) -> None:
    # Setup settings with explicit values
    mock_settings = mock_get_settings.return_value
    mock_settings.tavily_api_key.get_secret_value.return_value = "test-key"
    mock_settings.search_max_results = 5
    mock_settings.search_depth = "advanced"

    mock_client = mock_client_cls.return_value
    mock_client.search.return_value = {
        "results": [
            {"title": "Title 1", "content": "Content 1", "url": "http://example.com/1"},
            {"title": "Title 2", "content": "Content 2", "url": "http://example.com/2"},
        ]
    }

    search = TavilySearch()
    result = search.search("query")

    assert "Title 1" in result
    assert "Content 1" in result
    assert "http://example.com/1" in result

    # We assert that it called it with the mock objects from settings, or the values if resolved
    # Since we set the mock properties above, they should match
    mock_client.search.assert_called_with(query="query", max_results=5, search_depth="advanced")


@patch("src.tools.search.TavilyClient")
@patch("src.tools.search.get_settings")
def test_tavily_search_error_with_retry(
    mock_get_settings: MagicMock, mock_client_cls: MagicMock
) -> None:
    mock_settings = mock_get_settings.return_value
    mock_settings.tavily_api_key.get_secret_value.return_value = "test-key"
    mock_client = mock_client_cls.return_value
    # Simulate repeated failure
    mock_client.search.side_effect = Exception("Search error")

    search = TavilySearch()

    # We expect RetryError after retries are exhausted (tenacity behavior)
    # The search() method raises RetryError if retries fail.
    # The safe_search() method handles it.
    with pytest.raises(RetryError):
        search.search("query")

    # Verify multiple attempts
    assert mock_client.search.call_count >= 3


@patch("src.tools.search.TavilyClient")
@patch("src.tools.search.get_settings")
def test_tavily_safe_search_error(mock_get_settings: MagicMock, mock_client_cls: MagicMock) -> None:
    mock_settings = mock_get_settings.return_value
    mock_settings.tavily_api_key.get_secret_value.return_value = "test-key"
    mock_client = mock_client_cls.return_value
    # Simulate repeated failure
    mock_client.search.side_effect = Exception("Search error")

    search = TavilySearch()

    # safe_search should catch the RetryError (or underlying) and return error message
    # Updated to match constant ERR_SEARCH_FAILED in Cycle 06
    result = search.safe_search("query")
    assert "Search operation failed" in result
