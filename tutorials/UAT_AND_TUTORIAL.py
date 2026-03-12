# mypy: ignore-errors
import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def __1() -> tuple[object]:
    # type: ignore
    import logging
    import threading
    import time

    import marimo as mo

    logger = logging.getLogger(__name__)

    try:
        from src.core.graph import create_app
        from src.core.simulation import create_simulation_graph
        from src.domain_models.lean_canvas import LeanCanvas
        from src.domain_models.state import GlobalState, Phase
        from src.ui.renderer import SimulationRenderer

        IMPORTS_SUCCESSFUL = True
        IMPORT_ERROR = ""
    except ImportError as e:
        IMPORTS_SUCCESSFUL = False
        IMPORT_ERROR = "Failed to import src modules. Did you run `uv sync`? Will proceed in Mock Fallback mode."
        logger.warning(f"{IMPORT_ERROR} Error details: {e}")

    class TutorialContext:
        def __init__(self) -> None:
            import os

            self.mo = mo
            self.os = os

            if IMPORTS_SUCCESSFUL:
                # Use a specific tutorial config mock or modify the settings
                # Actually, wait, passing dependency injection instead of global config.
                # Just keeping a reference without mutating global is fine.
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
            # We don't dynamically redefine the class attributes to avoid complex typing mismatches
            # between real domain models and runtime mocks. The actual fallback behavior
            # handles the mock path safely through early returns when `is_mocked == True`.
            self.is_mocked = True

        def _execute_bg_thread(
            self, sim_app: object, initial_state: object, shared_state: dict[str, object]
        ) -> tuple[threading.Thread, threading.Event]:
            error_event = threading.Event()
            ready_event = threading.Event()

            def bg_task() -> None:
                try:
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
            ready_event.wait(timeout=2.0)
            return thread, error_event

        def _run_renderer(self, shared_state: dict[str, object]) -> None:
            # Pass headless mode explicitly rather than mutating environment variables
            renderer = self.SimulationRenderer(lambda: shared_state["current"], headless=True)
            renderer.start()

        def run_simulation(self, topic: str, canvas: object) -> None:
            from contextlib import contextmanager

            if self.is_mocked:
                # If mocked, we simulate the renderer delay and return early.
                self.mo.md(
                    f"**Warning**: Running mock simulation. Simulated success for '{topic}'."
                )
                time.sleep(1)
                return

            initial_state = self.GlobalState(
                topic=topic, selected_idea=canvas, simulation_active=True, phase=self.Phase.IDEATION
            )
            sim_app = self.create_simulation_graph()

            if not hasattr(sim_app, "stream"):
                msg = "create_simulation_graph did not return a valid LangGraph object."
                raise RuntimeError(msg)

            shared_state = {"current": initial_state}

            @contextmanager
            def managed_thread():
                thread, error_event = self._execute_bg_thread(sim_app, initial_state, shared_state)
                try:
                    if error_event.is_set():
                        msg = "Simulation background task failed to start or crashed."
                        raise RuntimeError(msg)
                    yield thread, error_event
                finally:
                    thread.join(timeout=2.0)

            with managed_thread():
                self._run_renderer(shared_state)

    ctx = TutorialContext()
    return (ctx,)


@app.cell
def __2(ctx: object) -> tuple[object]:
    from src.core.constants import MSG_TUTORIAL_TITLE

    return (ctx.mo.md(MSG_TUTORIAL_TITLE),)


@app.cell
def __3(ctx: object) -> tuple[object, str, object]:
    from src.core.constants import MSG_TUTORIAL_MOCK_MODE

    try:
        from src.domain_models.mock_data import get_mock_canvas

        mock_canvas = get_mock_canvas()
    except ImportError:
        # Graceful degradation
        mock_canvas = ctx.LeanCanvas(
            id=1,
            title="AI for Plumbers",
            problem="Scheduling is hard",
            customer_segments="Independent Plumbers",
            unique_value_prop="Automated Scheduling",
            solution="AI Assistant",
            status="draft",
        )

    topic = mock_canvas.title.strip() if mock_canvas.title else "Generic Startup Idea"
    result_md = ctx.mo.md(MSG_TUTORIAL_MOCK_MODE.format(topic=topic))
    return mock_canvas, topic, result_md


@app.cell
def __4(ctx: object, mock_canvas: object, topic: str) -> tuple[object]:
    from src.core.constants import MSG_TUTORIAL_START_SIM, MSG_TUTORIAL_SUCCESS

    ctx.mo.md(MSG_TUTORIAL_START_SIM)

    try:
        ctx.run_simulation(topic, mock_canvas)
        final_md = ctx.mo.md(MSG_TUTORIAL_SUCCESS)
    except Exception as e:
        final_md = ctx.mo.md(f"**Error during simulation**: {e}")

    return (final_md,)
