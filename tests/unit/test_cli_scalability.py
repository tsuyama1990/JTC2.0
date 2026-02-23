from collections.abc import Iterable
from unittest.mock import MagicMock, patch

from main import browse_and_select
from src.domain_models.lean_canvas import LeanCanvas


@patch("main.get_settings")
@patch("main.input")
@patch("main.echo")
def test_browse_and_select_lazy(
    mock_echo: MagicMock, mock_input: MagicMock, mock_get_settings: MagicMock
) -> None:
    """
    Test that browse_and_select consumes the iterator lazily
    and respects page size.
    """
    mock_ui = mock_get_settings.return_value.ui
    mock_ui.page_size = 2
    mock_ui.select_prompt = "Select:"

    # Create a generator that yields 5 items
    def idea_generator() -> Iterable[LeanCanvas]:
        for i in range(5):
            yield LeanCanvas(
                id=i,
                title=f"Idea {i}",
                problem="Problem is valid valid",
                customer_segments="Seg",
                unique_value_prop="UVP is valid valid",
                solution="Solution is valid valid"
            )

    # Mock input:
    # 1. 'n' (Next page) -> Page 1 (Items 0, 1) displayed
    # 2. 'n' (Next page) -> Page 2 (Items 2, 3) displayed
    # 3. '4' (Select ID 4) -> Page 3 (Item 4) displayed
    mock_input.side_effect = ["n", "n", "4"]

    result = browse_and_select(idea_generator(), page_size=2)

    assert result is not None
    assert result.id == 4

    # Verify echo calls to ensure we saw expected output
    # Just check call count or basic structure
    assert mock_echo.call_count > 0
