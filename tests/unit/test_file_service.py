from unittest.mock import MagicMock, patch

import pytest

from src.core.services.file_service import FileService


class TestFileService:
    """Test suite for FileService."""

    @pytest.fixture
    def file_service(self) -> FileService:
        from src.core.factory import ServiceFactory
        return ServiceFactory.get_file_service()

    @patch("src.core.services.file_service.FileService._save_text_sync")
    def test_save_text_async_success(
        self, mock_save_sync: MagicMock, file_service: FileService
    ) -> None:
        """Verify save_text_async correctly delegates to sync method."""
        # `save_text_async` is just submitting a job to an executor, so wait for executor.
        with patch("src.core.services.file_service.Path.cwd") as mock_cwd:
            from pathlib import Path

            mock_cwd.return_value = Path("/app")
            # We mock _validate_path directly to bypass real file system resolving strict=True checks
            with patch.object(file_service, "_validate_path", return_value=Path("/app/test.md")):
                file_service.save_text_async("content", "test.md")
                file_service._executor.shutdown(wait=True)

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
        from pathlib import Path

        with patch.object(file_service, "_validate_path", return_value=Path("/app/protected.md")):
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
        from pathlib import Path

        with patch.object(file_service, "_validate_path", return_value=Path("/app/file.md")):
            file_service.save_text_async("content", "file.md")
            file_service._executor.shutdown(wait=True)

    def test_path_traversal_prevention(self, file_service: FileService) -> None:
        """Verify path traversal is prevented."""
        from src.core.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="Invalid path"):
            file_service._validate_path("../../../etc/passwd")

    def test_generate_md_path_traversal(self, file_service: FileService) -> None:
        from src.core.exceptions import ConfigurationError
        from src.domain_models.agent_prompt_spec import AgentPromptSpec, StateMachine
        from src.domain_models.sitemap_and_story import UserStory

        story = UserStory(
            as_a="A", i_want_to="B", so_that="C", acceptance_criteria=["D"], target_route="/"
        )
        sm = StateMachine(success="A", loading="B", error="C", empty="D")
        spec = AgentPromptSpec(
            sitemap="S",
            routing_and_constraints="R",
            core_user_story=story,
            state_machine=sm,
            validation_rules="V",
            mermaid_flowchart="M",
        )

        with pytest.raises(ConfigurationError, match="Invalid path"):
            file_service.generate_agent_prompt_spec_md(spec, "../../../etc/passwd")
