from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr

from src.tools.search import TavilySearch


@patch("src.tools.search.TavilyClient")
@patch("src.tools.search.settings")
def test_tavily_search_init(mock_settings: MagicMock, mock_client_cls: MagicMock) -> None:
    mock_settings.tavily_api_key = SecretStr("test-key")
    search = TavilySearch()
    mock_client_cls.assert_called_with(api_key="test-key")
    assert search.api_key == "test-key"


@patch("src.tools.search.settings")
def test_tavily_search_missing_key(mock_settings: MagicMock) -> None:
    mock_settings.tavily_api_key = None
    with pytest.raises(ValueError, match="Search configuration error"):
        TavilySearch()


@patch("src.tools.search.TavilyClient")
@patch("src.tools.search.settings")
def test_tavily_search_success(mock_settings: MagicMock, mock_client_cls: MagicMock) -> None:
    # Setup settings with explicit values
    mock_settings.tavily_api_key = SecretStr("test-key")
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
@patch("src.tools.search.settings")
def test_tavily_search_empty(mock_settings: MagicMock, mock_client_cls: MagicMock) -> None:
    mock_settings.tavily_api_key = SecretStr("test-key")
    mock_client = mock_client_cls.return_value
    mock_client.search.return_value = {"results": []}

    search = TavilySearch()
    result = search.search("query")
    assert result == "No results found."


@patch("src.tools.search.TavilyClient")
@patch("src.tools.search.settings")
def test_tavily_search_error(mock_settings: MagicMock, mock_client_cls: MagicMock) -> None:
    mock_settings.tavily_api_key = SecretStr("test-key")
    mock_client = mock_client_cls.return_value
    mock_client.search.side_effect = Exception("Search error")

    search = TavilySearch()
    result = search.search("query")
    assert "Search service unavailable." in result
