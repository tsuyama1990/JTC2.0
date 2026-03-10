from src.core.config import Settings
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from src.core.config import Settings
from src.core.exceptions import ConfigurationError
from src.core.interfaces import IFileWriter
from src.core.retry_handler import RetryHandler

logger = logging.getLogger(__name__)


class ThreadedFileWriter(IFileWriter):
    def __init__(self, settings: Settings, executor: ThreadPoolExecutor | None = None) -> None:
        self.settings = settings
        self._executor = executor or ThreadPoolExecutor(max_workers=self.settings.threadpool.max_workers)

    def save_text_async(self, content: str, path: str | Path) -> None:
        try:
            # We assume path is already validated when hitting the writer
            valid_path = path if isinstance(path, Path) else Path(path)
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
                    try:
                        import fcntl
                        # Implement file locking to prevent concurrent writes from stomping each other
                        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                        locked = True
                    except (ImportError, AttributeError, OSError):
                        locked = False

                    try:
                        f.write(content)
                        f.flush()
                        os.fsync(f.fileno())
                    finally:
                        if locked:
                            import fcntl
                            fcntl.flock(f.fileno(), fcntl.LOCK_UN)

                # Atomic replace (POSIX/Windows safe starting Python 3.3)
                Path(temp_path).replace(path)
                logger.info(f"File saved successfully to {path}")
            except Exception:
                import contextlib

                with contextlib.suppress(OSError):
                    Path(temp_path).unlink()
                raise

        handler = RetryHandler()
        handler.execute_with_retry(_write_action, error_msg=f"Error writing to {path}")


class FileServiceFactory:
    """Factory to create FileService with its dependencies correctly."""
    @staticmethod
    def create(settings: Settings, writer: IFileWriter | None = None) -> "FileService":
        resolved_writer = writer or ThreadedFileWriter(settings=settings)
        return FileService(settings=settings, writer=resolved_writer)


class FileService:
    """
    Service for handling file operations securely and efficiently.
    Uses injected IFileWriter for non-blocking I/O in async contexts.
    """

    def __init__(self, settings: Settings, writer: IFileWriter) -> None:
        self.settings = settings
        self.writer = writer

    def _validate_path(self, path: str | Path) -> Path:
        """
        Validate path to prevent traversal strictly using absolute paths and containment.
        """
        try:
            cwd = Path.cwd().resolve(strict=True)
            # Use strict=False to handle paths that don't exist yet
            p = Path(path).resolve(strict=False)

            # Verify the resolved path is within the allowed boundary
            if not p.is_relative_to(cwd):
                msg = f"Path traversal detected: {p}"
                raise ConfigurationError(msg)
        except ConfigurationError:
            raise
        except Exception as e:
            msg = f"Invalid path format: {e}"
            raise ConfigurationError(msg) from e
        else:
            return p

    def save_text_async(self, content: str, path: str | Path) -> None:
        """
        Save text to a file asynchronously using the injected writer.
        This prevents blocking the main event loop during file I/O.

        Args:
            content: The string content to write.
            path: The destination file path.
        """
        valid_path = self._validate_path(path)
        self.writer.save_text_async(content, valid_path)

    def save_canvas_output_async(self, content: str, filename: str) -> None:
        """
        Saves output file inside the configurable canvas outputs directory.

        Args:
            content: The content to save.
            filename: The target filename.
        """
        import re

        # Sanitize filename
        safe_filename = re.sub(r"[^a-zA-Z0-9_\-\.]", "", filename)
        if not safe_filename:
            logger.error("Invalid filename provided for save_canvas_output_async.")
            return

        output_dir = Path(self.settings.canvas_output_dir).resolve()
        if not output_dir.is_absolute():
            output_dir = (Path.cwd() / output_dir).resolve()

        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            logger.exception("Failed to create outputs directory.")
            return

        target_path = output_dir / safe_filename
        self.save_text_async(content, target_path)
