import argparse
import sys
from itertools import islice

# Add src to path if running from root
sys.path.append(".")

from src.core.config import settings
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


def echo(msg: str) -> None:
    """Print message to stdout."""
    print(msg)  # noqa: T201


def display_ideas_paginated(
    ideas: list[LeanCanvas], page_size: int = settings.ui_page_size
) -> None:
    """
    Display generated ideas with pagination using a generator-like approach.

    Args:
        ideas: List of LeanCanvas objects.
        page_size: Number of items per page.
    """
    if not ideas:
        echo(MSG_NO_IDEAS)
        return

    total_ideas = len(ideas)
    echo(MSG_GENERATED_HEADER.format(count=total_ideas))

    # Use iterator to process chunks efficiently
    iterator = iter(ideas)

    shown_count = 0
    while shown_count < total_ideas:
        # Use islice to consume chunk without creating intermediate lists of full size
        chunk = list(islice(iterator, page_size))

        if not chunk:
            break

        for idea in chunk:
            echo(f"\n[{idea.id}] {idea.title}")
            echo(f"    Problem: {idea.problem}")
            echo(f"    Solution: {idea.solution}")
            echo("-" * 50)

        shown_count += len(chunk)

        if shown_count < total_ideas:
            input(MSG_PRESS_ENTER)


def select_idea(ideas: list[LeanCanvas]) -> LeanCanvas | None:
    """
    Prompt user to select an idea.

    Uses direct filtering to avoid O(N) memory allocation for a lookup dictionary.
    """
    while True:
        try:
            choice = input(MSG_SELECT_PROMPT)
            idx = int(choice)

            # O(N) search but O(1) memory - preferred for scalability constraint
            for idea in ideas:
                if idea.id == idx:
                    return idea

            echo(MSG_ID_NOT_FOUND.format(idx=idx))
        except ValueError:
            echo(MSG_INVALID_INPUT)


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

        if not topic.strip():
            echo(MSG_TOPIC_EMPTY)
            return

        echo(MSG_PHASE_START.format(phase=Phase.IDEATION))
        echo(MSG_RESEARCHING.format(topic=topic))
        echo(MSG_WAIT)

        app = create_app()
        initial_state = GlobalState(topic=topic)
        final_state = app.invoke(initial_state)
    except Exception as e:
        echo(MSG_EXECUTION_ERROR.format(e=e))
        # In a real app, we might log the full traceback here
        return

    generated_ideas = final_state.get("generated_ideas", [])

    # Ensure strict typing
    typed_ideas: list[LeanCanvas] = []
    if generated_ideas and isinstance(generated_ideas[0], LeanCanvas):
        typed_ideas = generated_ideas
    elif generated_ideas and isinstance(generated_ideas[0], dict):
        # Convert dicts to models if necessary (LangGraph serialization)
        typed_ideas = [LeanCanvas(**g) for g in generated_ideas]

    display_ideas_paginated(typed_ideas)

    if not typed_ideas:
        return

    selected_idea = select_idea(typed_ideas)
    if selected_idea:
        echo(MSG_SELECTED.format(title=selected_idea.title))
        echo(MSG_CYCLE_COMPLETE)


if __name__ == "__main__":
    main()
