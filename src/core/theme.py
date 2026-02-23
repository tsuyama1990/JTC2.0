from typing import Final

# UI Colors (Pyxel Palette)
COLOR_BG: Final[int] = 0
COLOR_TEXT: Final[int] = 7
COLOR_NEW_EMP: Final[int] = 11
COLOR_FINANCE: Final[int] = 8
COLOR_SALES: Final[int] = 9
COLOR_CPO: Final[int] = 12

# Agent Positions (Default)
AGENT_POS_NEW_EMP: Final[dict[str, int]] = {"x": 20, "y": 80, "w": 20, "h": 30, "text_x": 15, "text_y": 112}
AGENT_POS_FINANCE: Final[dict[str, int]] = {"x": 70, "y": 80, "w": 20, "h": 30, "text_x": 65, "text_y": 112}
AGENT_POS_SALES: Final[dict[str, int]] = {"x": 120, "y": 80, "w": 20, "h": 30, "text_x": 120, "text_y": 112}
AGENT_POS_CPO: Final[dict[str, int]] = {"x": 140, "y": 40, "w": 20, "h": 30, "text_x": 135, "text_y": 72}

# UI Defaults
DEFAULT_PAGE_SIZE: Final[int] = 5
DEFAULT_FPS: Final[int] = 30
DEFAULT_WIDTH: Final[int] = 160
DEFAULT_HEIGHT: Final[int] = 120
