import re
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr

from src.core.constants import ERR_V0_GENERATION_FAILED
from src.core.exceptions import V0GenerationError

try:
    from src.tools.v0_client import V0Client
except ImportError:
    V0Client = None # type: ignore


class TestV0Client:
    @pytest.fixture
    def mock_settings(self) -> Generator[MagicMock, None, None]:
        with patch("src.tools.v0_client.get_settings") as mock:
            yield mock.return_value

    @patch("src.tools.v0_client.pybreaker.CircuitBreaker")
    def test_generate_ui_success(self, mock_breaker: MagicMock, mock_settings: MagicMock) -> None:
        """Test successful UI generation."""
        mock_settings.v0_api_key = SecretStr("valid-key")
        mock_settings.v0_api_url = "https://api.v0.dev"
        mock_settings.v0.retry_max = 3
        mock_settings.v0.retry_backoff = 0.1 # Fast retry for test

        client = V0Client()
        # Mock breaker call to execute the function directly (simulate passthrough)
        client.breaker.call = lambda func, *args: func(*args) # type: ignore

        with patch("src.tools.v0_client.httpx.Client") as mock_http_cls:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"url": "https://v0.dev/test-ui"}

            mock_client_instance = mock_http_cls.return_value.__enter__.return_value
            mock_client_instance.post.return_value = mock_response

            url = client.generate_ui("Test prompt")
            assert url == "https://v0.dev/test-ui"

    @patch("src.tools.v0_client.pybreaker.CircuitBreaker")
    def test_generate_ui_api_error(self, mock_breaker: MagicMock, mock_settings: MagicMock) -> None:
        """Test API error handling."""
        mock_settings.v0_api_key = SecretStr("valid-key")
        mock_settings.v0.retry_max = 3
        client = V0Client()
        client.breaker.call = lambda func, *args: func(*args) # type: ignore

        with patch("src.tools.v0_client.httpx.Client") as mock_http_cls:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Server Error"

            mock_client_instance = mock_http_cls.return_value.__enter__.return_value
            mock_client_instance.post.return_value = mock_response

            with pytest.raises(V0GenerationError, match=re.escape(ERR_V0_GENERATION_FAILED.format(status_code=500))):
                client.generate_ui("Test prompt")

    def test_missing_api_key(self, mock_settings: MagicMock) -> None:
        """Test missing API key."""
        mock_settings.v0_api_key = None
        client = V0Client(api_key=None)

        # Updated error message constant in Cycle 06
        with pytest.raises(V0GenerationError, match="V0 API Key missing"):
            client.generate_ui("prompt")
