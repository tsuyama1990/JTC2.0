import json
import logging
from pathlib import Path

from fpdf import FPDF
from pydantic import BaseModel

from src.core.config import get_settings
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


def export_phase2_documents(state: GlobalState) -> None:
    """
    Exports Phase 2 models (Persona, VPC, AlternativeAnalysis) to PDF format.
    Uses fpdf2 to generate the PDFs securely.
    """
    settings = get_settings()
    target_dir = Path(settings.pdf_export_dir).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    cwd = Path.cwd().resolve(strict=True)
    if not str(target_dir).startswith(str(cwd)):
        logger.error(f"Path traversal detected for export dir: {target_dir}")
        return

    def _export(model: BaseModel | None, filename: str) -> None:
        if model:
            valid_path = target_dir / filename
            try:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("helvetica", size=12)

                # Format content as indented JSON string for simplicity, or we could iterate fields
                content = json.dumps(model.model_dump(), ensure_ascii=False, indent=2)

                # Split content by newlines
                for line in content.split("\n"):
                    # Encode to replace unsupported characters
                    safe_line = line.encode("latin-1", "replace").decode("latin-1")
                    pdf.cell(0, 10, text=safe_line, new_x="LMARGIN", new_y="NEXT")

                # The actual writing to disk
                pdf.output(valid_path)
                logger.info(f"Successfully generated PDF: {valid_path}")
            except Exception:
                logger.exception(f"Failed to export {filename}")

    if hasattr(state, "target_persona"):
        _export(state.target_persona, "Persona.pdf")
    if hasattr(state, "value_proposition_canvas"):
        _export(state.value_proposition_canvas, "ValuePropositionCanvas.pdf")
    if hasattr(state, "alternative_analysis"):
        _export(state.alternative_analysis, "AlternativeAnalysis.pdf")

    logger.info(f"Phase 2 PDF documents exported to {target_dir}")
