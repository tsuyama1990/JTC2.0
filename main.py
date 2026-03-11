import argparse
import logging
import re
import sys
import threading
from collections.abc import Iterator
from itertools import chain, islice
from pathlib import Path

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
    """Safely handle user input with stripping and EOF handling."""
    try:
        return input(prompt).strip()
    except EOFError:
        return ""
    except KeyboardInterrupt:
        sys.exit(0)


def validate_topic(topic: str) -> str:
    """Sanitize and validate the topic string."""
    if not topic or not topic.strip():
        msg = "Topic cannot be empty."
        raise ValueError(msg)

    if len(topic) > 200:
        msg = "Topic is too long (max 200 chars)."
        raise ValueError(msg)

    if not re.match(r"^[a-zA-Z0-9\s\-_\.,:]+$", topic):
        logger.warning(f"Topic contains special characters: {topic}")
        topic = re.sub(r"[^a-zA-Z0-9\s\-_\.,:]", "", topic)

    if not topic.strip():
        msg = "Topic is empty after sanitization."
        raise ValueError(msg)

    return topic


def validate_filepath(filepath: str) -> Path:
    """Validate filepath to prevent traversal attacks."""
    path = Path(filepath).resolve()
    cwd = Path.cwd().resolve()

    if not path.is_relative_to(cwd):
        msg = "File path must be within the project directory."
        raise ValueError(msg)

    if not path.exists():
        msg = f"File not found: {filepath}"
        raise ValueError(msg)

    return path


def _process_page_selection(
    page_items: list[LeanCanvas], page_size: int, ui_config: UIConfig
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

        if choice.lower() == "n":
            if len(page_items) < page_size:
                echo("End of list.")
                return None
            return "next"

        try:
            idx = int(choice)
            selected = next((i for i in page_items if i.id == idx), None)

            if selected:
                return selected

            echo(ui_config.id_not_found.format(idx=idx))
        except ValueError:
            echo(ui_config.invalid_input)

    return None


def browse_and_select(
    ideas_gen: Iterator[LeanCanvas], page_size: int | None = None
) -> LeanCanvas | None:
    """Browse items from generator in chunks (pages) and allow selection."""
    ui_config = get_settings().ui
    if page_size is None:
        page_size = ui_config.page_size

    if page_size <= 0:
        logger.warning(f"Invalid page_size {page_size}, defaulting to 5")
        page_size = 5

    try:
        first_item = next(ideas_gen)
    except StopIteration:
        echo(ui_config.no_ideas)
        return None

    current_iter = chain([first_item], ideas_gen)

    echo(ui_config.generated_header)

    while True:
        page_items = list(islice(current_iter, page_size))

        if not page_items:
            break

        result = _process_page_selection(page_items, page_size, ui_config)

        if isinstance(result, LeanCanvas):
            return result

        if result is None:
            return None

        if result == "next":
            continue

    return None


def _process_execution(topic: str) -> tuple[Iterator[LeanCanvas], GlobalState]:
    """Execute the ideation workflow."""
    ui_config = get_settings().ui
    echo(ui_config.phase_start.format(phase=Phase.IDEATION))
    echo(ui_config.researching.format(topic=topic))
    echo(ui_config.wait)

    app = create_app()
    initial_state = {"topic": topic, "phase": Phase.IDEATION}

    final_state_data = None
    for output in app.stream(initial_state, {"recursion_limit": 5, "configurable": {"thread_id": "1"}}):
        node_name = next(iter(output.keys()))
        final_state_data = output[node_name]

    if final_state_data is None:
        return iter([]), GlobalState(topic=topic)

    state_obj = GlobalState(**final_state_data) if isinstance(final_state_data, dict) else final_state_data
    generated_ideas_raw = getattr(state_obj, "generated_ideas", [])

    iterator = iter(generated_ideas_raw) if hasattr(generated_ideas_raw, "__iter__") else iter([])

    def _yield_items() -> Iterator[LeanCanvas]:
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

    return _yield_items(), state_obj


def run_simulation_mode(topic: str, selected_idea: LeanCanvas) -> None:
    """Run the simulation phase with UI."""
    initial_state = GlobalState(
        topic=topic, selected_idea=selected_idea, simulation_active=True, phase=Phase.IDEATION
    )

    app = create_simulation_graph()
    shared_state = {"current": initial_state}

    def background_task() -> None:
        try:
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

        except Exception:
            logger.exception("Simulation thread failed")

    thread = threading.Thread(target=background_task, daemon=True)
    thread.start()

    try:
        renderer = SimulationRenderer(lambda: shared_state["current"])
        renderer.start()
    finally:
        pass


def ingest_transcript(filepath: str) -> None:
    """Ingest a transcript file into the RAG engine."""
    try:
        echo(f"Ingesting transcript from {filepath}...")
        path = validate_filepath(filepath)

        with path.open(encoding="utf-8") as f:
            content = f.read()

        rag = RAG()
        rag.ingest_text(content, source=str(path))
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

        topic = validate_topic(topic)

        typed_ideas_gen, state = _process_execution(topic)
        selected_idea = browse_and_select(typed_ideas_gen)

        if selected_idea:
            echo(ui_config.selected.format(title=selected_idea.title))
            # Mutate state with selection and resume Graph
            # Resume execution with the selected idea
            try:
                from langgraph.types import Command
                app = create_app()
                app.invoke(Command(resume={"selected_idea": selected_idea.model_dump()}), {"configurable": {"thread_id": "1"}})
            except Exception:
                logger.exception("Failed to resume graph")
            run_simulation_mode(topic, selected_idea)

    except Exception as e:
        logger.exception("Application execution failed")
        echo(ui_config.execution_error.format(e=e))


if __name__ == "__main__":
    main()
