from unittest.mock import MagicMock, patch

import pytest

from src.domain_models.simulation import DialogueMessage, Role
from src.domain_models.state import GlobalState
from src.ui.renderer import SimulationRenderer


@pytest.fixture
def mock_state() -> GlobalState:
    return GlobalState(
        debate_history=[
            DialogueMessage(role=Role.NEW_EMPLOYEE, content="Hi", timestamp=1.0)
        ]
    )


@patch("src.ui.renderer.pyxel")
def test_renderer_draw(mock_pyxel: MagicMock, mock_state: GlobalState) -> None:
    renderer = SimulationRenderer(lambda: mock_state)
    renderer.draw()

    mock_pyxel.cls.assert_called_with(0)
    # Check if text was called with expected content
    # Note: color logic is complex, just check any call
    mock_pyxel.text.assert_any_call(5, 5, f"{Role.NEW_EMPLOYEE}:", 11)
    # Check rects
    mock_pyxel.rect.assert_any_call(20, 80, 20, 30, 11)


@patch("src.ui.renderer.pyxel")
def test_renderer_update_quit(mock_pyxel: MagicMock, mock_state: GlobalState) -> None:
    renderer = SimulationRenderer(lambda: mock_state)
    mock_pyxel.btnp.return_value = True  # Q pressed

    renderer.update()
    mock_pyxel.quit.assert_called_once()


def test_renderer_console_loop() -> None:
    """Test the fallback console loop."""
    # We create a sequence of states
    msg1 = DialogueMessage(role=Role.NEW_EMPLOYEE, content="Hi", timestamp=1.0)
    msg2 = DialogueMessage(role=Role.FINANCE, content="Bye", timestamp=2.0)

    # State 1: 1 message
    s1 = GlobalState(debate_history=[msg1], simulation_active=True)
    # State 2: 2 messages
    s2 = GlobalState(debate_history=[msg1, msg2], simulation_active=True)
    # State 3: 2 messages, inactive -> should break loop
    s3 = GlobalState(debate_history=[msg1, msg2], simulation_active=False)

    states = [s1, s2, s3, s3] # extra s3 to be safe

    # Use an iterator
    state_iter = iter(states)

    def state_getter() -> GlobalState:
        return next(state_iter)

    renderer = SimulationRenderer(state_getter)
    renderer.headless = True

    with patch("builtins.print") as mock_print:
        with patch("time.sleep"): # Skip sleep
             renderer.start()

        # Verify prints
        # First iteration: count=1, last_count=0. Prints msg1.
        # Second iteration: count=2, last_count=1. Prints msg2.
        # Third iteration: count=2. simulation_active=False. Breaks.

        # Check calls. print calls might be complex due to logging or other prints.
        # We look for specific content.

        # Argument of print is f"[{msg.role}]: {msg.content}"
        mock_print.assert_any_call(f"[{Role.NEW_EMPLOYEE}]: Hi")
        mock_print.assert_any_call(f"[{Role.FINANCE}]: Bye")
