import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src.core.config import Settings, get_settings
from src.core.retry_handler import RetryHandler

logger = logging.getLogger(__name__)


class FileService:
    """
    Service for handling file operations securely and efficiently.
    Uses ThreadPoolExecutor for non-blocking I/O in async contexts.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        # Max workers limited to avoid thread exhaustion
        self._executor = ThreadPoolExecutor(max_workers=5)
        self.settings = settings or get_settings()

    def _validate_path(self, path: str | Path) -> Path:
        from src.core.utils import validate_safe_path

        return validate_safe_path(path, self.settings.rag.allowed_paths)

    def save_text_async(self, content: str, path: str | Path) -> None:
        """
        Save text to a file asynchronously using a thread pool.
        This prevents blocking the main event loop during file I/O.

        Args:
            content: The string content to write.
            path: The destination file path.
        """
        try:
            valid_path = self._validate_path(path)
            self._executor.submit(self._save_text_sync, content, valid_path)
        except Exception:
            logger.exception("Failed to schedule file save")

    def _save_text_sync(self, content: str, path: Path) -> None:
        """
        Synchronous implementation of save text.
        Uses RetryHandler and atomic file write strategy for robustness.
        """

        def _write_action() -> None:
            import os
            import tempfile

            # Ensure parent exists
            path.parent.mkdir(parents=True, exist_ok=True)

            # Atomic write pattern: write to temp file, then atomic rename
            fd, temp_path = tempfile.mkstemp(dir=path.parent, text=True)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(content)
                # Atomic replace
                Path(temp_path).replace(path)
                logger.info(f"File saved successfully to {path}")
            except Exception:
                import contextlib

                with contextlib.suppress(OSError):
                    Path(temp_path).unlink()
                raise

        RetryHandler.execute_with_retry(
            _write_action, max_attempts=3, error_msg=f"Error writing to {path}"
        )
