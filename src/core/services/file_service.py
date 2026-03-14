import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING

from src.core.config import get_settings
from src.core.exceptions import ConfigurationError

if TYPE_CHECKING:
    from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


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
            p = Path(path)

            # Resolve parent strictly (must exist)
            parent = p.parent.resolve(strict=True)

            # Reconstruct the target path
            target_path = parent / p.name

            # Atomic path validation check
            if not target_path.is_relative_to(cwd):
                msg = f"Path traversal detected: {target_path}"
                raise ConfigurationError(msg)  # noqa: TRY301

        except ConfigurationError:
            raise
        except Exception as e:
            msg = f"Invalid path: {e}"
            raise ConfigurationError(msg) from e

        return target_path

<<<<<<< HEAD
    def save_pdf_sync(  # noqa: C901
        self, state: "GlobalState", base_dir: Path, filename: str = "Final_Artifacts_Canvas.pdf"
    ) -> None:
=======
    def save_pdf_sync(
        self, state: "GlobalState", base_dir: Path, filename: str = "Final_Artifacts_Canvas.pdf"
    ) -> None:  # noqa: C901
>>>>>>> dbf79509e5301d6b0cbef8dc6782ab30464bee9e
        """
        Generates the Final Artifact Canvas PDF from GlobalState.
        Includes robust path validation and uses fpdf2 for secure rendering.
        """
        if not state:
            msg = "GlobalState is required for PDF generation."
            raise ValueError(msg)

        # Ensure we have at least the selected idea to generate a meaningful PDF
        if not state.selected_idea:
            logger.warning("PDF Generation: missing selected_idea. PDF might be empty.")

        from fpdf import FPDF

        try:
            pdf_path = self._validate_path(base_dir / filename)

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(
                0, 10, "The JTC 2.0 - Final Artifacts", new_x="LMARGIN", new_y="NEXT", align="C"
            )
            pdf.ln(10)

            def add_section(title: str, content: str) -> None:
                pdf.set_font("Helvetica", "B", 14)
                pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 10)

                # Use multi_cell for text wrapping. Ensure utf-8 strings are handled.
                # fpdf2 natively handles utf-8.
                pdf.multi_cell(0, 8, content)
                pdf.ln(5)

            if state.selected_idea:
                add_section("1. Lean Canvas", state.selected_idea.model_dump_json(indent=2))

            if state.vpc:
                add_section("2. Value Proposition Canvas", state.vpc.model_dump_json(indent=2))

            if state.alternative_analysis:
                add_section(
                    "3. Alternative Analysis", state.alternative_analysis.model_dump_json(indent=2)
                )

            if state.mental_model:
                pdf.add_page()
                add_section("4. Mental Model", state.mental_model.model_dump_json(indent=2))

            if state.customer_journey:
                add_section("5. Customer Journey", state.customer_journey.model_dump_json(indent=2))

            if state.sitemap_and_story:
                add_section(
                    "6. Sitemap and Story", state.sitemap_and_story.model_dump_json(indent=2)
                )

            pdf.output(str(pdf_path))
            logger.info(f"PDF generated successfully at {pdf_path}")

        except ConfigurationError:
            logger.exception("Security error during PDF generation.")
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
                break  # No point retrying permission error
            except OSError:
                if attempt < attempts - 1:
                    logger.warning(
                        f"OS error writing to {path}, retrying... ({attempt + 1}/{attempts})"
                    )
                    continue
                logger.exception(f"OS error writing to {path} after {attempts} attempts")
            except Exception:
                logger.exception(f"Unexpected error writing to {path}")
                break
