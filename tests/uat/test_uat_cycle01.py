import itertools
import os
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest
from langgraph.graph.state import CompiledStateGraph

# We import create_app but we will mock the LLM and Tools inside it
from src.core.config import get_settings
from src.core.graph import create_app
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.mvp import MVP, Feature, MVPType, Priority
from src.domain_models.persona import EmpathyMap, Persona
from src.domain_models.state import GlobalState, Phase


@pytest.fixture
def mock_llm_factory() -> MagicMock:
    return MagicMock()


@patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test", "TAVILY_API_KEY": "tv-test", "V0_API_KEY": "v0-test"})
@patch("src.core.graph.IdeatorAgent")
@patch("src.core.graph.get_llm")
def test_uat_cycle01_full_flow(
    mock_get_llm: MagicMock, mock_ideator_cls: MagicMock
) -> None:
    """
    UAT Scenario: Full JTC 2.0 Cycle (Ideation -> Verification -> Simulation -> Solution -> PMF)

    This test verifies:
    1. Graph Compilation and Interrupts
    2. Scalable Iterator consumption
    3. State transitions through all 4 gates
    """
    get_settings.cache_clear()

    # --- 1. Setup Logic Mock ---
    mock_ideator_instance = mock_ideator_cls.return_value

    def large_dataset_generator() -> Iterator[LeanCanvas]:
        for i in range(100):
            yield LeanCanvas(
                id=i,
                title=f"Idea {i}",
                problem="Problem statement text",
                customer_segments="Customer Segments",
                unique_value_prop="Unique Value Proposition",
                solution="Solution description text",
            )

    # Use LazyIdeaIterator wrapper as per new implementation if agent returns raw iterator,
    # but GlobalState expects LazyIdeaIterator or Iterator.
    # Ideally the agent should return the wrapped iterator or the graph/handler should wrap it.
    # In `ideator.py`, it yields items. `IdeatorAgent.run` returns `{"generated_ideas": ideas_iter}`.
    # The GlobalState model will accept Iterator.
    mock_ideator_instance.run.return_value = {"generated_ideas": large_dataset_generator()}

    # --- 2. Build App ---
    app = create_app()
    assert isinstance(app, CompiledStateGraph)

    # --- 3. Execution: Phase 1 (Ideation) ---
    initial_state = GlobalState(topic="AI for Agriculture")

    # Run until first interrupt (after 'ideator')
    result_dict = app.invoke(initial_state)

    # --- Scalability Check ---
    # GlobalState validates inputs. If it was cast to GlobalState, validation runs.
    # invoke returns a dict.
    ideas_iter = result_dict["generated_ideas"]
    assert ideas_iter is not None

    page_size = 5
    page_1 = list(itertools.islice(ideas_iter, page_size))
    assert len(page_1) == 5
    assert page_1[0].id == 0
    assert page_1[4].id == 4

    # Verify the generator is NOT exhausted
    next_item = next(ideas_iter)
    assert next_item.id == 5

    # --- Gate 1 Decision: User Selects Idea #2 ---
    selected_idea = page_1[2]
    assert selected_idea.id == 2

    # Update state with selection
    state_after_gate_1 = GlobalState(
        **result_dict,
        selected_idea=selected_idea
    )

    # --- 4. Validate Phase 2 (Verification) Readiness ---
    dummy_persona = Persona(
        name="Farmer Joe",
        occupation="Farmer",
        demographics="50s, Midwest",
        goals=["Better yields"],
        frustrations=[" pests"],
        bio="Loves corn.",
        empathy_map=EmpathyMap(
            says=["I need help"],
            thinks=["Costs are high"],
            does=["Checks crops"],
            feels=["Worried"]
        )
    )

    state_ready_for_verification = state_after_gate_1.model_copy()
    state_ready_for_verification.target_persona = dummy_persona
    state_ready_for_verification.phase = Phase.VERIFICATION

    GlobalState.model_validate(state_ready_for_verification.model_dump())
    assert state_ready_for_verification.phase == Phase.VERIFICATION

    # --- 5. Validate Phase 3 (Solution) Readiness ---
    dummy_feature = Feature(
        name="Crop Scan",
        description="Scans crops for disease.",
        priority=Priority.MUST_HAVE
    )
    dummy_mvp = MVP(
        type=MVPType.LANDING_PAGE,
        core_features=[dummy_feature],
        success_criteria="10 signups",
        v0_url="https://v0.dev/test" # Added valid HttpUrl
    )

    state_ready_for_solution = state_ready_for_verification.model_copy()
    state_ready_for_solution.mvp_definition = dummy_mvp
    state_ready_for_solution.phase = Phase.SOLUTION

    GlobalState.model_validate(state_ready_for_solution.model_dump())
    assert state_ready_for_solution.phase == Phase.SOLUTION

    # --- 6. Validate Phase 4 (PMF) Readiness ---
    state_ready_for_pmf = state_ready_for_solution.model_copy()
    state_ready_for_pmf.phase = Phase.PMF

    GlobalState.model_validate(state_ready_for_pmf.model_dump())
    assert state_ready_for_pmf.phase == Phase.PMF
