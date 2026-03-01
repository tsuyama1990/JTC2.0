import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src.core.config import get_settings
from src.core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class FileService:
    """
    Service for handling file operations securely and efficiently.
    Uses ThreadPoolExecutor for non-blocking I/O in async contexts.
    """

    def __init__(self) -> None:
        # Max workers limited to avoid thread exhaustion
        self._executor = ThreadPoolExecutor(max_workers=5)
        self.settings = get_settings()

    def _validate_path(self, path: str | Path) -> Path:
        """
        Validate path to prevent traversal.
        """
        try:
            target_path = Path(path).resolve(strict=False)
            cwd = Path.cwd().resolve(strict=True)
        except Exception as e:
            msg = f"Invalid path: {e}"
            raise ConfigurationError(msg) from e

        if not str(target_path).startswith(str(cwd)):
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
        Includes simple retry logic for robustness.
        """
        attempts = 3
        for attempt in range(attempts):
            try:
                # Ensure parent exists
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                logger.info(f"File saved successfully to {path}")
                break
            except PermissionError:
                logger.exception(f"Permission denied writing to {path}")
                break # No point retrying permission error
            except OSError:
                if attempt < attempts - 1:
                    logger.warning(f"OS error writing to {path}, retrying... ({attempt+1}/{attempts})")
                    continue
                logger.exception(f"OS error writing to {path} after {attempts} attempts")
            except Exception:
                logger.exception(f"Unexpected error writing to {path}")
                break
