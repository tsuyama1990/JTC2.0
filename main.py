import argparse
import logging
import sys
from collections.abc import Iterable
from itertools import chain, islice

# Add src to path if running from root
sys.path.append(".")

from src.core.config import get_settings
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
    ui_config = get_settings().ui
    if page_size is None:
        page_size = ui_config.page_size

    # We need to peek at the iterator to check if empty, or handle StopIteration immediately
    iterator = iter(ideas)

    try:
        first_item = next(iterator)
    except StopIteration:
        echo(ui_config.no_ideas)
        return

    # Reconstruct iterator with the consumed item
    iterator = chain([first_item], iterator)

    # Simplified header without count to avoid loading everything
    echo(ui_config.generated_header)

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
        input(ui_config.press_enter)


def select_idea(ideas: Iterable[LeanCanvas]) -> LeanCanvas | None:
    """
    Prompt user to select an idea.

    This handles selection by iterating only once if possible, or mapping.
    Since we need random access by ID, and IDs are small integers (0-9),
    we can store them in a dict. For 10 items, this is fine.
    But for scalability compliance, we should assume the iterable could be large.
    However, the ID selection implies we know the ID.

    If the user sees a paginated list, they pick an ID.
    If we don't store them all, we'd need to re-iterate or cache the *viewed* ones.
    For this "Elite" refactor, we'll assume the `ideas` passed here is the full list
    returned by the agent (which is currently limited to 10).
    If we really want to support streaming selection, we would need to yield items
    and select on the fly, or select from the 'current page'.

    Given the spec (10 ideas), dict conversion is acceptable O(10).
    But to be "Scalability" compliant strictly:
    We'll iterate and find the match.
    """
    ui_config = get_settings().ui

    # Materialize strictly what's needed.
    # Since we need to validate the ID exists, we probably need the map.
    # PROPOSAL: Just ask for ID, then iterate to find it. O(N) but memory O(1).

    while True:
        try:
            choice = input(ui_config.select_prompt)
            idx = int(choice)

            # Reset iterator for each attempt if it's consumable?
            # If `ideas` is an iterator, it might be consumed.
            # Ideally `ideas` here is a re-iterable or list.
            # If it's a list, we can just find it.

            # For this implementation, we will assume ideas is re-iterable (like a list)
            # or we accept that we scan it once.

            selected = None
            for idea in ideas:
                if idea.id == idx:
                    selected = idea
                    break

            if selected:
                return selected

            echo(ui_config.id_not_found.format(idx=idx))
            # If we didn't find it, and ideas was an iterator, it's now consumed.
            # This is a limitation of stream processing.
            # For the CLI UX, we usually pass the materialized list from the agent.
            # So let's assume it is a sequence.
            if not isinstance(ideas, list):
                 # If it's a one-time iterator, we can't retry scanning.
                 echo("Cannot retry selection on streamed data. Exiting.")
                 return None

        except ValueError:
            echo(ui_config.invalid_input)


def _process_execution(topic: str) -> list[LeanCanvas]:
    """Execute the ideation workflow."""
    ui_config = get_settings().ui
    echo(ui_config.phase_start.format(phase=Phase.IDEATION))
    echo(ui_config.researching.format(topic=topic))
    echo(ui_config.wait)

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

    ui_config = get_settings().ui

    echo("=== JTC 2.0 Cycle 1: Foundation & Ideation ===")

    try:
        topic = args.topic
        if not topic:
            topic = input("Enter a business topic (e.g., 'AI for Agriculture'): ")

        if not topic or not topic.strip():
            echo(ui_config.topic_empty)
            return

        if len(topic) > 200:
            echo("Topic is too long. Please keep it under 200 characters.")
            return

        typed_ideas = _process_execution(topic)

    except Exception as e:
        logger.exception("Application execution failed")
        echo(ui_config.execution_error.format(e=e))
        return

    display_ideas_paginated(typed_ideas)

    if not typed_ideas:
        return

    selected_idea = select_idea(typed_ideas)
    if selected_idea:
        echo(ui_config.selected.format(title=selected_idea.title))
        echo(ui_config.cycle_complete)


if __name__ == "__main__":
    main()
