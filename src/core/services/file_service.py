import logging
import os
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

        unquoted = urllib.parse.unquote(path_str)
        if unquoted != path_str:
            path_str = unquoted  # evaluate the decoded version for directory traversals

        normalized = unicodedata.normalize("NFKC", path_str)
        if normalized != path_str:
            path_str = normalized

        if ".." in path_str or "\\" in path_str:
            msg = "Path traversal sequences detected."
            raise ConfigurationError(msg)

        # Prevent complex Unicode traversal attacks by restricting to basic ASCII
        if not path_str.isascii():
            msg = "Non-ASCII characters in paths are not allowed to prevent canonicalization attacks."
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
        """Check if content memory size exceeds strict maximum allowed to prevent OOM attacks."""
        # Set a hard upper bound based on actual system expectations
        # A single PDF artifact or JSON dump should realistically never exceed 50MB in plain text.
        max_memory_bytes = getattr(
            self.settings.file_service, "max_file_size_bytes", 50 * 1024 * 1024
        )

        if len(content) > max_memory_bytes:
            msg = f"Content length too large for {title}."
            raise ValueError(msg)

        byte_length = len(content.encode("utf-8"))
        if byte_length > max_memory_bytes:
            msg = f"Content memory footprint ({byte_length} bytes) exceeds limit ({max_memory_bytes}) for {title}."
            raise ValueError(msg)

    def _sanitize_pdf_content(self, content: str) -> str:
        """
        Sanitize content specifically for PDF generation (fpdf2).
        Uses a strict whitelist to prevent any PDF-specific structure injections.
        Only allows basic alphanumeric, whitespace, and a very limited set of punctuation.
        """
        self._validate_content_size(content, "Sanitization")

        import re

        # We also need to permit basic Japanese/multilingual characters which would be blocked by string.printable
        # but block things that form PDF syntax like << >> / and ()
        import unicodedata

        allowed_categories = {
            "Lu", "Ll", "Lt", "Lm", "Lo", "Nd", "Nl", "No",
            "Pc", "Pd", "Ps", "Pe", "Pi", "Pf", "Po",
            "Zs", "Zl", "Zp", "Sm", "Sc", "Sk", "So"
        }

        # Block specific PDF structural characters
        blocked_chars = {"<", ">", "/", "(", ")", "\\"}

        sanitized_chars = []
        for ch in content:
            if ch in blocked_chars:
                sanitized_chars.append(" ")
            elif unicodedata.category(ch) in allowed_categories or ch in {"\n", "\t", "\r", " "}:
                sanitized_chars.append(ch)
            else:
                sanitized_chars.append(" ")

        sanitized_str = "".join(sanitized_chars)

        # Redact remaining known keywords just in case they are formed from safe letters
        return re.sub(r"(?i)\b(obj|endobj|stream|endstream|xref|trailer|startxref)\b", "[REDACTED_PDF_TOKEN]", sanitized_str)

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
        Ensures explicit state validation and redaction before pushing state across threads.
        """
        if self._is_shutdown:
            msg = "FileService is shut down."
            raise RuntimeError(msg)

        from src.domain_models.state import GlobalState

        if not isinstance(state, GlobalState):
            msg = f"Expected GlobalState, got {type(state)}"
            raise TypeError(msg)

        # Perform explicit memory limit size checks synchronously before queuing
        # This prevents large payloads from consuming thread pool resources.
        if state.vpc:
            self._validate_content_size(state.vpc.model_dump_json(indent=2), "VPC PDF Chunk")
        if state.mental_model:
            self._validate_content_size(state.mental_model.model_dump_json(indent=2), "MentalModel PDF Chunk")
        if state.customer_journey:
            self._validate_content_size(state.customer_journey.model_dump_json(indent=2), "Journey PDF Chunk")
        if state.sitemap_and_story:
            self._validate_content_size(state.sitemap_and_story.model_dump_json(indent=2), "Sitemap PDF Chunk")

        # Create a safe whitelist-only instance of the state specifically for PDF generation.
        # This completely avoids leaking internal configuration, agent histories, or unvalidated data.
        safe_state = GlobalState(
            topic="*** REDACTED TOPIC ***" if "secret" in state.topic.lower() else state.topic,
            selected_idea=state.selected_idea.model_copy(deep=True) if state.selected_idea else None,
            vpc=state.vpc.model_copy(deep=True) if state.vpc else None,
            mental_model=state.mental_model.model_copy(deep=True) if state.mental_model else None,
            customer_journey=state.customer_journey.model_copy(deep=True) if state.customer_journey else None,
            sitemap_and_story=state.sitemap_and_story.model_copy(deep=True) if state.sitemap_and_story else None,
            alternative_analysis=state.alternative_analysis.model_copy(deep=True) if state.alternative_analysis else None,
        )

        future = self._executor.submit(
            self._save_pdf_sync, safe_state, base_dir, filename, pdf_generator
        )
        future.add_done_callback(self._handle_async_error)
        return future

    def _save_pdf_sync(
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
        """Check if the user has write permissions for the directory and owns it securely avoiding TOCTOU."""
        dir_path = path if path.is_dir() else path.parent

        if not dir_path.exists():
            return

        import stat
        try:
            # Atomic file descriptor operation
            flags = getattr(os, "O_RDONLY", 0) | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
            fd = os.open(dir_path, flags)
        except OSError as e:
            msg = f"Unable to verify directory safely (might be a symlink or inaccessible): {e}"
            raise PermissionError(msg) from e

        try:
            st = os.fstat(fd)
            # Ensure it is a directory and not a symlink
            # O_NOFOLLOW should already prevent opening a symlink, but verify type
            if not stat.S_ISDIR(st.st_mode):
                msg = f"Expected a directory: {dir_path}"
                raise PermissionError(msg)

            # Check write permissions based on fstat mode
            # 0o200 is User Write
            if not (st.st_mode & 0o200):
                msg = f"Permission denied for directory: {dir_path}"
                raise PermissionError(msg)

            # Cross-platform permission checking, handling root correctly
            if os.name == "posix" and hasattr(os, "geteuid"):
                euid = os.geteuid()
                if euid not in (0, st.st_uid):
                    msg = f"Directory not owned by current user: {dir_path}"
                    raise PermissionError(msg)
        finally:
            os.close(fd)

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

        # Validate synchronously before enqueuing to prevent thread exhaustion with huge payloads
        self._validate_content_size(content, "Text Save Async")

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
        Secured with strict TOCTOU prevention via single atomic open without retries that could target different files.
        """
        self._validate_content_size(content, "Text Save")

        # Check permissions strictly
        self._check_permissions(path)

        try:
            # Resolve the final path exactly before open
            final_path = Path(os.path.realpath(str(path)))
            cwd = Path.cwd().resolve(strict=True)
            output_dir = cwd / self.settings.file_service.output_directory
            output_dir = output_dir.resolve(strict=True)

            if not final_path.is_relative_to(output_dir):
                msg = f"Path traversal detected before open: {final_path}"
                raise ConfigurationError(msg)  # noqa: TRY301

            # Validate the parent directory before writing to ensure it's not a symlink.
            import stat

            try:
                # lstat the parent and the file itself if it exists
                parent_st = os.lstat(final_path.parent)
                if stat.S_ISLNK(parent_st.st_mode):
                    msg = f"Parent directory is a symlink: {final_path.parent}"
                    raise ConfigurationError(msg)

                if final_path.exists():
                    target_st = os.lstat(final_path)
                    if stat.S_ISLNK(target_st.st_mode):
                        msg = f"Target file is a symlink: {final_path}"
                        raise ConfigurationError(msg)
            except OSError as e:
                msg = f"OS error verifying symlinks: {e}"
                raise ConfigurationError(msg) from e

            # Atomic file writing utilizing O_EXCL to prevent TOCTOU symlink hijacking
            # We add O_NOFOLLOW to explicitly refuse opening a symlink target.
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW

            fd = os.open(final_path, flags, 0o600)

            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"File saved successfully to {final_path}")
        except FileExistsError:
            logger.warning(f"File already exists (concurrent access or symlink trick): {path}")
        except PermissionError:
            logger.exception(f"Permission denied writing to {path}")
        except OSError:
            logger.exception(f"OS error writing to {path}")
        except Exception:
            logger.exception(f"Unexpected error writing to {path}")
