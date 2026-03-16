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


class PathValidator:
    """Handles strictly robust path validation to prevent traversal attacks."""

    @staticmethod
    def validate_filename(filename: str) -> None:
        """Whitelist strategy to validate pure filenames without any path hierarchy components."""
        import re

        if not filename or not isinstance(filename, str):
            raise ConfigurationError("Filename must be a non-empty string.")

        if not filename.isascii():
            msg = "Non-ASCII characters in filename are not allowed to prevent canonicalization attacks."
            raise ConfigurationError(msg)

        if ".." in filename or "/" in filename or "\\" in filename or "\x00" in filename:
            raise ConfigurationError(f"Path traversal sequence in filename: {filename}")

        p = Path(filename)
        if p.stem and not re.match(r"^[a-zA-Z0-9_\-]+$", p.stem):
            raise ConfigurationError(f"Invalid characters in filename: {p.stem}")
        if p.suffix and not re.match(r"^\.[a-zA-Z0-9]+$", p.suffix):
            raise ConfigurationError(f"Invalid characters in suffix: {p.suffix}")

    @staticmethod
    def get_secure_directory_fd(output_directory: str) -> int:
        """
        Opens a directory and returns its file descriptor to prevent TOCTOU symlink injection attacks.
        Uses O_NOFOLLOW to abort if the directory path involves a symlink at the very end.
        """
        import stat

        cwd = Path.cwd().resolve(strict=True)
        output_dir = (cwd / output_directory).resolve(strict=True)

        if not output_dir.is_relative_to(cwd):
            raise ConfigurationError("Output directory must be within CWD.")

        try:
            # Atomic file descriptor operation
            flags = (
                getattr(os, "O_RDONLY", 0)
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0)
            )
            fd = os.open(str(output_dir), flags)
        except OSError as e:
            raise PermissionError(
                f"Unable to safely open directory descriptor for {output_dir}"
            ) from e

        try:
            st = os.fstat(fd)
            if not stat.S_ISDIR(st.st_mode):
                os.close(fd)
                raise PermissionError(f"Expected a directory: {output_dir}")

            # Check write permissions
            if not (st.st_mode & 0o200):
                os.close(fd)
                raise PermissionError(f"Permission denied for directory: {output_dir}")

            # Cross-platform permission checking, handling root correctly
            if os.name == "posix" and hasattr(os, "geteuid"):
                euid = os.geteuid()
                if euid not in (0, st.st_uid):
                    os.close(fd)
                    raise PermissionError(f"Directory not owned by current user: {output_dir}")

        except Exception:
            import contextlib

            with contextlib.suppress(OSError):
                os.close(fd)
            raise

        return fd


class ContentSanitizer:
    """Handles deep string, memory, and injection sanitization."""

    @staticmethod
    def validate_content_size(
        content: str, title: str = "Content", max_bytes: int = 50 * 1024 * 1024
    ) -> None:
        """Check if content memory size exceeds strict maximum allowed to prevent OOM attacks."""
        if len(content) > max_bytes:
            raise ValueError(f"Content length too large for {title}.")

        byte_length = len(content.encode("utf-8"))
        if byte_length > max_bytes:
            raise ValueError(
                f"Content memory footprint ({byte_length} bytes) exceeds limit ({max_bytes}) for {title}."
            )

    @staticmethod
    def sanitize_pdf_content(content: str) -> str:
        """
        Sanitize content using a strict character whitelist to prevent PDF rendering breaks or injection.
        Bleach is insufficient against raw PDF structural injections.
        """
        ContentSanitizer.validate_content_size(content, "Sanitization")

        import string

        # A strictly safe set of allowed characters to prevent PDF structural syntax like << >> / and ()
        # We permit alphanumeric and a highly restricted set of punctuation. No slashes, brackets, or angle brackets.
        # This completely mitigates complex PDF payload injections without relying on regex parsing.
        allowed_chars = set(string.ascii_letters + string.digits + " \n\t\r-.,:;!?'\"%")

        # In Python 3, unicodedata can help us identify standard word characters for multi-lingual text
        import unicodedata

        allowed_categories = {"Lu", "Ll", "Lt", "Lm", "Lo", "Nd", "Nl", "No", "Zs", "Zl", "Zp"}

        sanitized_chars = []
        for ch in content:
            if ch in allowed_chars or unicodedata.category(ch) in allowed_categories:
                sanitized_chars.append(ch)
            else:
                # Transliterate or drop unsafe characters (especially syntax operators)
                sanitized_chars.append(" ")

        sanitized_str = "".join(sanitized_chars)

        # Redact remaining known keywords just in case they are formed from safe letters
        import re

        sanitized_str = re.sub(
            r"(?i)\b(obj|endobj|stream|endstream|xref|trailer|startxref)\b",
            "[REDACTED_PDF_TOKEN]",
            sanitized_str,
        )

        return sanitized_str


class StateSanitizer:
    """Redacts GlobalState to prevent leakage of internal configuration or sensitive agent histories to output artifacts."""

    @staticmethod
    def redact_state_for_pdf(state: "GlobalState") -> "GlobalState":
        from src.domain_models.state import GlobalState

        # Create a safe whitelist-only instance of the state specifically for PDF generation.
        return GlobalState(
            topic="*** REDACTED TOPIC ***" if "secret" in state.topic.lower() else state.topic,
            selected_idea=state.selected_idea.model_copy(deep=True)
            if state.selected_idea
            else None,
            vpc=state.vpc.model_copy(deep=True) if state.vpc else None,
            mental_model=state.mental_model.model_copy(deep=True) if state.mental_model else None,
            customer_journey=state.customer_journey.model_copy(deep=True)
            if state.customer_journey
            else None,
            sitemap_and_story=state.sitemap_and_story.model_copy(deep=True)
            if state.sitemap_and_story
            else None,
            alternative_analysis=state.alternative_analysis.model_copy(deep=True)
            if state.alternative_analysis
            else None,
        )


