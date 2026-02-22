import sys
from typing import Any

# Add src to path if running from root
sys.path.append(".")

from src.core.graph import create_app
from src.domain_models.state import GlobalState, Phase


def echo(msg: str) -> None:
    """Print message to stdout."""
    print(msg)  # noqa: T201


def get_topic() -> str:
    """Get topic from args or input."""
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:])
    return input("Enter a business topic (e.g., 'AI for Agriculture'): ")


def display_ideas(ideas: list[Any]) -> None:
    """Display generated ideas."""
    if not ideas:
        echo("\nNo ideas generated. Please try again or check logs.")
        return

    echo(f"\n=== Generated {len(ideas)} Ideas ===")
    for idea in ideas:
        # Handle dict or object
        if isinstance(idea, dict):
            title = idea.get("title", "N/A")
            problem = idea.get("problem", "N/A")
            solution = idea.get("solution", "N/A")
            idx = idea.get("id", -1)
        else:
            title = getattr(idea, "title", "N/A")
            problem = getattr(idea, "problem", "N/A")
            solution = getattr(idea, "solution", "N/A")
            idx = getattr(idea, "id", -1)

        echo(f"\n[{idx}] {title}")
        echo(f"    Problem: {problem}")
        echo(f"    Solution: {solution}")
        echo("-" * 50)


def select_idea(ideas: list[Any]) -> Any:
    """Prompt user to select an idea."""
    while True:
        try:
            choice = input("\n[GATE 1] Select an Idea ID (0-9) to proceed: ")
            idx = int(choice)

            for idea in ideas:
                idea_id = idea.get("id", -1) if isinstance(idea, dict) else getattr(idea, "id", -1)

                if idea_id == idx:
                    return idea

            echo(f"ID {idx} not found. Please try again.")
        except ValueError:
            echo("Please enter a valid number.")


def main() -> None:
    """CLI Entry Point."""
    echo("=== JTC 2.0 Cycle 1: Foundation & Ideation ===")

    topic = get_topic()
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
    display_ideas(generated_ideas)

    if not generated_ideas:
        return

    selected_idea = select_idea(generated_ideas)

    if isinstance(selected_idea, dict):
        title = selected_idea.get("title", "N/A")
    else:
        title = getattr(selected_idea, "title", "N/A")

    echo(f"\n✓ Selected Plan: {title}")
    echo("Cycle 1 Complete. State updated.")


if __name__ == "__main__":
    main()
