import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def __():
    import logging
    import os
    import threading
    import time

    import marimo as mo

    logger = logging.getLogger(__name__)

    try:
        from src.core.config import get_settings
        from src.core.graph import create_app
        from src.core.simulation import create_simulation_graph
        from src.domain_models.lean_canvas import LeanCanvas
        from src.domain_models.state import GlobalState, Phase
        from src.ui.renderer import SimulationRenderer
    except ImportError as e:
        mo.md(f"**Error**: Missing required dependencies. {e}")
        raise

    class TutorialContext:
        def __init__(self) -> None:
            self.mo = mo
            self.os = os
            self.get_settings = get_settings
            self.create_app = create_app
            self.create_simulation_graph = create_simulation_graph
            self.GlobalState = GlobalState
            self.Phase = Phase
            self.LeanCanvas = LeanCanvas
            self.SimulationRenderer = SimulationRenderer

        def run_simulation(self, topic: str, canvas: LeanCanvas) -> None:
            initial_state = self.GlobalState(
                topic=topic, selected_idea=canvas, simulation_active=True, phase=self.Phase.IDEATION
            )
            sim_app = self.create_simulation_graph()
            shared_state = {"current": initial_state}

            error_event = threading.Event()

            def bg_task():
                try:
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

            # Wait briefly to ensure thread starts successfully
            time.sleep(0.5)

            if error_event.is_set():
                msg = "Simulation background task failed to start or crashed."
                raise RuntimeError(msg)

            # Start headless renderer to prevent X11 crashes in test env
            self.os.environ["HEADLESS_MODE"] = "true"
            renderer = self.SimulationRenderer(lambda: shared_state["current"])

            try:
                # Add a timeout for the UI loop if needed, but renderer blocks until complete.
                renderer.start()
            finally:
                # Give thread a chance to wind down
                thread.join(timeout=2.0)

    ctx = TutorialContext()
    return (ctx,)


@app.cell
def __(ctx):
    ctx.mo.md("# JTC 2.0 User Acceptance Test / Tutorial")


@app.cell
def __(ctx):
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

    topic = mock_canvas.title
    result_md = ctx.mo.md(f"**Mock Mode**: Simulating workflow for '{topic}'")
    return mock_canvas, topic, result_md


@app.cell
def __(ctx, mock_canvas, topic):
    ctx.mo.md("## Starting Simulation")

    # Execute simulation in headless mode
    ctx.run_simulation(topic, mock_canvas)

    final_md = ctx.mo.md("Simulation completed successfully in Mock Mode.")
    return (final_md,)


if __name__ == "__main__":
    try:
        app.run()
    except Exception:
        import logging
        import sys

        logging.exception("Failed to run Marimo notebook.")
        sys.exit(1)
