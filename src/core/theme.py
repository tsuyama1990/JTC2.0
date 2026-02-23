from typing import Final

# UI Colors (Pyxel Palette)
COLOR_BG: Final[int] = 0
COLOR_TEXT: Final[int] = 7
COLOR_NEW_EMP: Final[int] = 11
COLOR_FINANCE: Final[int] = 8
COLOR_SALES: Final[int] = 9
COLOR_CPO: Final[int] = 12

# Nemawashi Colors
COLOR_NEMAWASHI_BG: Final[int] = 1
COLOR_NODE_DEFAULT: Final[int] = 8  # Red
COLOR_NODE_SUPPORT: Final[int] = 3  # Green
COLOR_EDGE_WEAK: Final[int] = 5
COLOR_EDGE_STRONG: Final[int] = 11
COLOR_SUPPORT_BAR_BG: Final[int] = 0
COLOR_SUPPORT_BAR_FILL: Final[int] = 11

# Agent Positions (Default)
AGENT_POS_NEW_EMP: Final[dict[str, int]] = {
    "x": 20,
    "y": 80,
    "w": 20,
    "h": 30,
    "text_x": 15,
    "text_y": 112,
}
AGENT_POS_FINANCE: Final[dict[str, int]] = {
    "x": 70,
    "y": 80,
    "w": 20,
    "h": 30,
    "text_x": 65,
    "text_y": 112,
}
AGENT_POS_SALES: Final[dict[str, int]] = {
    "x": 120,
    "y": 80,
    "w": 20,
    "h": 30,
    "text_x": 120,
    "text_y": 112,
}
AGENT_POS_CPO: Final[dict[str, int]] = {
    "x": 140,
    "y": 40,
    "w": 20,
    "h": 30,
    "text_x": 135,
    "text_y": 72,
}
