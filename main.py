import argparse
import sys
from itertools import islice

# Add src to path if running from root
sys.path.append(".")

from src.core.config import settings
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
        echo("\nNo ideas generated. Please try again or check logs.")
        return

    total_ideas = len(ideas)
    echo(f"\n=== Generated {total_ideas} Ideas ===")

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
            input("\nPress Enter to see more...")


def select_idea(ideas: list[LeanCanvas]) -> LeanCanvas | None:
    """
    Prompt user to select an idea.

    Uses direct filtering to avoid O(N) memory allocation for a lookup dictionary.
    """
    while True:
        try:
            choice = input("\n[GATE 1] Select an Idea ID (0-9) to proceed: ")
            idx = int(choice)

            # O(N) search but O(1) memory
            for idea in ideas:
                if idea.id == idx:
                    return idea

            echo(f"ID {idx} not found. Please try again.")
        except ValueError:
            echo("Please enter a valid number.")


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
            echo("Topic cannot be empty.")
            return

        echo(f"\nPhase: {Phase.IDEATION}")
        echo(f"Researching and Ideating for: '{topic}'...")
        echo("(This may take 30-60 seconds due to search and LLM generation)...")

        app = create_app()
        initial_state = GlobalState(topic=topic)
        final_state = app.invoke(initial_state)
    except Exception as e:
        echo(f"\nError during execution: {e}")
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
        echo(f"\n✓ Selected Plan: {selected_idea.title}")
        echo("Cycle 1 Complete. State updated.")


if __name__ == "__main__":
    main()
