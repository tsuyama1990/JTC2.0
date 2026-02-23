from unittest.mock import patch

from main import safe_input


def test_safe_input_basic() -> None:
    """Test simple input."""
    with patch("builtins.input", return_value="hello "):
        assert safe_input("prompt") == "hello"


def test_safe_input_eof() -> None:
    """Test EOF handling."""
    with patch("builtins.input", side_effect=EOFError):
        assert safe_input("prompt") == ""


def test_safe_input_keyboard_interrupt() -> None:
    """Test KeyboardInterrupt handling."""
    with patch("builtins.input", side_effect=KeyboardInterrupt), patch("sys.exit") as mock_exit:
        safe_input("prompt")
        mock_exit.assert_called_with(0)
