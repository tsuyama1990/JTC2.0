import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

logger = logging.getLogger(__name__)


class FileService:
    """
    Service for handling file operations securely and efficiently.
    """

    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=5)

    def save_text_async(self, content: str, path: str | Path) -> None:
        """
        Save text to a file asynchronously using a thread pool.

        Args:
            content: The string content to write.
            path: The destination file path.
        """
        self._executor.submit(self._save_text_sync, content, path)

    def _save_text_sync(self, content: str, path: str | Path) -> None:
        """
        Synchronous implementation of save text.
        Includes simple retry logic for robustness.
        """
        attempts = 3
        for attempt in range(attempts):
            try:
                target_path = Path(path)
                target_path.write_text(content, encoding="utf-8")
                logger.info(f"File saved successfully to {target_path.resolve()}")
                return
            except PermissionError:
                logger.exception(f"Permission denied writing to {path}")
                break # No point retrying permission error
            except FileNotFoundError:
                logger.exception(f"Path not found: {path}")
                break
            except OSError:
                if attempt < attempts - 1:
                    logger.warning(f"OS error writing to {path}, retrying... ({attempt+1}/{attempts})")
                    continue
                logger.exception(f"OS error writing to {path} after {attempts} attempts")
            except Exception:
                logger.exception(f"Unexpected error writing to {path}")
                break
