import math

import pyxel

from src.core.config import get_settings
from src.core.constants import MSG_NEMAWASHI_TITLE
from src.domain_models.politics import InfluenceNetwork


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
        pyxel.rect(self.x, self.y, self.w, self.h, 1)  # Dark Blue background

        pyxel.text(self.x + 5, self.y + 5, MSG_NEMAWASHI_TITLE, 7)

        if not network:
            pyxel.text(self.x + 5, self.y + 20, "No network data.", 5)
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
        matrix = network.matrix
        for i in range(n):
            for j in range(n):
                weight = matrix[i][j]
                if i != j and weight > 0.1:  # Threshold to avoid clutter
                    start = nodes[j]
                    end = nodes[i]
                    col = 5 if weight < 0.5 else 11  # Dark blue vs Green
                    pyxel.line(start[0], start[1], end[0], end[1], col)

        # Draw nodes
        for nx, ny, s in nodes:
            col = 8  # Red
            if s.initial_support > 0.5:
                col = 3  # Green
            pyxel.circ(nx, ny, 3, col)
            pyxel.text(nx - 10, ny - 8, s.name[:5], 7)
            # Show support bar
            bar_w = 10
            fill_w = int(bar_w * s.initial_support)
            pyxel.rect(nx - 5, ny + 5, bar_w, 2, 0)
            pyxel.rect(nx - 5, ny + 5, fill_w, 2, 11)
