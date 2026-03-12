import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def __():  # type: ignore[no-redef]
    import logging
    import os
    import sys
    import threading
    import time
    from pathlib import Path

    import marimo as mo

    # Ensure project root is in path for imports to work
    project_root = str(Path(__file__).parent.parent.resolve())
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    logger = logging.getLogger(__name__)

    try:
        from src.core.config import get_settings
        from src.core.graph import create_app
        from src.core.simulation import create_simulation_graph
        from src.domain_models.lean_canvas import LeanCanvas
        from src.domain_models.state import GlobalState, Phase
        from src.ui.renderer import SimulationRenderer
        IMPORTS_SUCCESSFUL = True
        IMPORT_ERROR = ""
    except ImportError as e:
        IMPORTS_SUCCESSFUL = False
        IMPORT_ERROR = (
            f"Failed to import src modules. Did you run `uv sync`?\n"
            f"Error details: {e}\n"
            "Will proceed in Mock Fallback mode."
        )
        logger.warning(IMPORT_ERROR)

    class TutorialContext:
        def __init__(self) -> None:
            self.mo = mo
            self.os = os

            if IMPORTS_SUCCESSFUL:
                self.get_settings = get_settings
                self.create_app = create_app
                self.create_simulation_graph = create_simulation_graph
                self.GlobalState = GlobalState
                self.Phase = Phase
                self.LeanCanvas = LeanCanvas
                self.SimulationRenderer = SimulationRenderer
                self.is_mocked = False
            else:
                self._setup_mocks()

        def _setup_mocks(self) -> None:
            from unittest.mock import MagicMock
            self.get_settings = MagicMock()
            self.create_app = MagicMock()
            self.create_simulation_graph = MagicMock()
            self.GlobalState = MagicMock()
            self.Phase = MagicMock()
            self.LeanCanvas = MagicMock()
            self.SimulationRenderer = MagicMock()
            self.is_mocked = True

        def run_simulation(self, topic: str, canvas: 'LeanCanvas') -> None:
            if self.is_mocked:
                self.mo.md(f"**Warning**: Running mock simulation due to import failure: {IMPORT_ERROR}")
                time.sleep(1)
                return

            initial_state = self.GlobalState(
                topic=topic, selected_idea=canvas, simulation_active=True, phase=self.Phase.IDEATION
            )
            sim_app = self.create_simulation_graph()

            if not hasattr(sim_app, 'stream'):
                msg = "create_simulation_graph did not return a valid LangGraph object."
                raise RuntimeError(msg)

            shared_state = {"current": initial_state}

            error_event = threading.Event()
            ready_event = threading.Event()

            def bg_task():
                try:
                    # Signal that the thread has successfully started execution
                    ready_event.set()
                    for update in sim_app.stream(initial_state, stream_mode="values"):
                        if isinstance(update, dict):
                            shared_state["current"] = self.GlobalState(**update)
                        elif isinstance(update, self.GlobalState):
                            shared_state["current"] = update
                except Exception:
                    logger.exception("Simulation failed.")
                    error_event.set()

            thread = threading.Thread(target=bg_task, daemon=True)
            thread.start()

            # Synchronize thread startup
            ready_event.wait(timeout=2.0)

            if error_event.is_set():
                msg = "Simulation background task failed to start or crashed."
                raise RuntimeError(msg)

            # Start headless renderer to prevent X11 crashes in test env
            old_headless = self.os.environ.get("HEADLESS_MODE")
            self.os.environ["HEADLESS_MODE"] = "true"

            try:
                renderer = self.SimulationRenderer(lambda: shared_state["current"])
                # Add a timeout for the UI loop if needed, but renderer blocks until complete.
                renderer.start()
            finally:
                if old_headless is not None:
                    self.os.environ["HEADLESS_MODE"] = old_headless
                else:
                    self.os.environ.pop("HEADLESS_MODE", None)

                # Give thread a chance to wind down
                thread.join(timeout=2.0)

    ctx = TutorialContext()
    return (ctx,)


@app.cell
def __(ctx):  # type: ignore[no-redef]
    ctx.mo.md("# JTC 2.0 User Acceptance Test / Tutorial")


@app.cell
def __(ctx):  # type: ignore[no-redef]
    ctx.os.environ["MOCK_MODE"] = ctx.os.getenv("MOCK_MODE", "true")

    try:
        from tests.fixtures.mock_data import get_mock_canvas

        mock_canvas = get_mock_canvas()
    except ImportError:
        # Fallback if tests module is not in path for some reason during pure tutorial execution
        mock_canvas = ctx.LeanCanvas(
            id=1,
            title="AI for Plumbers",
            problem="Scheduling is hard",
            customer_segments="Independent Plumbers",
            unique_value_prop="Automated Scheduling",
            solution="AI Assistant",
        )

    topic = mock_canvas.title.strip() if mock_canvas.title else "Generic Startup Idea"
    result_md = ctx.mo.md(f"**Mock Mode**: Simulating workflow for '{topic}'")
    return mock_canvas, topic, result_md


@app.cell
def __(ctx, mock_canvas, topic):  # type: ignore[no-redef]
    ctx.mo.md("## Starting Simulation")

    # Execute simulation in headless mode
    ctx.run_simulation(topic, mock_canvas)

    final_md = ctx.mo.md("Simulation completed successfully in Mock Mode.")
    return (final_md,)


if __name__ == "__main__":
    try:
        app.run()
    except ImportError as e:
        import sys
        print(f"Missing marimo or core dependency: {e}", file=sys.stderr)
        print("Please ensure you have installed dependencies with `uv sync`.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        import sys
        print(f"Failed to run Marimo notebook: {e}", file=sys.stderr)
        sys.exit(1)