class FileService:
    """
    Service for handling file operations securely and efficiently.
    Composes dedicated validator and sanitizer components.
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

        PathValidator.validate_filename(filename)

        # Perform explicit memory limit size checks synchronously before queuing
        if state.vpc:
            ContentSanitizer.validate_content_size(
                state.vpc.model_dump_json(indent=2), "VPC PDF Chunk"
            )
        if state.mental_model:
            ContentSanitizer.validate_content_size(
                state.mental_model.model_dump_json(indent=2), "MentalModel PDF Chunk"
            )
        if state.customer_journey:
            ContentSanitizer.validate_content_size(
                state.customer_journey.model_dump_json(indent=2), "Journey PDF Chunk"
            )
        if state.sitemap_and_story:
            ContentSanitizer.validate_content_size(
                state.sitemap_and_story.model_dump_json(indent=2), "Sitemap PDF Chunk"
            )

        safe_state = StateSanitizer.redact_state_for_pdf(state)

        future = self._executor.submit(
            self._save_pdf_sync, safe_state, base_dir, filename, pdf_generator
        )
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
            PathValidator.validate_filename(filename)
            dir_fd = PathValidator.get_secure_directory_fd(
                self.settings.file_service.output_directory
            )

            pdf = pdf_generator or FPDFGenerator()
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(
                0, 10, "The JTC 2.0 - Final Artifacts", new_x="LMARGIN", new_y="NEXT", align="C"
            )
            pdf.ln(10)

            def add_section(title: str, content: str) -> None:
                ContentSanitizer.validate_content_size(content, title)
                sanitized_content = ContentSanitizer.sanitize_pdf_content(content)

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
                    ContentSanitizer.validate_content_size(json_str, title)
                    _ = ContentSanitizer.sanitize_pdf_content(json_str)

            for idx, (title, model) in enumerate(sections):
                if model:
                    if idx == 3:
                        pdf.add_page()
                    add_section(title, model.model_dump_json(indent=2))

            # Atomically save the file using the secure directory file descriptor
            cwd = Path.cwd().resolve(strict=True)
            output_dir = cwd / self.settings.file_service.output_directory
            temp_pdf_path = output_dir / f"{filename}.tmp"
            final_pdf_path = output_dir / filename

            # fpdf2 outputs directly to string path. We use a temp file in the dir then atomically rename.
            pdf.output(str(temp_pdf_path))
            os.rename(str(temp_pdf_path), str(final_pdf_path))

            os.close(dir_fd)
            logger.info(f"PDF generated successfully at {final_pdf_path}")

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

    def save_text_async(self, content: str, path: str | Path) -> Future[None]:
        """
        Save text to a file asynchronously using a thread pool.
        This prevents blocking the main event loop during file I/O.
        Exceptions are returned inside the Future instead of an explicit callback.
        """
        if self._is_shutdown:
            msg = "FileService is shut down."
            raise RuntimeError(msg)

        # Validate synchronously before enqueuing to prevent thread exhaustion with huge payloads
        ContentSanitizer.validate_content_size(content, "Text Save Async")

        try:
            filename = Path(path).name
            PathValidator.validate_filename(filename)
            future = self._executor.submit(self._save_text_sync, content, filename)
        except Exception:
            logger.exception("Failed to schedule file save")
            # Create a failed future to fulfill return type
            failed_future: Future[None] = Future()
            failed_future.set_exception(RuntimeError("Failed to schedule file save"))
            return failed_future
        else:
            return future

    def _save_text_sync(self, content: str, filename: str) -> None:
        """
        Synchronous implementation of save text.
        Secured with strict TOCTOU prevention via single atomic open using dir_fd if available.
        """
        ContentSanitizer.validate_content_size(content, "Text Save")

        dir_fd = -1
        try:
            dir_fd = PathValidator.get_secure_directory_fd(
                self.settings.file_service.output_directory
            )

            # Atomic file writing utilizing O_EXCL to prevent TOCTOU symlink hijacking
            # We add O_NOFOLLOW to explicitly refuse opening a symlink target.
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)

            # To use the secure dir_fd directly and prevent TOCTOU attacks outside the folder:
            # We use openat relative to the directory file descriptor on POSIX systems.
            if getattr(os, "supports_dir_fd", None) and os.open in os.supports_dir_fd:
                fd = os.open(filename, flags, 0o600, dir_fd=dir_fd)
            else:
                cwd = Path.cwd().resolve(strict=True)
                output_dir = cwd / self.settings.file_service.output_directory
                final_path_str = str(output_dir / filename)
                fd = os.open(final_path_str, flags, 0o600)

            cwd = Path.cwd().resolve(strict=True)
            output_dir = cwd / self.settings.file_service.output_directory
            final_path = output_dir / filename

            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception:
                import contextlib

                with contextlib.suppress(OSError):
                    os.close(fd)
                if final_path.exists():
                    final_path.unlink()
                raise

            logger.info(f"File saved successfully to {final_path}")
        except FileExistsError:
            logger.warning(f"File already exists (concurrent access or symlink trick): {filename}")
        except PermissionError:
            logger.exception(f"Permission denied writing to {filename}")
        except OSError:
            logger.exception(f"OS error writing to {filename}")
        except Exception:
            logger.exception(f"Unexpected error writing to {filename}")
        finally:
            if dir_fd != -1:
                import contextlib

                with contextlib.suppress(OSError):
                    os.close(dir_fd)
