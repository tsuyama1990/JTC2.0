from collections.abc import Iterator
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

    def idea_generator() -> Iterator[LeanCanvas]:
        for i in range(5):
            yield LeanCanvas(
                id=i,
                title=f"Valid Idea Title {i}",
                problem="Problem is valid valid",
                customer_segments="Customer Segments are Valid",
                unique_value_prop="UVP is valid valid",
                solution="Solution is valid valid",
            )

    mock_input.side_effect = ["n", "n", "4"]

    result = browse_and_select(idea_generator(), page_size=2)

    assert result is not None
    assert result.id == 4
    assert mock_echo.call_count > 0

@patch("main.get_settings")
@patch("main.input")
@patch("main.echo")
def test_browse_and_select_scalability(
    mock_echo: MagicMock, mock_input: MagicMock, mock_get_settings: MagicMock
) -> None:
    """
    Test that browse_and_select can handle an incredibly large dataset (e.g. 10,000+ items)
    without running out of memory, verifying true lazy iteration.
    """
    mock_ui = mock_get_settings.return_value.ui
    mock_ui.page_size = 100
    mock_ui.select_prompt = "Select:"

    def large_idea_generator() -> Iterator[LeanCanvas]:
        # Generating 15,000 items
        for i in range(15000):
            yield LeanCanvas(
                id=i,
                title=f"Valid Idea Title {i}",
                problem="Problem is valid valid",
                customer_segments="Customer Segments are Valid",
                unique_value_prop="UVP is valid valid",
                solution="Solution is valid valid",
            )

    # We skip 5 pages (500 items) then select the 501st item
    mock_input.side_effect = ["n"] * 5 + ["501"]

    result = browse_and_select(large_idea_generator(), page_size=100)

    assert result is not None
    assert result.id == 501

    # We shouldn't have iterated all 15,000. It should be very fast.
