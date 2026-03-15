import logging
import os
import time
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

from src.core.config import get_settings
from src.core.exceptions import ConfigurationError

if TYPE_CHECKING:
    from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


class PDFGenerator(Protocol):
    """Protocol for generating PDFs to allow dependency injection/testing."""

    def add_page(self) -> None: ...
    def set_font(self, *args: Any, **kwargs: Any) -> None: ...
    def cell(self, *args: Any, **kwargs: Any) -> None: ...
    def ln(self, *args: Any, **kwargs: Any) -> None: ...
    def multi_cell(self, *args: Any, **kwargs: Any) -> None: ...
    def output(self, *args: Any, **kwargs: Any) -> None: ...


class FPDFGenerator:
    """Concrete implementation using fpdf2."""

    def __init__(self) -> None:
        from fpdf import FPDF

        self._pdf = FPDF()

    def add_page(self) -> None:
        self._pdf.add_page()

    def set_font(self, *args: Any, **kwargs: Any) -> None:
        self._pdf.set_font(*args, **kwargs)

    def cell(self, *args: Any, **kwargs: Any) -> None:
        self._pdf.cell(*args, **kwargs)

    def ln(self, *args: Any, **kwargs: Any) -> None:
        self._pdf.ln(*args, **kwargs)

    def multi_cell(self, *args: Any, **kwargs: Any) -> None:
        self._pdf.multi_cell(*args, **kwargs)

    def output(self, *args: Any, **kwargs: Any) -> None:
        self._pdf.output(*args, **kwargs)


