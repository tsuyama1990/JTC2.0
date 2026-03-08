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
    def _write_content_to_pdf(pdf: FPDF, data: dict[str, Any]) -> None:
        def add_list_to_pdf(lst: list[Any], indent: int) -> None:
            for item in lst:
                if isinstance(item, dict):
                    add_dict_to_pdf(item, indent)
                else:
                    text = f"{'  ' * (indent - 1)}  - {item!s}"
                    pdf.multi_cell(w=190, h=10, text=text)

        def add_dict_to_pdf(d: dict[str, Any], indent: int = 0) -> None:
            for key, value in d.items():
                indent_str = "  " * indent
                title_key = key.replace("_", " ").title()

                if isinstance(value, dict):
                    pdf.multi_cell(w=190, h=10, text=f"{indent_str}{title_key}:")
                    add_dict_to_pdf(value, indent + 1)
                elif isinstance(value, list):
                    pdf.multi_cell(w=190, h=10, text=f"{indent_str}{title_key}:")
                    add_list_to_pdf(value, indent + 1)
                else:
                    text = f"{indent_str}{title_key}: {value!s}"
                    pdf.multi_cell(w=190, h=10, text=text)

        add_dict_to_pdf(data)

    @staticmethod
    def generate_canvas_pdf(model: BaseModel, filename: str) -> str | None:
        """
        Generates a PDF representation of a given Pydantic model.
        """
        settings = get_settings()

        import re

        # Sanitize filename
        safe_filename = re.sub(r"[^a-zA-Z0-9_\-\.]", "", filename)
        if not safe_filename:
            logger.error("Invalid filename provided for PDF generation.")
            return None

        # Use configurable output directory
        output_dir = Path(settings.canvas_output_dir).resolve()
        if not output_dir.is_absolute():
            output_dir = (Path.cwd() / output_dir).resolve()
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            logger.exception("Failed to create outputs directory.")
            return None

        file_path = (output_dir / safe_filename).resolve()

        # Prevent path traversal
        if not str(file_path).startswith(str(output_dir)):
            logger.error("Path traversal detected.")
            return None

        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", size=12)

            # Title
            pdf.set_font("Helvetica", style="B", size=16)
            pdf.cell(
                w=200,
                h=10,
                text=f"Canvas Output: {model.__class__.__name__}",
                new_x="LMARGIN",
                new_y="NEXT",
                align="C",
            )
            pdf.ln(10)

            # Content mapping
            pdf.set_font("Helvetica", size=12)

            PDFGenerator._write_content_to_pdf(pdf, model.model_dump())

            pdf.output(str(file_path))
            logger.info(f"Generated PDF for {model.__class__.__name__} at {file_path}")
            return str(file_path)

        except Exception:
            logger.exception(f"Error generating PDF {filename}")
            return None
