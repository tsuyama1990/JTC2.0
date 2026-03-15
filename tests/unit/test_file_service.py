import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.core.exceptions import ConfigurationError
from src.core.services.file_service import FileService
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.state import GlobalState


class TestFileService:
    """Test suite for FileService focusing on security and actual I/O."""

    @pytest.fixture
    def file_service(self) -> Generator[FileService, None, None]:
        fs = FileService()
        yield fs
        fs.shutdown(wait=True)

    def test_validate_path_traversal(self, file_service: FileService) -> None:
        """Verify path traversal attacks are blocked."""
        with pytest.raises(ConfigurationError, match="Path traversal"):
            file_service._validate_path("../../../etc/passwd")

    def test_validate_path_null_byte(self, file_service: FileService) -> None:
        """Verify null byte attacks are blocked."""
        with pytest.raises(ConfigurationError, match="Null byte"):
            file_service._validate_path("file\x00.txt")

    def test_save_text_async_success(self, file_service: FileService) -> None:
        """Verify save_text_async writes content correctly without mocks."""
        with tempfile.TemporaryDirectory() as _:
            # Overwrite the settings output dir to use temp_dir relative to cwd
            cwd = Path.cwd().resolve(strict=True)

            # Since we can't easily change the output_directory mid-flight if it's outside cwd,
            # we will create a temp directory inside the CWD for this test.
            test_out_dir = cwd / "outputs"
            test_out_dir.mkdir(parents=True, exist_ok=True)

            # Use original output_directory or default
            output_dir_name = file_service.settings.file_service.output_directory
            actual_out_dir = cwd / output_dir_name
            actual_out_dir.mkdir(parents=True, exist_ok=True)

            test_file = actual_out_dir / "test_secure.md"
            if test_file.exists():
                test_file.unlink()

            future = file_service.save_text_async("Secure content", test_file)
            future.result()  # Wait for completion

            assert test_file.exists()
            assert test_file.read_text() == "Secure content"

            # Cleanup
            test_file.unlink()

    def test_save_text_async_shutdown(self, file_service: FileService) -> None:
        """Verify save_text_async fails immediately if shutdown."""
        file_service.shutdown()
        with pytest.raises(RuntimeError, match="shut down"):
            file_service.save_text_async("content", "test.md")

    def test_save_pdf_async_shutdown(self, file_service: FileService) -> None:
        """Verify save_pdf_async fails immediately if shutdown."""
        file_service.shutdown()
        state = GlobalState(topic="Test")
        with pytest.raises(RuntimeError, match="shut down"):
            file_service.save_pdf_async(state, Path())

    def test_symlink_hijack_prevention(self, file_service: FileService) -> None:
        """Verify that symlinks inside the output directory are resolved properly and blocked if they escape."""
        cwd = Path.cwd().resolve(strict=True)
        output_dir_name = file_service.settings.file_service.output_directory
        actual_out_dir = cwd / output_dir_name
        actual_out_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as outside_dir:
            outside_file = Path(outside_dir) / "secret.txt"
            outside_file.write_text("secrets")

            symlink_path = actual_out_dir / "evil_link.txt"
            if symlink_path.exists() or symlink_path.is_symlink():
                symlink_path.unlink()

            Path(symlink_path).symlink_to(outside_file)

            try:
                with pytest.raises(ConfigurationError, match="Path traversal"):
                    file_service._validate_path(symlink_path)
            finally:
                symlink_path.unlink()

    def test_sanitize_pdf_content(self, file_service: FileService) -> None:
        """Verify PDF content sanitization strips bad characters but keeps text."""
        dirty_content = "Normal text\nwith \x00 null and \x08 backspace."
        clean_content = file_service._sanitize_pdf_content(dirty_content)
        assert "Normal text" in clean_content
        assert "\x00" not in clean_content
        assert "\x08" not in clean_content
        assert "\n" in clean_content

    def test_save_pdf_async_success(self, file_service: FileService) -> None:
        """Test PDF generation pipeline securely."""
        cwd = Path.cwd().resolve(strict=True)
        actual_out_dir = cwd / file_service.settings.file_service.output_directory
        actual_out_dir.mkdir(parents=True, exist_ok=True)

        state = GlobalState(
            topic="Secure Topic",
            selected_idea=LeanCanvas(
                id=1, title="Test Idea Generation", problem="Problem to solve effectively", customer_segments="CS",
                unique_value_prop="UVP that provides value", solution="Solution that solves the problem"
            )
        )

        mock_pdf = MagicMock()
        future = file_service.save_pdf_async(state, actual_out_dir, "test_out.pdf", pdf_generator=mock_pdf)
        future.result()

        # Verify the mock was called, indicating successful logic pass
        assert mock_pdf.add_page.called
        assert mock_pdf.output.called
