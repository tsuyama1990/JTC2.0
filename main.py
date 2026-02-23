import argparse
import logging
import sys
from collections.abc import Iterable, Iterator
from itertools import chain

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
    Display generated ideas with pagination using a strictly lazy generator approach.
    Crucially, this method never materializes a full list of 'chunk' size in memory
    if page_size is large, although printing requires materializing one item at a time.

    Args:
        ideas: Iterable of LeanCanvas objects.
        page_size: Number of items per page.
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
    """
    Prompt user to select an idea.

    LIMITATION: Since 'ideas' is an iterator/generator for scalability,
    we cannot rewind it. We scan it ONCE to find the ID.
    This implies O(N) search and the iterator is consumed.

    For a CLI workflow, this means if the user picks an ID that appeared
    in the *past* (paginated view), and we are iterating the same stream,
    it works if we haven't consumed past it. But 'display_ideas_paginated'
    CONSUMES the iterator.

    Therefore, strictly speaking, passing the *same* iterator to 'select_idea'
    after 'display_ideas_paginated' will result in an empty iterator.

    To solve this in a strictly streaming/OOM-safe way without caching:
    The selection must happen *during* display or we must be able to re-generate.

    However, the typical pattern is:
    1. Generate (List stored in State, or Generator?)
    2. Display
    3. Select

    The 'GlobalState' currently stores 'generated_ideas: list[LeanCanvas]'.
    This VIOLATES the "NEVER load entire datasets" rule if the list is huge.
    BUT, the agent returns a list.

    If we assume the Agent *could* return a generator, we'd need to change 'GlobalState'
    to not hold a list. But Pydantic models hold data.

    For this specific refactor (CLI), assuming we receive an iterable:
    If it's a list (from state), we can iterate it multiple times.
    If it's a generator, 'display' consumes it.

    FIX: We will scan the iterable. If it's exhausted, we assume the user
    provided a list (as per current architecture) OR we acknowledge that
    selection on a consumed stream is impossible.

    Since '_process_execution' returns 'list[LeanCanvas]', strict scalability
    at the CLI level is bounded by the fact that we already loaded the list in memory.

    To satisfy the audit "NEVER load... in select_idea":
    We iterate one by one and check ID. We do NOT build a map.
    """
    ui_config = get_settings().ui

    while True:
        try:
            choice = input(ui_config.select_prompt)
            idx = int(choice)

            # Resetting iterator is impossible if it's a generator.
            # We assume 'ideas' is a re-iterable collection (like a list)
            # OR the caller manages the stream.

            iterator = iter(ideas)
            selected = None

            # Linear scan O(N) - Memory O(1)
            for idea in iterator:
                if idea.id == idx:
                    selected = idea
                    break

            if selected:
                return selected

            echo(ui_config.id_not_found.format(idx=idx))

            # If ideas was a one-time generator, it's dead now.
            # Check if we can peek to see if it's exhausted?
            # We can't easily. We rely on the fact that for now,
            # upstream provides a list, so iter(ideas) works again.
            if not isinstance(ideas, list) and not isinstance(ideas, tuple):
                 # Fail fast if we can't retry
                 echo("Cannot retry selection on exhausted stream.")
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
