import argparse
import logging
import re
import sys
from collections.abc import Iterator
from itertools import chain
from pathlib import Path

from src.core.config import get_settings
from src.core.simulation import SimulationManager, SimulationService
from src.data.rag import RAG
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


def safe_input(prompt: str, allowed_chars: str = r"^[a-zA-Z0-9\s\-_\.,:]+$") -> str:
    """Safely handle user input with stripping and EOF handling, validating against allowed characters."""
    try:
        user_in = input(prompt).strip()
    except EOFError:
        return ""
    except KeyboardInterrupt:
        sys.exit(0)
    else:
        if not re.match(allowed_chars, user_in) and user_in != "":
            logger.warning(f"Input contains special characters: {user_in}")
            return "".join(
                c for c in user_in if re.match(allowed_chars.replace("+$", "").replace("^", ""), c)
            )
        return user_in


def validate_topic(topic: str) -> str:
    """Sanitize and validate the topic string."""
    if not topic or not topic.strip():
        msg = "Topic cannot be empty."
        raise ValueError(msg)

    if len(topic) > 200:
        msg = "Topic is too long (max 200 chars)."
        raise ValueError(msg)

    if not re.match(r"^[a-zA-Z0-9\s\-_]+$", topic):
        msg = "Invalid characters in topic. Only alphanumeric, spaces, hyphens and underscores allowed."
        raise ValueError(msg)

    if not topic.strip():
        msg = "Topic is empty after sanitization."
        raise ValueError(msg)

    return topic


def validate_filepath(filepath: str) -> Path:
    """Validate filepath to prevent traversal attacks."""
    path = Path(filepath).resolve(strict=True)
    cwd = Path.cwd().resolve(strict=True)

    if not path.is_relative_to(cwd):
        msg = "File path must be within the project directory."
        raise ValueError(msg)

    if not path.exists():
        msg = f"File not found: {filepath}"
        raise ValueError(msg)

    return path


def _prompt_user_selection(current_page_items: list[LeanCanvas]) -> LeanCanvas | str:
    """Prompt user for selection and handle input lazily."""
    ui_config = get_settings().ui
    while True:
        choice = safe_input(ui_config.select_prompt)

        if not choice:
            continue

        if choice.lower() == "n":
            return "next"

        try:
            idx = int(choice)
            selected = next((i for i in current_page_items if i.id == idx), None)
            if selected:
                return selected
            echo(ui_config.id_not_found.format(idx=idx))
        except ValueError:
            echo(ui_config.invalid_input)


def browse_and_select(
    ideas_gen: Iterator[LeanCanvas], page_size: int | None = None
) -> LeanCanvas | None:
    """Browse items from generator lazily, maintaining minimal memory footprint."""
    ui_config = get_settings().ui
    if page_size is None:
        page_size = ui_config.page_size

    if page_size <= 0:
        logger.warning(f"Invalid page_size {page_size}, defaulting to 5")
        page_size = 5

    echo(ui_config.generated_header)

    current_page_items: list[LeanCanvas] = []

    while True:
        try:
            item = next(ideas_gen)
            current_page_items.append(item)

            echo(f"\n[{item.id}] {item.title}")
            echo(f"    Problem: {item.problem}")
            echo(f"    Solution: {item.solution}")
            echo("-" * 50)

            if len(current_page_items) < page_size:
                continue

        except StopIteration:
            if not current_page_items:
                echo(ui_config.no_ideas)
                return None
            echo("End of list.")

        result = _prompt_user_selection(current_page_items)
        if isinstance(result, LeanCanvas):
            return result

        current_page_items.clear()

        # Check if actually empty
        try:
            next_item = next(ideas_gen)
            ideas_gen = chain([next_item], ideas_gen)
        except StopIteration:
            return None

    return None


def run_simulation_mode(topic: str, selected_idea: LeanCanvas) -> None:
    """Run the simulation phase with UI."""
    initial_state = GlobalState(
        topic=topic, selected_idea=selected_idea, simulation_active=True, phase=Phase.IDEATION
    )

    manager = SimulationManager(initial_state, SimulationRenderer)
    manager.run()


def _read_file_safe(path: Path) -> str:
    """Read a file safely with size limits."""
    # Max size 10MB
    if path.stat().st_size > 10 * 1024 * 1024:
        msg = "File exceeds maximum allowed size of 10MB."
        raise ValueError(msg)

    # We could chunk it, but standard ingest_text in RAG accepts a single string.
    # At least we validate it's small enough to fit in memory safely.
    with path.open(encoding="utf-8") as f:
        return f.read()

def ingest_transcript(filepath: str) -> None:
    """Ingest a transcript file into the RAG engine."""
    try:
        echo(f"Ingesting transcript from {filepath}...")
        path = validate_filepath(filepath)

        content = _read_file_safe(path)

        rag = RAG()
        rag.ingest_text(content, source=str(path))
        rag.persist_index()
        echo(f"Successfully ingested {filepath} into vector store.")
    except Exception:
        logger.exception("Ingestion failed")
        echo("An unexpected error occurred. Please check the logs for details.")


def main() -> None:
    """CLI Entry Point."""
    parser = argparse.ArgumentParser(description="JTC 2.0")
    parser.add_argument("topic", nargs="?", help="Business topic")
    parser.add_argument("--ingest", help="Path to transcript file to ingest", type=str)
    args = parser.parse_args()

    ui_config = get_settings().ui
    echo("=== JTC 2.0 ===")

    if args.ingest:
        ingest_transcript(args.ingest)
        return

    try:
        topic = args.topic
        if not topic:
            topic = safe_input("Enter a business topic (e.g., 'AI for Agriculture'): ")

        topic = validate_topic(topic)

        # Use the service to isolate LangGraph logic
        sim_service = SimulationService()

        echo(ui_config.phase_start.format(phase=Phase.IDEATION))
        echo(ui_config.researching.format(topic=topic))
        echo(ui_config.wait)

        typed_ideas_gen, state = sim_service.run_ideation_to_gate(topic)
        selected_idea = browse_and_select(typed_ideas_gen)

        if selected_idea:
            echo(ui_config.selected.format(title=selected_idea.title))
            try:
                sim_service.resume_after_gate(selected_idea)
            except Exception:
                logger.exception("Failed to resume graph")
            run_simulation_mode(topic, selected_idea)

    except Exception:
        logger.exception("Application execution failed")
        echo("An unexpected error occurred. Please check the logs for details.")


if __name__ == "__main__":
    main()