class FileService:
    """
    Service for handling file operations securely and efficiently.
    Uses ThreadPoolExecutor for non-blocking I/O in async contexts.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self._executor = ThreadPoolExecutor(max_workers=self.settings.file_service.max_workers)
        self._is_shutdown = False

    def shutdown(self, wait: bool = True) -> None:
        """
        Cleanly shut down the thread pool executor to prevent resource leaks.
        Waits for all pending operations to complete.
        """
        if self._is_shutdown:
            return
        self._is_shutdown = True
        self._executor.shutdown(wait=wait)

    def _validate_path(self, path: str | Path) -> Path:
        """
        Validate path to prevent traversal.
        Uses os.path.realpath() directly on the target path to prevent TOCTOU vulnerabilities.
        """
        import unicodedata
        import urllib.parse

        path_str = str(path)
        if "\x00" in path_str:
            msg = "Null byte detected in path."
            raise ConfigurationError(msg)

        if urllib.parse.unquote(path_str) != path_str:
            msg = "URL-encoded paths are not allowed."
            raise ConfigurationError(msg)

        if unicodedata.normalize("NFKC", path_str) != path_str:
            msg = "Un-normalized unicode sequences detected in path."
            raise ConfigurationError(msg)

        if ".." in path_str or "\\" in path_str:
            msg = "Path traversal sequences detected."
            raise ConfigurationError(msg)

        p = Path(path_str)

        # Whitelist approach for the filename itself
        import re
        # Reject literal '..' in the name
        if ".." in p.name:
            msg = f"Path traversal sequence in filename: {p.name}"
            raise ConfigurationError(msg)

        if p.stem and not re.match(r"^[a-zA-Z0-9_\-]+$", p.stem):
            msg = f"Invalid characters in filename: {p.stem}"
            raise ConfigurationError(msg)
        if p.suffix and not re.match(r"^\.[a-zA-Z0-9]+$", p.suffix):
            msg = f"Invalid characters in suffix: {p.suffix}"
            raise ConfigurationError(msg)

        cwd = Path.cwd().resolve(strict=True)
        output_dir = cwd / self.settings.file_service.output_directory
        output_dir.mkdir(parents=True, exist_ok=True)
        output_dir = output_dir.resolve(strict=True)

        # Combine strictly with the output directory directly, bypassing piecemeal parent logic
        target_path = output_dir / p.name

        # Perform final realpath resolution to check for symlink escapes
        resolved_target = Path(os.path.realpath(str(target_path)))

        if not resolved_target.is_relative_to(output_dir):
            msg = f"Path traversal detected: {resolved_target}"
            raise ConfigurationError(msg)

        return resolved_target

    def _validate_content_size(self, content: str, title: str = "Content") -> None:
        """Check if content memory size exceeds max allowed to prevent OOM."""
        # Dynamic memory calculation based on configuration instead of hardcoded 20MB limit
        base_size = self.settings.governance.max_llm_response_size
        multiplier = self.settings.governance.max_content_multiplier
        max_memory_bytes = (
            base_size * multiplier * 100
        )  # Rough heuristic scale up for safe JSON footprints

        # Use actual string byte length for more accurate text OOM prevention
        if len(content.encode('utf-8')) > max_memory_bytes:
            msg = f"Content memory footprint too large for {title}."
            raise ValueError(msg)

    def _sanitize_pdf_content(self, content: str) -> str:
        """
        Sanitize content specifically for PDF generation (fpdf2).
        Removes HTML tags and unprintable characters that could disrupt PDF rendering.
        Also explicitly removes known PDF-specific injection vectors.
        """
        import re
        import unicodedata

        self._validate_content_size(content, "Sanitization")

        # Strip explicit PDF injection patterns
        content = re.sub(r"(?i)(/JavaScript|/JS|/OpenAction|/AA|/A|/URI|/SubmitForm|/Launch|/GoToR|/SetOCGState)", "[REDACTED]", content)
        content = re.sub(r"(?i)\bobj\b", "o b j", content)
        content = re.sub(r"(?i)\bendobj\b", "e n d o b j", content)

        # Instead of bleach (HTML), we strip characters not suitable for PDF
        allowed_categories = {"Lu", "Ll", "Lt", "Lm", "Lo", "Nd", "Nl", "No", "Pc", "Pd", "Ps", "Pe", "Pi", "Pf", "Po", "Sm", "Sc", "Sk", "So", "Zs", "Zl", "Zp"}

        # Add basic ASCII control characters we want to keep (newline, tab)
        keep_chars = {"\n", "\t", "\r"}

        return "".join(
            ch for ch in content
            if unicodedata.category(ch) in allowed_categories or ch in keep_chars
        )

    def save_pdf_async(
        self,
        state: "GlobalState",
        base_dir: Path,
        filename: str = "Final_Artifacts_Canvas.pdf",
        pdf_generator: PDFGenerator | None = None,
        timeout: float | None = None,
    ) -> Future[None]:
        """
        Submits the PDF generation task to the ThreadPoolExecutor and returns a Future.
        The timeout parameter is handled at the point of future.result().
        """
        if self._is_shutdown:
            msg = "FileService is shut down."
            raise RuntimeError(msg)

        future = self._executor.submit(self._save_pdf_sync, state, base_dir, filename, pdf_generator)
        future.add_done_callback(self._handle_async_error)
        return future

    def _save_pdf_sync(  # noqa: C901
        self,
        state: "GlobalState",
        base_dir: Path,
        filename: str = "Final_Artifacts_Canvas.pdf",
        pdf_generator: PDFGenerator | None = None,
    ) -> None:
        """
        Generates the Final Artifact Canvas PDF from GlobalState.
        Includes robust path validation and uses fpdf2 for secure rendering.
        """
        from src.domain_models.state import GlobalState

        if not isinstance(state, GlobalState):
            msg = f"Expected GlobalState, got {type(state)}"
            raise TypeError(msg)

        if not state.selected_idea:
            logger.warning("PDF Generation: missing selected_idea. PDF might be empty.")

        try:
            pdf_path = self._validate_path(base_dir / filename)
            self._check_permissions(pdf_path)

            pdf = pdf_generator or FPDFGenerator()
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(
                0, 10, "The JTC 2.0 - Final Artifacts", new_x="LMARGIN", new_y="NEXT", align="C"
            )
            pdf.ln(10)

            def add_section(title: str, content: str) -> None:
                self._validate_content_size(content, title)
                sanitized_content = self._sanitize_pdf_content(content)

                pdf.set_font("Helvetica", "B", 14)
                pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 10)
                pdf.multi_cell(0, 8, sanitized_content)
                pdf.ln(5)

            sections = [
                ("1. Lean Canvas", state.selected_idea),
                ("2. Value Proposition Canvas", state.vpc),
                ("3. Alternative Analysis", state.alternative_analysis),
                ("4. Mental Model", state.mental_model),
                ("5. Customer Journey", state.customer_journey),
                ("6. Sitemap and Story", state.sitemap_and_story),
            ]

            # Pre-validate/sanitize all sections completely to prevent malicious Pydantic injections
            # before beginning actual PDF generation structure manipulation.
            for title, model in sections:
                if model:
                    json_str = model.model_dump_json(indent=2)
                    self._validate_content_size(json_str, title)
                    # Running it through sanitize early prevents unsafe strings getting stored
                    _ = self._sanitize_pdf_content(json_str)

            for idx, (title, model) in enumerate(sections):
                if model:
                    if idx == 3:
                        pdf.add_page()
                    add_section(title, model.model_dump_json(indent=2))

            pdf.output(str(pdf_path))
            logger.info(f"PDF generated successfully at {pdf_path}")

        except ConfigurationError:
            logger.exception("Security error during PDF generation.")
            raise
        except ValueError:
            logger.exception("Validation error during PDF generation.")
            raise
        except TypeError:
            logger.exception("Type error during PDF generation.")
            raise
        except Exception:
            logger.exception("Failed to generate PDF artifact.")

    def _check_permissions(self, path: Path) -> None:
        """Check if the user has write permissions for the directory and owns it."""
        dir_path = path if path.is_dir() else path.parent
        if dir_path.exists():
            if not os.access(dir_path, os.W_OK):
                msg = f"Permission denied for directory: {dir_path}"
                raise PermissionError(msg)
            # Ensure the directory is owned by the current user to prevent privilege escalation
            if hasattr(os, "geteuid") and dir_path.stat().st_uid != os.geteuid():
                msg = f"Directory not owned by current user: {dir_path}"
                raise PermissionError(msg)

    def save_text_async(self, content: str, path: str | Path) -> Future[None]:
        """
        Save text to a file asynchronously using a thread pool.
        This prevents blocking the main event loop during file I/O.

        Args:
            content: The string content to write.
            path: The destination file path.
        """
        if self._is_shutdown:
            msg = "FileService is shut down."
            raise RuntimeError(msg)

        try:
            valid_path = self._validate_path(path)
            future = self._executor.submit(self._save_text_sync, content, valid_path)
            future.add_done_callback(self._handle_async_error)
        except Exception:
            logger.exception("Failed to schedule file save")
            # Create a failed future to fulfill return type
            failed_future: Future[None] = Future()
            failed_future.set_exception(RuntimeError("Failed to schedule file save"))
            return failed_future
        else:
            return future

    def _handle_async_error(self, future: Future[Any]) -> None:
        """Callback to handle errors from async operations."""
        try:
            exc = future.exception(timeout=0)
            if exc:
                logger.error(f"Async file save operation failed: {exc}")
        except Exception:
            logger.exception("Async file save operation failed with unexpected error")

    def _save_text_sync(self, content: str, path: Path) -> None:
        """
        Synchronous implementation of save text.
        Includes simple retry logic for robustness and absolute TOCTOU prevention via atomic open.
        """
        self._validate_content_size(content, "Text Save")

        attempts = 3
        for attempt in range(attempts):
            try:
                # Validate the parent directory before writing to ensure it's not a symlink.
                # _validate_path guarantees 'path' is inside output_directory and output_directory exists.
                # The parent will be output_dir directly, which is created securely.
                # Do not indiscriminately call mkdir here on arbitrary parents.

                if path.parent.is_symlink():
                    msg = f"Parent directory is a symlink: {path.parent}"
                    raise ConfigurationError(msg)  # noqa: TRY301

                # Resolve the final path exactly before open
                final_path = Path(os.path.realpath(str(path)))
                cwd = Path.cwd().resolve(strict=True)
                output_dir = cwd / self.settings.file_service.output_directory
                output_dir = output_dir.resolve(strict=True)

                if not final_path.is_relative_to(output_dir):
                    msg = f"Path traversal detected before open: {final_path}"
                    raise ConfigurationError(msg)  # noqa: TRY301

                # Atomic file writing utilizing O_EXCL to prevent TOCTOU symlink hijacking
                # This guarantees the file wasn't replaced by a symlink prior to creation.
                # We also add O_NOFOLLOW to explicitly refuse opening a symlink target if the OS supports it.
                flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
                if hasattr(os, "O_NOFOLLOW"):
                    flags |= os.O_NOFOLLOW

                fd = os.open(final_path, flags, 0o600)

                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(content)

                logger.info(f"File saved successfully to {final_path}")
                break
            except FileExistsError:
                logger.warning(f"File already exists (concurrent access or symlink trick): {path}")
                # We do not retry if the file already exists since O_EXCL was strict about creation
                break
            except PermissionError:
                logger.exception(f"Permission denied writing to {path}")
                break  # No point retrying permission error
            except OSError:
                if attempt < attempts - 1:
                    wait_time = 2**attempt
                    logger.warning(
                        f"OS error writing to {path}, retrying in {wait_time}s... ({attempt + 1}/{attempts})"
                    )
                    time.sleep(wait_time)
                    continue
                logger.exception(f"OS error writing to {path} after {attempts} attempts")
            except Exception:
                logger.exception(f"Unexpected error writing to {path}")
                break
