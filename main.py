import argparse
import sys
from typing import Any

# Add src to path if running from root
sys.path.append(".")

from src.core.graph import create_app
from src.domain_models.state import GlobalState, Phase


def echo(msg: str) -> None:
    """Print message to stdout."""
    print(msg)  # noqa: T201


def get_idea_property(idea: Any, prop: str, default: Any = "N/A") -> Any:
    """Helper to get property from dict or object safely."""
    if isinstance(idea, dict):
        return idea.get(prop, default)
    return getattr(idea, prop, default)


def display_ideas_paginated(ideas: list[Any], page_size: int = 5) -> None:
    """Display generated ideas with pagination."""
    if not ideas:
        echo("\nNo ideas generated. Please try again or check logs.")
        return

    total_ideas = len(ideas)
    echo(f"\n=== Generated {total_ideas} Ideas ===")

    for i in range(0, total_ideas, page_size):
        chunk = ideas[i : i + page_size]
        for idea in chunk:
            idx = get_idea_property(idea, "id", -1)
            title = get_idea_property(idea, "title")
            problem = get_idea_property(idea, "problem")
            solution = get_idea_property(idea, "solution")

            echo(f"\n[{idx}] {title}")
            echo(f"    Problem: {problem}")
            echo(f"    Solution: {solution}")
            echo("-" * 50)

        if i + page_size < total_ideas:
            input("\nPress Enter to see more...")


def select_idea(ideas: list[Any]) -> Any:
    """Prompt user to select an idea."""
    while True:
        try:
            choice = input("\n[GATE 1] Select an Idea ID (0-9) to proceed: ")
            idx = int(choice)

            for idea in ideas:
                idea_id = get_idea_property(idea, "id", -1)
                if idea_id == idx:
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

    topic = args.topic
    if not topic:
        topic = input("Enter a business topic (e.g., 'AI for Agriculture'): ")

    if not topic.strip():
        echo("Topic cannot be empty.")
        return

    echo(f"\nPhase: {Phase.IDEATION}")
    echo(f"Researching and Ideating for: '{topic}'...")
    echo("(This may take 30-60 seconds due to search and LLM generation)...")

    try:
        app = create_app()
        initial_state = GlobalState(topic=topic)
        final_state = app.invoke(initial_state)
    except Exception as e:
        echo(f"\nError during execution: {e}")
        return

    generated_ideas = final_state.get("generated_ideas", [])
    display_ideas_paginated(generated_ideas)

    if not generated_ideas:
        return

    selected_idea = select_idea(generated_ideas)
    title = get_idea_property(selected_idea, "title")

    echo(f"\n✓ Selected Plan: {title}")
    echo("Cycle 1 Complete. State updated.")


if __name__ == "__main__":
    main()
