import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from fpdf import FPDF

from src.core.config import get_settings
from src.core.exceptions import ConfigurationError
from src.domain_models.alternative_analysis import AlternativeAnalysis
from src.domain_models.persona import Persona
from src.domain_models.value_proposition_canvas import ValuePropositionCanvas

logger = logging.getLogger(__name__)


class FileService:
    """
    Service for handling file operations securely and efficiently.
    Uses ThreadPoolExecutor for non-blocking I/O in async contexts.
    """

    def __init__(self) -> None:
        # Max workers scales with CPU count to avoid thread starvation under load
        max_workers = (os.cpu_count() or 1) * 2 + 1
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self.settings = get_settings()

    def _validate_path(self, path: str | Path) -> Path:
        """
        Validate path to prevent traversal.
        """
        try:
            p = Path(path)
            # If path doesn't exist, we resolve its parent, which must exist
            if p.exists():
                target_path = p.resolve(strict=True)
            else:
                # Ensure the parent directory resolves cleanly and we construct the path back
                parent = p.parent.resolve(strict=True)
                target_path = parent / p.name

            cwd = Path.cwd().resolve(strict=True)
        except Exception as e:
            msg = f"Invalid path: {e}"
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
            except (ValueError, TypeError, RuntimeError):
                logger.exception(f"Unexpected data error writing to {path}")
                break

    def generate_vpc_pdf(
        self,
        persona: Persona,
        analysis: AlternativeAnalysis,
        vpc: ValuePropositionCanvas,
        output_dir: str | Path,
    ) -> Path:
        """
        Generate a PDF containing Persona, Alternative Analysis, and Value Proposition Canvas.
        """
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)

        # 1. Persona Section
        pdf.set_font("Helvetica", style="B", size=16)
        pdf.cell(w=200, h=10, text="1. Target Persona", new_x="LMARGIN", new_y="NEXT", align="L")
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(w=0, h=10, text=f"Name: {persona.name} | Occupation: {persona.occupation}")
        pdf.multi_cell(w=0, h=10, text=f"Demographics: {persona.demographics}")
        pdf.multi_cell(w=0, h=10, text=f"Bio: {persona.bio}")
        pdf.multi_cell(w=0, h=10, text=f"Goals: {', '.join(persona.goals)}")
        pdf.multi_cell(w=0, h=10, text=f"Frustrations: {', '.join(persona.frustrations)}")
        pdf.ln(5)

        # 2. Alternative Analysis Section
        pdf.set_font("Helvetica", style="B", size=16)
        pdf.cell(w=200, h=10, text="2. Alternative Analysis", new_x="LMARGIN", new_y="NEXT", align="L")
        pdf.set_font("Helvetica", size=12)
        for alt in analysis.current_alternatives:
            pdf.multi_cell(
                w=0,
                h=10,
                text=f"- Tool: {alt.name} | Cost: {alt.financial_cost} | Time: {alt.time_cost} | UX Friction: {alt.ux_friction}",
            )
        pdf.multi_cell(w=0, h=10, text=f"Switching Cost: {analysis.switching_cost}")
        pdf.multi_cell(w=0, h=10, text=f"10x Value: {analysis.ten_x_value}")
        pdf.ln(5)

        # 3. Value Proposition Canvas Section
        pdf.set_font("Helvetica", style="B", size=16)
        pdf.cell(w=200, h=10, text="3. Value Proposition Canvas", new_x="LMARGIN", new_y="NEXT", align="L")

        pdf.set_font("Helvetica", style="B", size=14)
        pdf.cell(w=200, h=10, text="Customer Profile:", new_x="LMARGIN", new_y="NEXT", align="L")
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(w=0, h=10, text=f"Jobs: {', '.join(vpc.customer_profile.customer_jobs)}")
        pdf.multi_cell(w=0, h=10, text=f"Pains: {', '.join(vpc.customer_profile.pains)}")
        pdf.multi_cell(w=0, h=10, text=f"Gains: {', '.join(vpc.customer_profile.gains)}")

        pdf.set_font("Helvetica", style="B", size=14)
        pdf.cell(w=200, h=10, text="Value Map:", new_x="LMARGIN", new_y="NEXT", align="L")
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(w=0, h=10, text=f"Products & Services: {', '.join(vpc.value_map.products_and_services)}")
        pdf.multi_cell(w=0, h=10, text=f"Pain Relievers: {', '.join(vpc.value_map.pain_relievers)}")
        pdf.multi_cell(w=0, h=10, text=f"Gain Creators: {', '.join(vpc.value_map.gain_creators)}")

        pdf.set_font("Helvetica", style="B", size=14)
        pdf.cell(w=200, h=10, text="Fit Evaluation:", new_x="LMARGIN", new_y="NEXT", align="L")
        pdf.set_font("Helvetica", size=12)
        pdf.multi_cell(w=0, h=10, text=vpc.fit_evaluation)

        # Resolve path safely
        try:
            target_dir = self._validate_path(output_dir)
            target_dir.mkdir(parents=True, exist_ok=True)
            output_path = target_dir / "value_proposition_canvas.pdf"

            # Use unicode encoding and fallback characters to avoid latin-1 errors
            # fpdf2 supports unicode
            pdf.output(str(output_path))
            logger.info(f"VPC PDF generated successfully at {output_path}")
        except Exception:
            logger.exception("Failed to generate VPC PDF")
            raise
        else:
            return output_path
