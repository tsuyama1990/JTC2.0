from unittest.mock import MagicMock, patch

import pytest

from src.core.services.file_service import FileService


class TestFileService:
    """Test suite for FileService."""

    @pytest.fixture
    def file_service(self) -> FileService:
        return FileService()

    @patch("src.core.services.file_service.FileService._validate_path")
    def test_save_text_async_success(
        self, mock_validate: MagicMock, file_service: FileService
    ) -> None:
        """Verify save_text_async writes content correctly."""
        with (
            patch("tempfile.mkstemp") as mock_mkstemp,
            patch("os.fdopen") as mock_fdopen,
            patch("os.replace") as mock_replace,
        ):
            mock_path = MagicMock()
            mock_path.__str__.return_value = "protected.md"  # type: ignore[attr-defined]
            mock_validate.return_value = mock_path
            mock_path.__str__.return_value = "protected.md"  # type: ignore[attr-defined]
            mock_validate.return_value = mock_path
            mock_path.parent = MagicMock()
            mock_mkstemp.return_value = (1, "temp.md")

            mock_file = MagicMock()
            mock_fdopen.return_value.__enter__.return_value = mock_file

            # Call the method
            file_service.save_text_async("content", "test.md")

            # Shutdown executor to ensure sync execution finishes
            file_service._executor.shutdown(wait=True)

            # Assertions
            mock_validate.assert_called_with("test.md")
            mock_file.write.assert_called_with("content")
            # In the updated implementation, Path('temp.md').replace(path) is used.
            # We must assert against Path objects.
            mock_replace.assert_called_once()

    @patch("src.core.services.file_service.FileService._validate_path")
    def test_save_text_async_permission_error(
        self,
        mock_validate: MagicMock,
        file_service: FileService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Verify handling of PermissionError."""
        with patch("tempfile.mkstemp") as mock_mkstemp:
            mock_path = MagicMock()
            mock_path.__str__.return_value = "protected.md"  # type: ignore[attr-defined]
            mock_validate.return_value = mock_path
            mock_mkstemp.side_effect = PermissionError("Access denied")

            file_service.save_text_async("content", "protected.md")
            file_service._executor.shutdown(wait=True)

            assert "Permission denied" in caplog.text or "Fatal error encountered" in caplog.text

    @patch("src.core.services.file_service.FileService._validate_path")
    def test_save_text_async_large_file(
        self, mock_validate: MagicMock, file_service: FileService
    ) -> None:
        """Verify handling of large string payloads."""
        with (
            patch("tempfile.mkstemp") as mock_mkstemp,
            patch("os.fdopen") as mock_fdopen,
            patch("os.replace") as mock_replace,
        ):
            mock_path = MagicMock()
            mock_path.__str__.return_value = "large.md" # type: ignore[attr-defined]
            mock_validate.return_value = mock_path
            mock_path.parent = MagicMock()
            mock_mkstemp.return_value = (1, "temp.md")
            mock_file = MagicMock()
            mock_fdopen.return_value.__enter__.return_value = mock_file

            large_content = "A" * (1024 * 1024 * 10)  # 10 MB string
            file_service.save_text_async(large_content, "large.md")
            file_service._executor.shutdown(wait=True)

            mock_file.write.assert_called_with(large_content)
            mock_replace.assert_called_once()

    @patch("src.core.services.file_service.FileService._validate_path")
    def test_save_text_async_os_error(
        self,
        mock_validate: MagicMock,
        file_service: FileService,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Verify handling of generic OSError."""
        with patch("tempfile.mkstemp") as mock_mkstemp:
            mock_path = MagicMock()
            mock_path.__str__.return_value = "file.md"  # type: ignore[attr-defined]
            mock_validate.return_value = mock_path
            mock_mkstemp.side_effect = OSError("Disk full")

            file_service.save_text_async("content", "file.md")
            file_service._executor.shutdown(wait=True)

            assert "OS error" in caplog.text or "Error writing to file.md" in caplog.text
