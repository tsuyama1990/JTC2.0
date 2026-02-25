from collections.abc import Generator
from unittest.mock import MagicMock, patch

import httpx
import pytest
from pydantic import SecretStr

from src.core.exceptions import V0GenerationError

try:
    from src.tools.v0_client import V0Client
except ImportError:
    V0Client = None # type: ignore


class TestV0Client:
    @pytest.fixture
    def mock_settings(self) -> Generator[MagicMock, None, None]:
        with patch("src.tools.v0_client.get_settings") as mock:
            mock.return_value.v0.retry_max = 1 # Speed up tests
            mock.return_value.v0.retry_backoff = 0.0 # No wait
            yield mock.return_value

    @patch("src.tools.v0_client.pybreaker.CircuitBreaker")
    def test_generate_ui_success(self, mock_breaker: MagicMock, mock_settings: MagicMock) -> None:
        """Test successful UI generation."""
        mock_settings.v0_api_key = SecretStr("valid-key")
        mock_settings.v0_api_url = "https://api.v0.dev"

        client = V0Client()
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
    def test_generate_ui_network_error(self, mock_breaker: MagicMock, mock_settings: MagicMock) -> None:
        """Test network failure handling (Timeout/ConnectionError)."""
        mock_settings.v0_api_key = SecretStr("valid-key")
        client = V0Client()
        client.breaker.call = lambda func, *args: func(*args) # type: ignore

        with patch("src.tools.v0_client.httpx.Client") as mock_http_cls:
            mock_client_instance = mock_http_cls.return_value.__enter__.return_value
            # Simulate RequestError (base class for Timeout/Connection)
            mock_client_instance.post.side_effect = httpx.RequestError("Network Down")

            with pytest.raises(V0GenerationError) as exc:
                client.generate_ui("Test prompt")

            # Check message format from constant
            assert "V0 network error" in str(exc.value)

    def test_missing_api_key(self, mock_settings: MagicMock) -> None:
        """Test missing API key."""
        mock_settings.v0_api_key = None
        client = V0Client(api_key=None)

        with pytest.raises(V0GenerationError, match="V0 API Key missing"):
            client.generate_ui("prompt")
