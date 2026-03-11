import contextlib
import logging
import os
import time
from collections.abc import Callable

import pyxel

from src.core.config import get_settings
from src.domain_models.simulation import DialogueMessage
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


class ApprovalStampRenderer:
    """Renders an Approval Stamp animation on screen."""

    def __init__(self) -> None:
        self.active = False
        self.frame_count = 0
        self.max_frames = 60
        self.x = 100
        self.y = 100

    def trigger(self) -> None:
        self.active = True
        self.frame_count = 0
        try:
            # Play a simple sound effect for the stamp
            pyxel.play(0, 0)
        except Exception:
            logger.debug("Sound playback failed or not configured.")

    def update(self) -> None:
        if self.active:
            self.frame_count += 1
            if self.frame_count >= self.max_frames:
                self.active = False

    def draw(self) -> None:
        if self.active:
            # Simple scale down effect
            scale = max(1.0, 5.0 - (self.frame_count / 10.0))
            color = 8  # Red
            # Draw a bold rectangle for the stamp border
            pyxel.rectb(self.x, self.y, int(60 * scale), int(40 * scale), color)
            # Draw the text inside
            pyxel.text(self.x + int(10 * scale), self.y + int(15 * scale), "APPROVED", color)


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
        """
        self.state_getter = state_getter
        self.headless = os.getenv("HEADLESS_MODE", "false").lower() == "true"
        self.settings = get_settings().simulation

        self.width = self.settings.width
        self.height = self.settings.height
        self.bg_color = self.settings.bg_color
        self.text_color = self.settings.text_color

        # Caching for text wrapping
        self._last_msg_content: str | None = None
        self._cached_lines: list[str] = []
        self.stamp_renderer = ApprovalStampRenderer()
        self._vpc_generated = False

    def start(self) -> None:
        """Start the Pyxel application loop."""
        if self.headless:
            logger.info("Headless mode detected. Skipping Pyxel UI.")
            self._console_loop()
            return

        try:
            pyxel.init(self.width, self.height, title=self.settings.title, fps=self.settings.fps)
            pyxel.run(self.update, self.draw)
        except Exception as e:
            logger.warning(f"Failed to initialize Pyxel (likely no display): {e}")
            logger.info("Falling back to console mode.")
            self.headless = True
            # Ensure any partial Pyxel init is cleaned up before console loop
            with contextlib.suppress(Exception):
                pyxel.quit()
            self._console_loop()
        finally:
            if not self.headless:
                with contextlib.suppress(Exception):
                    pyxel.quit()

    def _console_loop(self) -> None:
        """Fallback loop for headless environments."""
        last_count = 0
        while True:
            try:
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

                # Safety break
                if current_count >= self.settings.max_turns:
                    break

                time.sleep(self.settings.console_sleep)
            except KeyboardInterrupt:
                break
            except Exception:
                logger.exception("Console loop error")
                break

    def update(self) -> None:
        """Update logic (poll inputs)."""
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        state = self.state_getter()
        if state.value_proposition_canvas is not None and not self._vpc_generated:
            self.stamp_renderer.trigger()
            self._vpc_generated = True

        self.stamp_renderer.update()

    def draw(self) -> None:
        """Render the frame."""
        pyxel.cls(self.bg_color)
        state = self.state_getter()

        self._draw_agents()
        self._draw_dialogue(state)
        self.stamp_renderer.draw()

    def _draw_agents(self) -> None:
        """Draw rectangles representing agents."""
        for _role_name, cfg in self.settings.agents.items():
            pyxel.rect(cfg.x, cfg.y, cfg.w, cfg.h, cfg.color)
            pyxel.text(cfg.text_x, cfg.text_y, cfg.label, cfg.color)

    def _get_wrapped_lines(self, msg: DialogueMessage) -> list[str]:
        """Wrap text for display, with caching."""
        if msg.content == self._last_msg_content:
            return self._cached_lines

        self._last_msg_content = msg.content
        chars = self.settings.chars_per_line
        self._cached_lines = [msg.content[i : i + chars] for i in range(0, len(msg.content), chars)]
        return self._cached_lines

    def _draw_dialogue(self, state: GlobalState) -> None:
        """Draw the latest dialogue message."""
        if not state.debate_history:
            pyxel.text(
                self.settings.dialogue_x,
                self.settings.dialogue_y,
                self.settings.waiting_msg,
                self.text_color,
            )
            return

        msg = state.debate_history[-1]

        # Determine speaker color from config map
        color = self.text_color
        # msg.role is an Enum, we map it to string key used in settings.agents
        role_key = str(msg.role.value)
        if role_key in self.settings.agents:
            color = self.settings.agents[role_key].color

        pyxel.text(self.settings.dialogue_x, self.settings.dialogue_y, f"{msg.role}:", color)

        lines = self._get_wrapped_lines(msg)
        y = self.settings.dialogue_y + 10  # Start below role name

        for line in lines:
            pyxel.text(self.settings.dialogue_x, y, line, self.text_color)
            y += self.settings.line_height
            if y > self.settings.max_y:
                break
