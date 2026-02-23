from unittest.mock import MagicMock, patch

from src.domain_models.lean_canvas import LeanCanvas
from main import display_ideas_paginated, select_idea


@patch("main.get_settings")
@patch("main.input")
@patch("main.echo")
def test_display_ideas_paginated_lazy(
    mock_echo: MagicMock, mock_input: MagicMock, mock_get_settings: MagicMock
) -> None:
    """
    Test that display_ideas_paginated consumes the iterator lazily
    and respects page size.
    """
    mock_ui = mock_get_settings.return_value.ui
    mock_ui.page_size = 2
    mock_ui.press_enter = "Press Enter"

    # Create a generator that yields 5 items
    def idea_generator():
        for i in range(5):
            yield LeanCanvas(
                id=i,
                title=f"Idea {i}",
                problem="Problem is valid valid",
                customer_segments="Seg",
                unique_value_prop="UVP is valid valid",
                solution="Solution is valid valid"
            )

    # Mock input to break the loop after first page (simulate user interaction)
    # We want to verify it asks for input.
    # The loop condition is `while True`.
    # `input()` is called. If we want to exit, `input` won't cause exit unless we break.
    # The function breaks if `len(chunk) < page_size`.
    # It also breaks if `not chunk`.

    # We want to simulate full consumption over pages.
    # 5 items, page_size 2.
    # Page 1: Items 0, 1. Prompt.
    # Page 2: Items 2, 3. Prompt.
    # Page 3: Item 4. Break (count < page_size).

    # We mock input to just return (simulating Enter)
    mock_input.side_effect = ["", ""]

    display_ideas_paginated(idea_generator(), page_size=2)

    # Verify input calls (pages)
    # Total 5 items. Page size 2.
    # 1. Chunk [0, 1]. Prompt.
    # 2. Chunk [2, 3]. Prompt.
    # 3. Chunk [4]. End loop (no prompt because count < page_size).
    assert mock_input.call_count == 2


@patch("main.get_settings")
@patch("main.input")
@patch("main.echo")
def test_select_idea_lazy(
    mock_echo: MagicMock, mock_input: MagicMock, mock_get_settings: MagicMock
) -> None:
    """Test select_idea with a generator."""
    mock_ui = mock_get_settings.return_value.ui
    mock_ui.select_prompt = "Select:"

    # Match ID 3
    mock_input.return_value = "3"

    def idea_generator():
        for i in range(5):
            yield LeanCanvas(
                id=i,
                title=f"Idea {i}",
                problem="Problem is valid valid",
                customer_segments="Seg",
                unique_value_prop="UVP is valid valid",
                solution="Solution is valid valid"
            )

    result = select_idea(idea_generator())

    assert result is not None
    assert result.id == 3
