import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def __():
    import os
    import threading

    import marimo as mo

    # Import core components
    from src.core.graph import create_app
    from src.core.simulation import create_simulation_graph
    from src.domain_models.lean_canvas import LeanCanvas
    from src.domain_models.state import GlobalState, Phase
    from src.ui.renderer import SimulationRenderer

    # Helper function to run the simulation asynchronously so Marimo is not blocked
    def run_simulation(topic, canvas):
        initial_state = GlobalState(
            topic=topic, selected_idea=canvas, simulation_active=True, phase=Phase.IDEATION
        )
        sim_app = create_simulation_graph()
        shared_state = {"current": initial_state}

        def bg_task():
            for update in sim_app.stream(initial_state, stream_mode="values"):
                if isinstance(update, dict):
                    shared_state["current"] = GlobalState(**update)
                elif isinstance(update, GlobalState):
                    shared_state["current"] = update

        threading.Thread(target=bg_task, daemon=True).start()

        # Start headless renderer to prevent X11 crashes in test env
        os.environ["HEADLESS_MODE"] = "true"
        renderer = SimulationRenderer(lambda: shared_state["current"])
        renderer.start()

    return (
        run_simulation,
        mo,
        os,
        threading,
        create_app,
        create_simulation_graph,
        GlobalState,
        Phase,
        LeanCanvas,
        SimulationRenderer,
    )


@app.cell
def __(run_simulation, mo, GlobalState, Phase, LeanCanvas, create_app, os):
    mo.md("# JTC 2.0 User Acceptance Test / Tutorial")


@app.cell
def __(run_simulation, mo, GlobalState, Phase, LeanCanvas, create_app, os):
    os.environ["MOCK_MODE"] = "true"

    mock_canvas = LeanCanvas(
        id=1,
        title="AI for Plumbers",
        problem="Scheduling is hard",
        customer_segments="Independent Plumbers",
        unique_value_prop="Automated Scheduling",
        solution="AI Assistant",
    )

    topic = "AI for Plumbers"
    mo.md(f"**Mock Mode**: Simulating workflow for '{topic}'")
    return mock_canvas, topic


@app.cell
def __(run_simulation, mock_canvas, topic, mo):
    mo.md("## Starting Simulation")

    # Execute simulation in headless mode
    run_simulation(topic, mock_canvas)

    mo.md("Simulation completed successfully in Mock Mode.")


if __name__ == "__main__":
    app.run()
