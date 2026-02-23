from unittest.mock import MagicMock, patch

import pytest

from src.data.rag import RAG


def test_rag_init_missing_api_key() -> None:
    """Test RAG initialization failure when API key is missing."""
    # We can't easily unset the key if it's already set in the singleton
    # So we patch the settings object on the RAG instance or during init

    with patch("src.data.rag.get_settings") as mock_settings_getter:
        mock_settings = MagicMock()
        mock_settings.openai_api_key = None
        # Mock error message
        mock_settings.errors.config_missing_openai = "Missing API Key"
        mock_settings_getter.return_value = mock_settings

        with pytest.raises(ValueError, match="Missing API Key"):
            RAG(persist_dir="./test")

def test_rag_init_invalid_path() -> None:
    """Test RAG initialization failure when path is unsafe."""
    with pytest.raises(ValueError, match="Path traversal"):
        RAG(persist_dir="../unsafe")
