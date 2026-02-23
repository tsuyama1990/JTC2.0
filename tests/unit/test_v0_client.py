from unittest.mock import MagicMock, patch

import pytest
from httpx import Response, RequestError

from src.core.exceptions import V0GenerationError

try:
    from src.tools.v0_client import V0Client
except ImportError:
    V0Client = None # type: ignore


class TestV0Client:
    @pytest.fixture
    def client(self) -> V0Client:
        if V0Client is None:
            pytest.skip("V0Client not implemented")
        return V0Client(api_key="test-key")

    @patch("src.tools.v0_client.httpx.Client.post")
    def test_generate_ui_success(self, mock_post: MagicMock, client: V0Client) -> None:
        """Test successful UI generation."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"url": "https://v0.dev/test-ui"}
        mock_post.return_value = mock_response

        url = client.generate_ui(prompt="A login page")

        assert url == "https://v0.dev/test-ui"
        mock_post.assert_called_once()

    @patch("src.tools.v0_client.httpx.Client.post")
    def test_generate_ui_failure(self, mock_post: MagicMock, client: V0Client) -> None:
        """Test API failure."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        with pytest.raises(V0GenerationError, match="v0.dev generation failed: 400"):
            client.generate_ui(prompt="Invalid prompt")

    def test_missing_api_key(self) -> None:
        """Test missing API key."""
        if V0Client is None:
            pytest.skip("V0Client not implemented")

        # Ensure settings don't provide a key
        with patch("src.tools.v0_client.get_settings") as mock_settings:
            mock_settings.return_value.v0_api_key = None
            client = V0Client(api_key=None)

            with pytest.raises(V0GenerationError, match="V0_API_KEY is not configured"):
                client.generate_ui("prompt")

    @patch("src.tools.v0_client.httpx.Client.post")
    def test_malformed_response(self, mock_post: MagicMock, client: V0Client) -> None:
        """Test response without URL."""
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "No URL here"}
        mock_post.return_value = mock_response

        with pytest.raises(V0GenerationError, match="No URL found in v0 response"):
            client.generate_ui("prompt")

    @patch("src.tools.v0_client.httpx.Client.post")
    def test_network_error(self, mock_post: MagicMock, client: V0Client) -> None:
        """Test network error."""
        mock_post.side_effect = RequestError("Connection failed")

        with pytest.raises(V0GenerationError, match="Network error:"):
            client.generate_ui("prompt")
