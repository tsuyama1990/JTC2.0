from src.core.config import Settings
from pathlib import Path
from unittest.mock import patch

from src.core.services.pdf_generator import PDFGenerator
from src.domain_models.persona import Persona


def test_generate_canvas_pdf_success(tmp_path: Path) -> None:
    model = Persona(
        name="John Doe",
        occupation="Farmer",
        demographics="30s, Rural",
        goals=["Increase yield"],
        frustrations=["High cost of seeds"],
        bio="John is a farmer who wants to improve his crop yield.",
    )

    with patch("src.core.services.pdf_generator.Path.cwd", return_value=tmp_path):
        result = PDFGenerator.generate_canvas_pdf(model, "test_persona.pdf")
        assert result is not None
        assert result.endswith("test_persona.pdf")

        expected_path = Path(result)
        assert expected_path.exists()


def test_generate_canvas_pdf_mkdir_failure() -> None:
    model = Persona(
        name="John Doe",
        occupation="Farmer",
        demographics="30s, Rural",
        goals=["Increase yield"],
        frustrations=["High cost of seeds"],
        bio="John is a farmer who wants to improve his crop yield.",
    )

    with patch(
        "src.core.services.pdf_generator.Path.mkdir", side_effect=Exception("Permission denied")
    ):
        result = PDFGenerator.generate_canvas_pdf(model, "test_persona.pdf")
        assert result is None


def test_generate_canvas_pdf_output_failure(tmp_path: Path) -> None:
    model = Persona(
        name="John Doe",
        occupation="Farmer",
        demographics="30s, Rural",
        goals=["Increase yield"],
        frustrations=["High cost of seeds"],
        bio="John is a farmer who wants to improve his crop yield.",
    )

    with (
        patch("src.core.services.pdf_generator.Path.cwd", return_value=tmp_path),
        patch("fpdf.FPDF.output", side_effect=Exception("Disk full")),
    ):
        result = PDFGenerator.generate_canvas_pdf(model, "test_persona.pdf")
        assert result is None
