import argparse
import logging
import sys
import threading
from collections.abc import Iterator
from itertools import chain, islice
from pathlib import Path

# Add src to path if running from root
sys.path.append(".")

from src.core.config import UIConfig, get_settings
from src.core.graph import create_app
from src.core.simulation import create_simulation_graph
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


def safe_input(prompt: str) -> str:
    """
    Safely handle user input with stripping and EOF handling.

    Args:
        prompt: The prompt to display.

    Returns:
        Cleaned input string.
    """
    try:
        return input(prompt).strip()
    except EOFError:
        return ""
    except KeyboardInterrupt:
        sys.exit(0)


def _process_page_selection(
    page_items: list[LeanCanvas],
    page_size: int,
    ui_config: UIConfig
) -> LeanCanvas | None | str:
    """Handle user input for a single page."""
    for item in page_items:
        echo(f"\n[{item.id}] {item.title}")
        echo(f"    Problem: {item.problem}")
        echo(f"    Solution: {item.solution}")
        echo("-" * 50)

    while True:
        choice = safe_input(ui_config.select_prompt)

        if not choice:
            continue

        if choice.lower() == 'n':
            # If strictly less than page size, we know it's the last page
            if len(page_items) < page_size:
                echo("End of list.")
                return None
            return 'next'

        try:
            idx = int(choice)
            # Search in CURRENT page only
            selected = next((i for i in page_items if i.id == idx), None)

            if selected:
                return selected

            echo(ui_config.id_not_found.format(idx=idx))
        except ValueError:
            echo(ui_config.invalid_input)

    return None


def browse_and_select(ideas_gen: Iterator[LeanCanvas], page_size: int | None = None) -> LeanCanvas | None:
    """
    Browse items from generator in chunks (pages) and allow selection.
    Strictly O(page_size) memory usage.
    """
    ui_config = get_settings().ui
    if page_size is None:
        page_size = ui_config.page_size

    # Validation
    if page_size <= 0:
        logger.warning(f"Invalid page_size {page_size}, defaulting to 5")
        page_size = 5

    # Peek to handle empty generator
    try:
        first_item = next(ideas_gen)
    except StopIteration:
        echo(ui_config.no_ideas)
        return None

    # Put first item back into a new iterator
    current_iter = chain([first_item], ideas_gen)

    echo(ui_config.generated_header)

    while True:
        # Materialize only ONE page (O(page_size) memory)
        page_items = list(islice(current_iter, page_size))

        if not page_items:
            break

        result = _process_page_selection(page_items, page_size, ui_config)

        if isinstance(result, LeanCanvas):
            return result

        if result is None:
            return None

        # If result is 'next', loop continues
        if result == 'next':
             continue

    return None


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

    if generated_ideas_raw is None:
        return

    # Normalize to iterator
    iterator = (
        generated_ideas_raw
        if isinstance(generated_ideas_raw, Iterator)
        else iter(generated_ideas_raw)
    )

    for item in iterator:
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
                         # Update shared state safely
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


def ingest_transcript(filepath: str) -> None:
    """Ingest a transcript file into the RAG engine."""
    try:
        echo(f"Ingesting transcript from {filepath}...")
        with Path(filepath).open(encoding="utf-8") as f:
            content = f.read()

        rag = RAG()
        rag.ingest_text(content, source=filepath)
        rag.persist_index()
        echo(f"Successfully ingested {filepath} into vector store.")
    except Exception as e:
        logger.exception("Ingestion failed")
        echo(f"Error ingesting file: {e}")


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

        if not topic or not topic.strip():
            echo(ui_config.topic_empty)
            return

        if len(topic) > 200:
            echo("Topic is too long.")
            return

        # STRICT SCALABILITY: typed_ideas_gen is a generator.
        # We pass it directly to the browse function without converting to list.
        typed_ideas_gen = _process_execution(topic)

        selected_idea = browse_and_select(typed_ideas_gen)

        if selected_idea:
            echo(ui_config.selected.format(title=selected_idea.title))
            run_simulation_mode(topic, selected_idea)

    except Exception as e:
        logger.exception("Application execution failed")
        echo(ui_config.execution_error.format(e=e))


if __name__ == "__main__":
    main()
