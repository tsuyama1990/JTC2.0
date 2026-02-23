import argparse
import logging
import sys
from collections.abc import Iterable
from itertools import islice

# Add src to path if running from root
sys.path.append(".")

from src.core.config import get_settings
from src.core.constants import (
    MSG_CYCLE_COMPLETE,
    MSG_EXECUTION_ERROR,
    MSG_GENERATED_HEADER,
    MSG_ID_NOT_FOUND,
    MSG_INVALID_INPUT,
    MSG_NO_IDEAS,
    MSG_PHASE_START,
    MSG_PRESS_ENTER,
    MSG_RESEARCHING,
    MSG_SELECT_PROMPT,
    MSG_SELECTED,
    MSG_TOPIC_EMPTY,
    MSG_WAIT,
)
from src.core.graph import create_app
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.state import GlobalState, Phase

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
    Display generated ideas with pagination using a generator-like approach.

    Args:
        ideas: Iterable of LeanCanvas objects.
        page_size: Number of items per page.
    """
    if page_size is None:
        page_size = get_settings().ui_page_size
    # We need to peek at the iterator to check if empty, or handle StopIteration immediately
    iterator = iter(ideas)

    try:
        first_item = next(iterator)
    except StopIteration:
        echo(MSG_NO_IDEAS)
        return

    # Reconstruct iterator with the consumed item
    from itertools import chain

    iterator = chain([first_item], iterator)

    # We don't know total length of iterator upfront without consuming it.
    # So we display header without count or consume it if it's a list.
    if hasattr(ideas, "__len__"):
        echo(MSG_GENERATED_HEADER.format(count=len(ideas)))  # type: ignore
    else:
        echo("\n=== Generated Ideas ===")

    while True:
        # Use islice to consume chunk without creating intermediate lists of full size
        chunk = list(islice(iterator, page_size))

        if not chunk:
            break

        for idea in chunk:
            echo(f"\n[{idea.id}] {idea.title}")
            echo(f"    Problem: {idea.problem}")
            echo(f"    Solution: {idea.solution}")
            echo("-" * 50)

        # Check if there might be more
        # If chunk size < page_size, we are done.
        if len(chunk) < page_size:
            break

        # If we filled the page, there MIGHT be more.
        # Ideally we peek, but simplest UI interaction is just to pause.
        input(MSG_PRESS_ENTER)


def select_idea(ideas: list[LeanCanvas]) -> LeanCanvas | None:
    """
    Prompt user to select an idea.

    Uses dictionary lookup for O(1) access.

    Args:
        ideas: List of LeanCanvas objects.
    """
    # Create lookup map for O(1) access
    idea_map = {idea.id: idea for idea in ideas}

    while True:
        try:
            choice = input(MSG_SELECT_PROMPT)
            idx = int(choice)

            if idx in idea_map:
                return idea_map[idx]

            echo(MSG_ID_NOT_FOUND.format(idx=idx))
        except ValueError:
            echo(MSG_INVALID_INPUT)


def _process_execution(topic: str) -> list[LeanCanvas]:
    """Execute the ideation workflow."""
    echo(MSG_PHASE_START.format(phase=Phase.IDEATION))
    echo(MSG_RESEARCHING.format(topic=topic))
    echo(MSG_WAIT)

    app = create_app()
    initial_state = GlobalState(topic=topic)
    final_state = app.invoke(initial_state)

    generated_ideas = final_state.get("generated_ideas", [])

    typed_ideas: list[LeanCanvas] = []
    if generated_ideas:
        try:
            if isinstance(generated_ideas[0], LeanCanvas):
                typed_ideas = generated_ideas
            elif isinstance(generated_ideas[0], dict):
                typed_ideas = [LeanCanvas(**g) for g in generated_ideas]
        except Exception:
            logger.exception("Failed to parse generated ideas")
            echo("Error processing generated ideas.")
            return []

    return typed_ideas


def main() -> None:
    """CLI Entry Point."""
    parser = argparse.ArgumentParser(description="JTC 2.0 Cycle 1: Foundation & Ideation")
    parser.add_argument("topic", nargs="?", help="Business topic for ideation")
    args = parser.parse_args()

    echo("=== JTC 2.0 Cycle 1: Foundation & Ideation ===")

    try:
        topic = args.topic
        if not topic:
            topic = input("Enter a business topic (e.g., 'AI for Agriculture'): ")

        if not topic or not topic.strip():
            echo(MSG_TOPIC_EMPTY)
            return

        if len(topic) > 200:
            echo("Topic is too long. Please keep it under 200 characters.")
            return

        typed_ideas = _process_execution(topic)

    except Exception as e:
        logger.exception("Application execution failed")
        echo(MSG_EXECUTION_ERROR.format(e=e))
        return

    display_ideas_paginated(typed_ideas)

    if not typed_ideas:
        return

    selected_idea = select_idea(typed_ideas)
    if selected_idea:
        echo(MSG_SELECTED.format(title=selected_idea.title))
        echo(MSG_CYCLE_COMPLETE)


if __name__ == "__main__":
    main()
