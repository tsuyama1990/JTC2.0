from collections.abc import Iterator
from unittest.mock import MagicMock, patch

from main import browse_and_select
from src.domain_models.lean_canvas import LeanCanvas


@patch("main.get_settings")
@patch("main.input")
@patch("main.echo")
def test_browse_and_select_memory_safety(
    mock_echo: MagicMock, mock_input: MagicMock, mock_get_settings: MagicMock
) -> None:
    """
    Test that browse_and_select consumes the iterator strictly page-by-page.
    """
    mock_ui = mock_get_settings.return_value.ui
    mock_ui.page_size = 2
    mock_ui.select_prompt = "Select:"

    # Create a generator that we can track consumption of
    consumed_count = 0
    def tracking_generator() -> Iterator[LeanCanvas]:
        nonlocal consumed_count
        for i in range(100): # Large dataset
            consumed_count += 1
            yield LeanCanvas(
                id=i,
                title=f"Idea {i}",
                problem="Problem is valid valid",
                customer_segments="Seg",
                unique_value_prop="UVP is valid valid",
                solution="Solution is valid valid"
            )

    # User action: 'n' (Next page), then '3' (Select ID 3 from Page 2 which has items 2,3)
    # Page 1: Items 0, 1 (Consumed 2)
    # Page 2: Items 2, 3 (Consumed 4)
    # Total consumption should be exactly 4 + 1 peek check?
    # Actually `chain` might peek.

    mock_input.side_effect = ["n", "3"]

    gen = tracking_generator()
    result = browse_and_select(gen, page_size=2)

    assert result is not None
    assert result.id == 3

    # Verify we didn't consume the whole generator
    # We expect roughly 4 items consumed (2 pages * 2 items)
    # chain([peek], iter) might affect count by 1.
    assert consumed_count <= 5
    assert consumed_count < 100 # Definitely not 100
