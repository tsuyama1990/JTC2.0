import argparse
import logging
import sys
import threading
from collections.abc import Iterable, Iterator
from itertools import chain

# Add src to path if running from root
sys.path.append(".")

from src.core.config import get_settings
from src.core.graph import create_app
from src.core.simulation import create_simulation_graph
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.state import GlobalState, Phase
from src.ui.renderer import SimulationRenderer

# Configure logging
settings = get_settings()
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


def echo(msg: str) -> None:
    """Print message to stdout."""
    print(msg)  # noqa: T201


def display_ideas_paginated(
    ideas: Iterable[LeanCanvas], page_size: int | None = None
) -> None:
    """
    Display generated ideas with pagination.
    """
    ui_config = get_settings().ui
    if page_size is None:
        page_size = ui_config.page_size

    iterator = iter(ideas)

    # Peek to handle "No ideas" case
    try:
        first_item = next(iterator)
    except StopIteration:
        echo(ui_config.no_ideas)
        return

    # Reconstruct iterator
    iterator = chain([first_item], iterator)
    echo(ui_config.generated_header)

    while True:
        count = 0
        has_items = False

        # Iterate manually up to page_size
        for _ in range(page_size):
            try:
                idea = next(iterator)
                has_items = True
                count += 1
                echo(f"\n[{idea.id}] {idea.title}")
                echo(f"    Problem: {idea.problem}")
                echo(f"    Solution: {idea.solution}")
                echo("-" * 50)
            except StopIteration:
                break

        if not has_items:
            break

        # If we processed fewer items than page_size, we are done
        if count < page_size:
            break

        # Prompt for next page
        input(ui_config.press_enter)


def select_idea(ideas: Iterable[LeanCanvas]) -> LeanCanvas | None:
    """Prompt user to select an idea."""
    ui_config = get_settings().ui

    while True:
        try:
            choice = input(ui_config.select_prompt)
            idx = int(choice)

            # ideas is expected to be re-iterable (list) here
            iterator = iter(ideas)
            selected = None

            for idea in iterator:
                if idea.id == idx:
                    selected = idea
                    break

            if selected:
                return selected

            echo(ui_config.id_not_found.format(idx=idx))

        except ValueError:
            echo(ui_config.invalid_input)


def _process_execution(topic: str) -> Iterator[LeanCanvas]:
    """Execute the ideation workflow."""
    ui_config = get_settings().ui
    echo(ui_config.phase_start.format(phase=Phase.IDEATION))
    echo(ui_config.researching.format(topic=topic))
    echo(ui_config.wait)

    app = create_app()
    initial_state = GlobalState(topic=topic)
    final_state = app.invoke(initial_state)

    generated_ideas_raw = final_state.get("generated_ideas", [])

    for item in generated_ideas_raw:
        if isinstance(item, LeanCanvas):
            yield item
        elif isinstance(item, dict):
            try:
                yield LeanCanvas(**item)
            except Exception:
                logger.exception("Failed to parse idea")
                continue
        else:
            logger.warning(f"Unknown item type in generated ideas: {type(item)}")


def run_simulation_mode(topic: str, selected_idea: LeanCanvas) -> None:
    """Run the simulation phase with UI."""
    # Note: We keep phase as IDEATION to avoid validation errors requiring Target Persona,
    # which is not yet created in this flow.
    initial_state = GlobalState(
        topic=topic,
        selected_idea=selected_idea,
        simulation_active=True,
        phase=Phase.IDEATION
    )

    app = create_simulation_graph()

    # Shared state container
    # We use a dict to hold the current state reference
    shared_state = {"current": initial_state}

    def background_task() -> None:
        try:
            # We use stream_mode="values" to get full state updates
            # app.stream yields state updates as dicts or objects depending on config
            for state_update in app.stream(initial_state, stream_mode="values"):
                if isinstance(state_update, dict):
                     try:
                         shared_state["current"] = GlobalState(**state_update)
                     except Exception:
                         logger.exception("Failed to convert state update to GlobalState")
                elif isinstance(state_update, GlobalState):
                     shared_state["current"] = state_update
                else:
                     logger.warning(f"Unknown state update type: {type(state_update)}")

            # Simulation finished
            # We treat the simulation as effectively done even if simulation_active is True
            # The UI loop will just continue showing the last state.

        except Exception:
            logger.exception("Simulation thread failed")

    thread = threading.Thread(target=background_task, daemon=True)
    thread.start()

    # Start UI
    renderer = SimulationRenderer(lambda: shared_state["current"])
    renderer.start()


def main() -> None:
    """CLI Entry Point."""
    parser = argparse.ArgumentParser(description="JTC 2.0")
    parser.add_argument("topic", nargs="?", help="Business topic")
    args = parser.parse_args()

    ui_config = get_settings().ui
    echo("=== JTC 2.0 ===")

    try:
        topic = args.topic
        if not topic:
            topic = input("Enter a business topic (e.g., 'AI for Agriculture'): ")

        if not topic or not topic.strip():
            echo(ui_config.topic_empty)
            return

        if len(topic) > 200:
            echo("Topic is too long.")
            return

        typed_ideas_gen = _process_execution(topic)

        # Buffer ideas for selection
        ideas_list = list(typed_ideas_gen)

        if not ideas_list:
            echo(ui_config.no_ideas)
            return

        display_ideas_paginated(ideas_list)

        selected_idea = select_idea(ideas_list)

        if selected_idea:
            echo(ui_config.selected.format(title=selected_idea.title))
            run_simulation_mode(topic, selected_idea)

    except Exception as e:
        logger.exception("Application execution failed")
        echo(ui_config.execution_error.format(e=e))


if __name__ == "__main__":
    main()
