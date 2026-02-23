import logging
import os
import time
from collections.abc import Callable

import pyxel

from src.domain_models.simulation import Role
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


class SimulationRenderer:
    """
    Renders the simulation state using Pyxel (Retro RPG style).
    """

    def __init__(self, state_getter: Callable[[], GlobalState]) -> None:
        """
        Initialize the renderer.

        Args:
            state_getter: A function that returns the current GlobalState.
                          This allows the renderer to pull the latest state
                          from the simulation thread.

                          THREAD SAFETY NOTE:
                          The state_getter is expected to return a reference to a GlobalState object.
                          Since the background thread replaces the GlobalState object atomically,
                          and we only read from the returned object (which is effectively immutable
                          for the duration of the frame), this pattern is safe without locks
                          for visualization purposes.
        """
        self.state_getter = state_getter
        self.headless = os.getenv("HEADLESS_MODE", "false").lower() == "true"
        self.width = 160
        self.height = 120
        self.bg_color = 0  # Black
        self.text_color = 7  # White

    def start(self) -> None:
        """Start the Pyxel application loop."""
        if self.headless:
            logger.info("Headless mode detected. Skipping Pyxel UI.")
            self._console_loop()
            return

        try:
            pyxel.init(self.width, self.height, title="JTC Simulation", fps=30)
            pyxel.run(self.update, self.draw)
        except Exception as e:
            logger.warning(f"Failed to initialize Pyxel (likely no display): {e}")
            logger.info("Falling back to console mode.")
            self.headless = True
            self._console_loop()

    def _console_loop(self) -> None:
        """Fallback loop for headless environments."""
        last_count = 0
        while True:
            state = self.state_getter()
            current_count = len(state.debate_history)

            if current_count > last_count:
                new_msgs = state.debate_history[last_count:]
                for msg in new_msgs:
                    # Using print here as it acts as the primary UI in headless mode
                    print(f"[{msg.role}]: {msg.content}")  # noqa: T201
                last_count = current_count

            # Simple exit condition for console mode
            if not state.simulation_active and current_count > 0:
                 break

            if current_count >= 5: # Hack: Simulation usually 5 steps
                break

            time.sleep(0.5)

    def update(self) -> None:
        """Update logic (poll inputs)."""
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

    def draw(self) -> None:
        """Render the frame."""
        pyxel.cls(self.bg_color)
        state = self.state_getter()

        self._draw_agents()
        self._draw_dialogue(state)

    def _draw_agents(self) -> None:
        """Draw rectangles representing agents."""
        # Draw New Employee (Green)
        pyxel.rect(20, 80, 20, 30, 11)
        pyxel.text(15, 112, "NewEmp", 11)

        # Draw Finance (Red)
        pyxel.rect(70, 80, 20, 30, 8)
        pyxel.text(65, 112, "Finance", 8)

        # Draw Sales (Orange)
        pyxel.rect(120, 80, 20, 30, 9)
        pyxel.text(120, 112, "Sales", 9)

    def _draw_dialogue(self, state: GlobalState) -> None:
        """Draw the latest dialogue message."""
        if not state.debate_history:
            pyxel.text(5, 5, "Waiting for debate start...", self.text_color)
            return

        msg = state.debate_history[-1]

        # Determine speaker color
        color = 7
        if msg.role == Role.NEW_EMPLOYEE:
            color = 11
        elif msg.role == Role.FINANCE:
            color = 8
        elif msg.role == Role.SALES:
            color = 9

        pyxel.text(5, 5, f"{msg.role}:", color)

        # Simple text wrapping (very basic)
        content = msg.content
        y = 15
        chars_per_line = 38
        for i in range(0, len(content), chars_per_line):
            line = content[i : i + chars_per_line]
            pyxel.text(5, y, line, 7)
            y += 8
            if y > 75: # Stop if overlapping agents
                break
