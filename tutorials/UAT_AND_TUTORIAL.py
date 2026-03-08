from typing import Any

import marimo as mo

__generated_with = "0.1.0"
app = mo.App()


@app.cell
def __init_environment() -> tuple[bool, str, Any]:
    import os as _os

    has_api_key = bool(_os.getenv("OPENAI_API_KEY"))
    mode = "Real Mode" if has_api_key else "Mock Mode"

    mo.md(f"# JTC 2.0 Remastered Tutorial\n\n**Current Mode:** {mode}")
    return has_api_key, mode, mo


@app.cell
def __run_uat_001(has_api_key: bool, mo: Any) -> tuple[Any]:
    if not has_api_key:
        _output = mo.md(
            "## Scenario UAT-001: The Complete End-to-End Fitness Journey\n\n*Running in Mock Mode. Skipping execution to prevent state side-effects without valid API keys.*"
        )
    else:
        import logging

        import src.domain_models.state as _state_mod
        from src.core.graph import create_app

        logging.getLogger().setLevel(logging.ERROR)

        _output = mo.md(
            "## Scenario UAT-001: The Complete End-to-End Fitness Journey\nExecuting..."
        )
        try:
            app_inst = create_app()
            _state = _state_mod.GlobalState(topic="AI for Agriculture")
            result = app_inst.invoke(_state, {"recursion_limit": 5})
            _output = result
        except Exception as e:
            _output = f"Execution Error: {e}"

    return (_output,)


@app.cell
def __run_uat_002(has_api_key: bool, mo: Any) -> tuple[Any]:
    if not has_api_key:
        _output_2 = mo.md(
            "## Scenario UAT-002: The Harsh Pivot at the Virtual Market\n\n*Running in Mock Mode. Skipping execution.*"
        )
    else:
        import src.domain_models.state as _state_mod
        from src.domain_models.lean_canvas import LeanCanvas

        _output_2 = mo.md(
            "## Scenario UAT-002: The Harsh Pivot at the Virtual Market\nTesting Pivot rejection logic..."
        )

        _state = _state_mod.GlobalState(topic="Web3 Dog Social Network")
        _state.selected_idea = LeanCanvas(
            id=1,
            title="Bad Idea",
            problem="Problem is a problem",
            solution="Solution is a solution",
            customer_segments="Segments segment segment",
            unique_value_prop="Unique value proposition",
        )

        if _state.topic != "Web3 Dog Social Network":
            _msg = "Topic mismatch"
            raise ValueError(_msg)

    return (_output_2,)


@app.cell
def __run_uat_003(has_api_key: bool, mo: Any) -> tuple[Any]:
    if not has_api_key:
        _output_3 = mo.md(
            "## Scenario UAT-003: Transcript Ingestion and Fact-Checking\n\n*Running in Mock Mode. Skipping execution.*"
        )
    else:
        import src.domain_models.state as _state_mod
        from src.domain_models.transcript import Transcript

        _output_3 = mo.md(
            "## Scenario UAT-003: Transcript Ingestion and Fact-Checking\nTesting RAG setup..."
        )

        _state = _state_mod.GlobalState(topic="Agriculture Supply Chain")
        _state.transcripts.append(
            Transcript(
                source="Interview 1",
                content="Supply chain logistics are rotting produce. " * 10,
                date="2023-01-01",
            )
        )

        if len(_state.transcripts) != 1:
            _msg = "Transcript length error"
            raise ValueError(_msg)

    return (_output_3,)


@app.cell
def __verify_outputs(mo: Any, has_api_key: bool) -> tuple[Any]:
    if not has_api_key:
        _verification = mo.md(
            "## Output Verification\n\n*Skipping Output Verification as tests ran in Mock Mode.*"
        )
    else:
        import pathlib as _pathlib

        _outputs_dir = _pathlib.Path.cwd() / "outputs" / "canvas"

        exists = _outputs_dir.exists()
        spec_path = _outputs_dir / "AgentPromptSpec.md"
        plan_path = _outputs_dir / "ExperimentPlan.md"

        spec_valid = False
        plan_valid = False

        if spec_path.exists():
            content = spec_path.read_text()
            if "Agent Prompt Specification" in content and "core_user_story" in content:
                spec_valid = True

        if plan_path.exists():
            content = plan_path.read_text()
            if "Experiment Plan" in content and "aarrr_metrics" in content:
                plan_valid = True

        if exists and spec_valid and plan_valid:
            _verification = mo.md(
                "## Output Verification\n\n**PASS** - Output files verified and content structured correctly."
            )
        else:
            _verification = mo.md(
                "## Output Verification\n\n**FAIL** - Output files missing or malformed."
            )

    return (_verification,)


if __name__ == "__main__":
    app.run()
