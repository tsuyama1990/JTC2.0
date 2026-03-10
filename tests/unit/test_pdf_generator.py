from pathlib import Path
from unittest.mock import MagicMock, patch

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
        from src.core.config import Settings

        mock_settings = MagicMock(spec=Settings)
        mock_settings.canvas_output_dir = str(tmp_path)
        result = PDFGenerator.generate_canvas_pdf(model, "test_persona.pdf", mock_settings)
        assert result is not None
        assert result.endswith("test_persona.pdf")

        expected_path = Path(result)
        assert expected_path.exists()


def test_generate_canvas_pdf_mkdir_failure(tmp_path: Path) -> None:
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
        from src.core.config import Settings

        mock_settings = MagicMock(spec=Settings)
        mock_settings.canvas_output_dir = str(tmp_path)
        result = PDFGenerator.generate_canvas_pdf(model, "test_persona.pdf", mock_settings)
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
        from src.core.config import Settings

        mock_settings = MagicMock(spec=Settings)
        mock_settings.canvas_output_dir = str(tmp_path)
        result = PDFGenerator.generate_canvas_pdf(model, "test_persona.pdf", mock_settings)
        assert result is None
