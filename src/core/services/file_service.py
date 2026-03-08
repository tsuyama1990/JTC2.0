import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src.core.config import Settings, get_settings
from src.core.exceptions import ConfigurationError
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
        """
        Validate path to prevent traversal strictly using absolute paths and containment.
        """
        try:
            cwd = Path.cwd().resolve(strict=True)
            # Use strict=False initially to construct path, then resolve based on absolute bounds
            # For writing, the exact file might not exist yet, so resolve(strict=True) on the parent.
            p = Path(path)
            if not p.is_absolute():
                p = cwd / p

            # Resolve the parent directory strictly to ensure it exists and is secure
            parent_path = p.parent.resolve(strict=True)
            target_path = parent_path / p.name
        except Exception as e:
            msg = f"Invalid path resolution: {e}"
            raise ConfigurationError(msg) from e

        if not target_path.is_relative_to(cwd):
            msg = f"Path traversal detected: {target_path}"
            raise ConfigurationError(msg)

        return target_path

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
        Uses RetryHandler for robustness.
        """

        def _write_action() -> None:
            # Ensure parent exists
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            logger.info(f"File saved successfully to {path}")

        RetryHandler.execute_with_retry(
            _write_action, max_attempts=3, error_msg=f"Error writing to {path}"
        )
