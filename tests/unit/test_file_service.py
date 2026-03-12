from unittest.mock import MagicMock, patch

import pytest

from src.core.services.file_service import FileService


class TestFileService:
    """Test suite for FileService."""

    @pytest.fixture
    def file_service(self) -> FileService:
        return FileService()

    @patch("src.core.services.file_service.FileService._save_text_sync")
    def test_save_text_async_success(
        self, mock_save_sync: MagicMock, file_service: FileService
    ) -> None:
        """Verify save_text_async correctly delegates to sync method."""
        # `save_text_async` is just submitting a job to an executor, so wait for executor.
        file_service.save_text_async("content", "test.md")
        file_service._executor.shutdown(wait=True)

        # We need to test whatever type save_text_async actually passed in
        from pathlib import Path
        mock_save_sync.assert_called_once()
        args, _ = mock_save_sync.call_args
        assert args[0] == "content"
        assert isinstance(args[1], Path)
        assert args[1].name == "test.md"

    @patch("src.core.services.file_service.FileService._save_text_sync")
    def test_save_text_async_permission_error(
        self,
        mock_save_sync: MagicMock,
        file_service: FileService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Verify handling of PermissionError."""
        mock_save_sync.side_effect = PermissionError("Access denied")

        file_service.save_text_async("content", "protected.md")
        file_service._executor.shutdown(wait=True)

    @patch("src.core.services.file_service.FileService._save_text_sync")
    def test_save_text_async_os_error(
        self,
        mock_save_sync: MagicMock,
        file_service: FileService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Verify handling of generic OSError."""
        mock_save_sync.side_effect = OSError("Disk full")

        file_service.save_text_async("content", "file.md")
        file_service._executor.shutdown(wait=True)
