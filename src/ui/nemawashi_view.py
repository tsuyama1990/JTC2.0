import math
from typing import cast

import pyxel

from src.core.config import get_settings
from src.core.constants import MSG_NEMAWASHI_TITLE
from src.core.theme import (
    COLOR_EDGE_STRONG,
    COLOR_EDGE_WEAK,
    COLOR_NEMAWASHI_BG,
    COLOR_NODE_DEFAULT,
    COLOR_NODE_SUPPORT,
    COLOR_SUPPORT_BAR_BG,
    COLOR_SUPPORT_BAR_FILL,
    COLOR_TEXT,
)
from src.domain_models.politics import InfluenceNetwork, SparseMatrixEntry


class NemawashiView:
    """Visualizes the Nemawashi Influence Network."""

    def __init__(self, x: int, y: int, w: int, h: int) -> None:
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.settings = get_settings()

    def draw(self, network: InfluenceNetwork | None) -> None:
        """Draw the network graph."""
        # Draw background
        pyxel.rect(self.x, self.y, self.w, self.h, COLOR_NEMAWASHI_BG)

        pyxel.text(self.x + 5, self.y + 5, MSG_NEMAWASHI_TITLE, COLOR_TEXT)

        if not network:
            pyxel.text(self.x + 5, self.y + 20, "No network data.", COLOR_EDGE_WEAK)
            return

        # Simple graph visualization
        # Arrange nodes in a circle
        n = len(network.stakeholders)
        if n == 0:
            return

        cx = self.x + self.w // 2
        cy = self.y + self.h // 2
        radius = min(self.w, self.h) // 3

        nodes = []
        for i, s in enumerate(network.stakeholders):
            angle = 2 * math.pi * i / n
            nx = cx + int(radius * math.cos(angle))
            ny = cy + int(radius * math.sin(angle))
            nodes.append((nx, ny, s))

        # Draw edges (influence)
        # matrix[i][j] is influence of j on i (i listens to j)
        # Draw arrow from j to i with thickness/color proportional to weight

        def draw_edge(i: int, j: int, weight: float) -> None:
            if i != j and weight > 0.1:  # Threshold to avoid clutter
                start = nodes[j]
                end = nodes[i]
                col = COLOR_EDGE_WEAK if weight < 0.5 else COLOR_EDGE_STRONG
                pyxel.line(start[0], start[1], end[0], end[1], col)

        if network.matrix and isinstance(network.matrix[0], list):
            # Dense
            matrix_dense = cast(list[list[float]], network.matrix)
            for i in range(n):
                for j in range(n):
                     weight = matrix_dense[i][j]
                     draw_edge(i, j, weight)
        else:
            # Sparse
            entries = cast(list[SparseMatrixEntry], network.matrix)
            for e in entries:
                draw_edge(e.row, e.col, e.val)

        # Draw nodes
        for nx, ny, s in nodes:
            col = COLOR_NODE_DEFAULT
            if s.initial_support > 0.5:
                col = COLOR_NODE_SUPPORT
            pyxel.circ(nx, ny, 3, col)
            pyxel.text(nx - 10, ny - 8, s.name[:5], COLOR_TEXT)
            # Show support bar
            bar_w = 10
            fill_w = int(bar_w * s.initial_support)
            pyxel.rect(nx - 5, ny + 5, bar_w, 2, COLOR_SUPPORT_BAR_BG)
            pyxel.rect(nx - 5, ny + 5, fill_w, 2, COLOR_SUPPORT_BAR_FILL)
