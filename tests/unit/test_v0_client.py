from collections.abc import Generator
from unittest.mock import MagicMock, patch

import httpx
import pytest
from pydantic import SecretStr

from src.core.exceptions import V0GenerationError

try:
    from src.tools.v0_client import V0Client
except ImportError:
    V0Client = None  # type: ignore


class TestV0Client:
    @pytest.fixture
    def mock_settings(self) -> Generator[MagicMock, None, None]:
        with patch("src.tools.v0_client.get_settings") as mock:
            mock.return_value.v0.retry_max = 1  # Speed up tests
            mock.return_value.v0.retry_backoff = 0.0  # No wait
            yield mock.return_value

    @patch("src.tools.v0_client.pybreaker.CircuitBreaker")
    def test_generate_ui_success(self, mock_breaker: MagicMock, mock_settings: MagicMock) -> None:
        """Test successful UI generation."""
        mock_settings.v0_api_key = SecretStr("valid-v0-dev-key-1234")
        mock_settings.v0_api_url = "https://api.v0.dev"

        client = V0Client()
        client.breaker.call = lambda func, *args: func(*args)  # type: ignore

        with patch("src.tools.v0_client.httpx.Client") as mock_http_cls:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"url": "https://v0.dev/test-ui"}

            mock_client_instance = mock_http_cls.return_value.__enter__.return_value
            mock_client_instance.post.return_value = mock_response

            url = client.generate_ui("Test prompt")
            assert url == "https://v0.dev/test-ui"

    @patch("src.tools.v0_client.pybreaker.CircuitBreaker")
    def test_generate_ui_network_error(
        self, mock_breaker: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test network failure handling (Timeout/ConnectionError)."""
        mock_settings.v0_api_key = SecretStr("valid-v0-dev-key-1234")
        client = V0Client()
        client.breaker.call = lambda func, *args: func(*args)  # type: ignore

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
        client = V0Client(api_key="")

        with pytest.raises(V0GenerationError, match="V0 API Key missing"):
            client.generate_ui("prompt")

    @patch("src.tools.v0_client.pybreaker.CircuitBreaker")
    def test_invalid_api_key_format(
        self, mock_breaker: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test invalid API key format."""
        mock_settings.v0_api_key = SecretStr("valid-v0-dev-key-1234")
        client = V0Client()
        client.api_key = "invalid key"

        with pytest.raises(V0GenerationError, match="Invalid API key format"):
            client.generate_ui("prompt")

    @patch("src.tools.v0_client.pybreaker.CircuitBreaker")
    def test_header_sanitization(self, mock_breaker: MagicMock, mock_settings: MagicMock) -> None:
        """Test that _sanitize_header works directly."""
        client = V0Client(api_key="valid-key-format-123")
        sanitized = client._sanitize_header("valid-key-format-123\r\n")
        assert sanitized == "valid-key-format-123"

    @patch("src.tools.v0_client.pybreaker.CircuitBreaker")
    def test_generate_ui_no_url_in_response(
        self, mock_breaker: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test when API returns 200 but lacks url field."""
        mock_settings.v0_api_key = SecretStr("valid-v0-dev-key-1234")
        mock_settings.v0_api_key = SecretStr("valid-v0-dev-key-1234")
        mock_settings.v0_api_key = SecretStr("valid-v0-dev-key-1234")
        mock_settings.v0_api_key = SecretStr("valid-v0-dev-key-1234")
        mock_settings.v0_api_key = SecretStr("valid-v0-dev-key-1234")
        mock_settings.v0_api_key = SecretStr("valid-v0-dev-key-1234")
        mock_settings.v0_api_url = "https://api.v0.dev"

        client = V0Client()
        client.breaker.call = lambda func, *args: func(*args)  # type: ignore

        with patch("src.tools.v0_client.httpx.Client") as mock_http_cls:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"other_field": "data"}

            mock_client_instance = mock_http_cls.return_value.__enter__.return_value
            mock_client_instance.post.return_value = mock_response

            with pytest.raises(V0GenerationError, match="No URL returned from V0."):
                client.generate_ui("Test prompt")

    @patch("src.tools.v0_client.pybreaker.CircuitBreaker")
    def test_generate_ui_429_retry_success(
        self, mock_breaker: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test successful retry after 429."""
        mock_settings.v0_api_key = SecretStr("valid-v0-dev-key-1234")
        mock_settings.v0_api_url = "https://api.v0.dev"
        mock_settings.v0.retry_max = 1
        mock_settings.v0.retry_backoff = 0.0

        client = V0Client()
        client.breaker.call = lambda func, *args: func(*args)  # type: ignore

        with patch("src.tools.v0_client.httpx.Client") as mock_http_cls:
            mock_response_429 = MagicMock()
            mock_response_429.status_code = 429

            mock_response_200 = MagicMock()
            mock_response_200.status_code = 200
            mock_response_200.json.return_value = {"url": "https://v0.dev/test-ui"}

            mock_client_instance = mock_http_cls.return_value.__enter__.return_value
            # First call returns 429, second call returns 200
            mock_client_instance.post.side_effect = [mock_response_429, mock_response_200]

            with patch("time.sleep") as mock_sleep:
                url = client.generate_ui("Test prompt")
                assert url == "https://v0.dev/test-ui"
                mock_sleep.assert_called_once_with(1.0)  # 0.0 ** 0 = 1.0

    @patch("src.tools.v0_client.pybreaker.CircuitBreaker")
    def test_generate_ui_429_retry_exhausted(
        self, mock_breaker: MagicMock, mock_settings: MagicMock
    ) -> None:
        """Test exhaustion of retries on 429."""
        mock_settings.v0_api_key = SecretStr("valid-v0-dev-key-1234")
        mock_settings.v0_api_url = "https://api.v0.dev"
        mock_settings.v0.retry_max = 1
        mock_settings.v0.retry_backoff = 0.0

        client = V0Client()
        client.breaker.call = lambda func, *args: func(*args)  # type: ignore

        with patch("src.tools.v0_client.httpx.Client") as mock_http_cls:
            mock_response_429 = MagicMock()
            mock_response_429.status_code = 429

            mock_client_instance = mock_http_cls.return_value.__enter__.return_value
            # Always return 429
            mock_client_instance.post.return_value = mock_response_429

            with (
                patch("time.sleep"),
                pytest.raises(V0GenerationError, match="v0.dev rate limit exceeded after retries"),
            ):
                client.generate_ui("Test prompt")

    @patch("src.tools.v0_client.pybreaker.CircuitBreaker")
    def test_generate_ui_500_error(self, mock_breaker: MagicMock, mock_settings: MagicMock) -> None:
        """Test API returning a 500 error."""
        mock_settings.v0_api_key = SecretStr("valid-v0-dev-key-1234")
        mock_settings.v0_api_url = "https://api.v0.dev"

        client = V0Client()
        client.breaker.call = lambda func, *args: func(*args)  # type: ignore

        with patch("src.tools.v0_client.httpx.Client") as mock_http_cls:
            mock_response_500 = MagicMock()
            mock_response_500.status_code = 500
            mock_response_500.text = "Internal Server Error"

            mock_client_instance = mock_http_cls.return_value.__enter__.return_value
            mock_client_instance.post.return_value = mock_response_500

            with pytest.raises(V0GenerationError, match="V0 generation failed."):
                client.generate_ui("Test prompt")
