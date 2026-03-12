import marimo

__generated_with = "0.20.4"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    return mo,


@app.cell
def _(mo):
    mo.md(
        """
        # Welcome to JTC 2.0 (Remastered)

        **The JTC 2.0 (Remastered Edition)** is an autonomous, multi-agent simulation platform designed to bridge the gap between "Startup Science" and the realities of Traditional Japanese Companies (JTCs).
        It acts as an interactive, role-playing co-founder, putting your ideas through rigorous "Gekizume" (harsh feedback) by AI stakeholders, validating them against real customer data via RAG, and ultimately outputting perfectly structured requirements designed for any autonomous AI coding agent.
        """
    )


@app.cell
def _(mo):
    mo.md(
        """
        ## Environment Setup

        Ensure you have Python 3.12+ and `uv` installed. The required dependencies will be downloaded automatically by `uv`.
        """
    )


@app.cell
def _(mo):
    import subprocess
    import sys

    python_version = sys.version
    try:
        uv_version = subprocess.check_output(["/usr/local/bin/uv", "--version"]).decode("utf-8").strip()
    except Exception:
        uv_version = "Not found"

    mo.md(
        f"""
        **System Info:**
        - Python Version: `{python_version}`
        - UV Version: `{uv_version}`
        """
    )


@app.cell
def _(mo):
    mo.md(
        """
        ## Scenario 1: The Fast-Track (Mock Mode Execution)

        Let's run the system in "Mock Mode". This allows you to experience the entire workflow and see the final PDF/Markdown outputs instantly without needing API keys or incurring costs.
        """
    )


@app.cell
def _():
    import os
    import secrets

    # Enable Mock Mode
    os.environ['MOCK_MODE'] = 'true'
    os.environ['OPENAI_API_KEY'] = f"sk-mock-{secrets.token_hex(24)}"
    os.environ['TAVILY_API_KEY'] = f"tvly-mock-{secrets.token_hex(16)}"
    os.environ['LLM_MODEL'] = 'gpt-4o-mini'
    return os,


@app.cell
def _(mo, os, sys):
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.core.config import get_settings
    from src.core.graph import create_app

    # Configure graph
    app_graph = create_app()

    inputs = {
        "topic": "AI for remote team building"
    }
    config = {"configurable": {"thread_id": "tutorial_mock_1"}}

    mo.md("Initializing Simulation Graph in Mock Mode...")
    return app_graph, config, get_settings, inputs


@app.cell
def _(app_graph, config, inputs, mo, os):
    is_mock = os.getenv("MOCK_MODE", "false").lower() == "true"
    final_state = None

    if is_mock:
        # Mock Mode bypasses actual graph logic for strict determinism in tutorial

        from src.core.factory import ServiceFactory
        from src.domain_models.agent_prompt_spec import AgentPromptSpec, StateMachine
        from src.domain_models.experiment_plan import ExperimentPlan, MetricTarget
        from src.domain_models.sitemap_and_story import UserStory
        from src.domain_models.state import GlobalState

        fs = ServiceFactory.get_file_service()

        mock_spec = AgentPromptSpec(
            sitemap="Mock Sitemap",
            routing_and_constraints="Mock Routing",
            core_user_story=UserStory(as_a="Mock", i_want_to="Mock", so_that="Mock", acceptance_criteria=["Mock"], target_route="/mock"),
            state_machine=StateMachine(success="Mock", loading="Mock", error="Mock", empty="Mock"),
            validation_rules="Mock Rules",
            mermaid_flowchart="graph TD;\nA-->B;"
        )

        mock_plan = ExperimentPlan(
            riskiest_assumption="Mock Assumption",
            experiment_type="Mock Type",
            acquisition_channel="Mock Channel",
            aarrr_metrics=[MetricTarget(metric_name="Acquisition", target_value="100", measurement_method="Google Analytics")],
            pivot_condition="If we fail."
        )

        # We manually use the private formatter functions since we bypassed the nodes
        from pathlib import Path as _Path

        from src.agents.builder import BuilderAgent
        from src.core.llm import get_llm

        builder = BuilderAgent(llm=get_llm(), file_service=fs)
        spec_md = builder._format_agent_prompt_spec_to_md(mock_spec)
        plan_md = builder._format_experiment_plan_to_md(mock_plan)

        # In mock mode for the tutorial, write to outputs directory correctly
        from src.core.config import get_settings
        out_dir = _Path.cwd() / get_settings().canvas_output_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "AgentPromptSpec.md").write_text(spec_md)
        (out_dir / "EXPERIMENT_PLAN.md").write_text(plan_md)

        final_state = GlobalState(topic=inputs["topic"], agent_prompt_spec=mock_spec, experiment_plan=mock_plan)
    else:
        # Run graph execution normally
        for state in app_graph.stream(inputs, config=config):
            final_state = state

    mo.md("Mock Simulation Completed!")
    return final_state, state


@app.cell
def _(mo, os):
    import time
    from pathlib import Path as _Path
    # Sleep shortly to allow ThreadPool async writes to finish
    time.sleep(0.5)

    from src.core.config import get_settings
    out_dir = _Path.cwd() / get_settings().canvas_output_dir
    # Read the generated Markdown outputs
    spec_path = out_dir / "AgentPromptSpec.md"
    plan_path = out_dir / "EXPERIMENT_PLAN.md"

    spec_content = "File not generated."
    spec_p = spec_path
    if spec_p.exists():
        with spec_p.open() as f:
            spec_content = f.read()

    plan_content = "File not generated."
    plan_p = _Path(plan_path)
    if plan_p.exists():
        with plan_p.open() as f:
            plan_content = f.read()

    mo.md(
        f"""
        ### Generated Artifacts

        #### AgentPromptSpec.md
        ```markdown
        {spec_content}
        ```

        #### EXPERIMENT_PLAN.md
        ```markdown
        {plan_content}
        ```
        """
    )
    return plan_content, plan_path, spec_content, spec_path


@app.cell
def _(mo):
    mo.md(
        """
        ## Scenario 2: The Real Deal (Connecting to the APIs)

        To run in Real Mode, set up your `.env` file with `OPENAI_API_KEY` and `TAVILY_API_KEY`.
        """
    )


@app.cell
def _(mo, os):
    # Instructions for real mode
    if 'MOCK_MODE' in os.environ:
        del os.environ['MOCK_MODE']

    mo.md("Disabled Mock Mode. (Make sure you have valid `.env` configuration for `OPENAI_API_KEY` to run this)")


@app.cell
def _(mo):
    mo.md(
        """
        ## Scenario 3: Grounding in Reality (RAG Demonstration)

        The CPO agent will check the logic against actual customer interviews using RAG.
        """
    )


@app.cell
def _():
    import pathlib

    # Create sample dummy interview
    pathlib.Path("sample_interview.txt").write_text("User: I hate typing my goals out manually. It wastes so much time.")
    return pathlib,


@app.cell
def _(mo):
    mo.md("Generated `sample_interview.txt`. The RAG engine will use this to ground validations.")


@app.cell
def _(mo):
    mo.md(
        """
        ## Reviewing the Outputs

        Once completed, high-resolution PDFs will be saved in your `/outputs/canvas/` directory.
        Use the `AgentPromptSpec.md` with tools like Cursor, Windsurf, or v0.dev to generate UI automatically.
        """
    )


if __name__ == "__main__":
    app.run()
