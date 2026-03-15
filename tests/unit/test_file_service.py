from unittest.mock import MagicMock, patch

import pytest

from src.core.services.file_service import FileService


class TestFileService:
    """Test suite for FileService."""

    @pytest.fixture
    def file_service(self) -> FileService:
        return FileService()

    @patch("src.core.services.file_service.FileService._validate_path")
    @patch("src.core.services.file_service.FileService._check_permissions")
    @patch("src.core.services.file_service.os.open")
    @patch("src.core.services.file_service.os.fdopen")
    @patch("src.core.services.file_service.Path")
    def test_save_text_async_success(
        self,
        mock_path: MagicMock,
        mock_fdopen: MagicMock,
        mock_os_open: MagicMock,
        mock_check_perms: MagicMock,
        mock_validate: MagicMock,
        file_service: FileService,
    ) -> None:
        mock_validate.return_value = mock_path.return_value
        mock_validate.return_value.__str__.return_value = "protected.md"
        mock_os_open.return_value = 123
        mock_file = MagicMock()
        mock_fdopen.return_value.__enter__.return_value = mock_file
        """Verify save_text_async writes content correctly using atomic os ops."""

        # Call the method
        file_service.save_text_async("content", "test.md")

        # Shutdown executor to ensure sync execution finishes
        file_service._executor.shutdown(wait=True)

        # Assertions
        mock_validate.assert_called_with("test.md")
        import os

        mock_os_open.assert_called_with(
            mock_validate.return_value, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
        )
        mock_file.write.assert_called_with("content")

    @patch("src.core.services.file_service.FileService._validate_path")
    @patch("src.core.services.file_service.Path")
    def test_save_text_async_permission_error(
        self,
        mock_path: MagicMock,
        mock_validate: MagicMock,
        file_service: FileService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Verify handling of PermissionError."""
        mock_validate.return_value = mock_path.return_value
        mock_validate.return_value.__str__.return_value = "protected.md"
        mock_validate.return_value.write_text.side_effect = PermissionError("Access denied")

        file_service.save_text_async("content", "protected.md")
        file_service._executor.shutdown(wait=True)

        assert "Permission denied writing to protected.md" in caplog.text

    @patch("src.core.services.file_service.FileService._validate_path")
    @patch("src.core.services.file_service.FileService._check_permissions")
    @patch("src.core.services.file_service.os.open")
    @patch("src.core.services.file_service.Path")
    def test_save_text_async_os_error(
        self,
        mock_path: MagicMock,
        mock_os_open: MagicMock,
        mock_check_perms: MagicMock,
        mock_validate: MagicMock,
        file_service: FileService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Verify handling of generic OSError with mock atomic op."""
        mock_validate.return_value = mock_path.return_value
        mock_validate.return_value.__str__.return_value = "file.md"
        # Since _save_text_sync sleeps on retries, we mock sleep to keep tests fast
        with patch("src.core.services.file_service.time.sleep"):
            mock_os_open.side_effect = OSError("Disk full")

            file_service.save_text_async("content", "file.md")
            file_service._executor.shutdown(wait=True)

            assert "OS error writing to file.md" in caplog.text
