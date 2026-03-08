import logging
from pathlib import Path
from typing import Any

from fpdf import FPDF
from pydantic import BaseModel

from src.core.config import get_settings

logger = logging.getLogger(__name__)

class PDFGenerator:
    """Service to generate PDF versions of canvases."""

    @staticmethod
    def generate_canvas_pdf(model: BaseModel, filename: str) -> str | None:
        """
        Generates a PDF representation of a given Pydantic model.
        """
        get_settings()

        # Use simple structure. Ensure the directory exists
        # In a real environment we would output to a path based on project root
        output_dir = Path.cwd() / "outputs" / "canvas"
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            logger.exception("Failed to create outputs directory.")
            return None

        file_path = output_dir / filename

        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", size=12)

            # Title
            pdf.set_font("Helvetica", style="B", size=16)
            pdf.cell(w=200, h=10, text=f"Canvas Output: {model.__class__.__name__}", new_x="LMARGIN", new_y="NEXT", align="C")
            pdf.ln(10)

            # Content mapping
            pdf.set_font("Helvetica", size=12)

            def add_dict_to_pdf(d: dict[str, Any], indent: int = 0) -> None:
                for key, value in d.items():
                    indent_str = "  " * indent
                    if isinstance(value, dict):
                        pdf.multi_cell(w=190, h=10, text=f"{indent_str}{key.replace('_', ' ').title()}:")
                        add_dict_to_pdf(value, indent + 1)
                    elif isinstance(value, list):
                        pdf.multi_cell(w=190, h=10, text=f"{indent_str}{key.replace('_', ' ').title()}:")
                        for item in value:
                            if isinstance(item, dict):
                                add_dict_to_pdf(item, indent + 1)
                            else:
                                # Safe encoding replacement for ascii support
                                text = f"{indent_str}  - {item!s}".encode("latin-1", "replace").decode("latin-1")
                                pdf.multi_cell(w=190, h=10, text=text)
                    else:
                        text = f"{indent_str}{key.replace('_', ' ').title()}: {value!s}".encode("latin-1", "replace").decode("latin-1")
                        pdf.multi_cell(w=190, h=10, text=text)

            data = model.model_dump()
            add_dict_to_pdf(data)

            pdf.output(str(file_path))
            logger.info(f"Generated PDF for {model.__class__.__name__} at {file_path}")
            return str(file_path)

        except Exception:
            logger.exception(f"Error generating PDF {filename}")
            return None
