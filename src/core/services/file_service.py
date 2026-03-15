import logging
import os
import time
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

import bleach

from src.core.config import get_settings
from src.core.constants import MAX_CONTENT_MULTIPLIER
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
        # Max workers limited to avoid thread exhaustion
        self._executor = ThreadPoolExecutor(max_workers=self.settings.file_service.max_workers)

    def shutdown(self, wait: bool = True) -> None:
        """
        Cleanly shut down the thread pool executor to prevent resource leaks.
        """
        self._executor.shutdown(wait=wait)

    def _validate_path(self, path: str | Path) -> Path:
        """
        Validate path to prevent traversal.
        Strictly resolves the parent directory (which must exist) and checks using is_relative_to().
        Never uses strict=False for security-critical path validation.
        """
        path_str = str(path)
        if "\x00" in path_str:
            msg = "Null byte detected in path."
            raise ConfigurationError(msg)

        try:
            cwd = Path.cwd().resolve(strict=True)
            output_dir = cwd / self.settings.file_service.output_directory
            output_dir.mkdir(parents=True, exist_ok=True)
            output_dir = output_dir.resolve(strict=True)

            p = Path(path)

            # Resolve parent strictly (must exist)
            parent = p.parent.resolve(strict=True)

            # Reconstruct the target path
            target_path = parent / p.name

            # Atomic path validation check
            resolved_target = target_path.resolve(strict=True)
            if not resolved_target.is_relative_to(output_dir):
                msg = f"Path traversal detected: {target_path}"
                raise ConfigurationError(msg)  # noqa: TRY301

        except FileNotFoundError as e:
            # If the target file doesn't exist yet, we check the parent which we already resolved strictly
            if not parent.is_relative_to(output_dir):
                msg = f"Path traversal detected (new file): {target_path}"
                raise ConfigurationError(msg) from e
        except ConfigurationError:
            raise
        except Exception as e:
            msg = f"Invalid path: {e}"
            raise ConfigurationError(msg) from e

        return target_path

    def _validate_content_size(self, content: str, title: str = "Content") -> None:
        """Check if content size exceeds max allowed."""
        max_size = self.settings.governance.max_llm_response_size * MAX_CONTENT_MULTIPLIER
        if len(content) > max_size:
            msg = f"Content too large for {title}."
            raise ValueError(msg)

    def _sanitize_content(self, content: str) -> str:
        """Sanitize content to prevent injection attacks."""
        return bleach.clean(content, strip=True)

    def _check_permissions(self, path: Path) -> None:
        """Check if the user has write permissions for the directory."""
        dir_path = path if path.is_dir() else path.parent
        if dir_path.exists() and not os.access(dir_path, os.W_OK):
            msg = f"Permission denied for directory: {dir_path}"
            raise PermissionError(msg)

    def save_pdf_sync(  # noqa: C901
        self, state: "GlobalState", base_dir: Path, filename: str = "Final_Artifacts_Canvas.pdf", pdf_generator: PDFGenerator | None = None
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
                sanitized_content = self._sanitize_content(content)

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
            future = self._executor.submit(self._save_text_sync, content, valid_path)
            future.add_done_callback(self._handle_async_error)
        except Exception:
            logger.exception("Failed to schedule file save")

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
        Includes simple retry logic for robustness.
        """
        self._validate_content_size(content, "Text Save")

        attempts = 3
        for attempt in range(attempts):
            try:
                # Ensure parent exists
                self._check_permissions(path.parent)
                path.parent.mkdir(parents=True, exist_ok=True)
                self._check_permissions(path)
                path.write_text(content, encoding="utf-8")
                logger.info(f"File saved successfully to {path}")
                break
            except PermissionError:
                logger.exception(f"Permission denied writing to {path}")
                break  # No point retrying permission error
            except OSError:
                if attempt < attempts - 1:
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"OS error writing to {path}, retrying in {wait_time}s... ({attempt + 1}/{attempts})"
                    )
                    time.sleep(wait_time)
                    continue
                logger.exception(f"OS error writing to {path} after {attempts} attempts")
            except Exception:
                logger.exception(f"Unexpected error writing to {path}")
                break
