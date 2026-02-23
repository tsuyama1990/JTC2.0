import itertools
import os
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest

# We import create_app but we will mock the LLM and Tools inside it
from src.core.config import get_settings
from src.core.graph import create_app
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.mvp import MVP, Feature, MVPType, Priority
from src.domain_models.persona import EmpathyMap, Persona
from src.domain_models.state import GlobalState, LazyIdeaIterator, Phase
from tests.conftest import DUMMY_ENV_VARS


@pytest.fixture
def mock_llm_factory() -> MagicMock:
    return MagicMock()


@pytest.fixture
def limited_lean_canvas_generator() -> Iterator[LeanCanvas]:
    """Yields a limited sequence of LeanCanvas objects on demand."""

    def _gen() -> Iterator[LeanCanvas]:
        for i in range(20):
            yield LeanCanvas(
                id=i,
                title=f"Idea {i}",
                problem="Problem statement text",
                customer_segments="Customer Segments",
                unique_value_prop="Unique Value Proposition",
                solution="Solution description text",
            )

    return _gen()


@patch.dict(os.environ, DUMMY_ENV_VARS)
@patch("src.core.factory.IdeatorAgent")
@patch("src.core.factory.get_llm")
def test_ideation_scalability(
    mock_get_llm: MagicMock,
    mock_ideator_cls: MagicMock,
    limited_lean_canvas_generator: Iterator[LeanCanvas],
) -> None:
    """
    Verify that the Ideation phase handles large/infinite iterators safely
    by consuming only what is needed (pagination).
    """
    get_settings.cache_clear()

    mock_ideator_instance = mock_ideator_cls.return_value
    # Return wrapped iterator as expected by strict validation
    mock_ideator_instance.run.return_value = {
        "generated_ideas": LazyIdeaIterator(limited_lean_canvas_generator)
    }

    app = create_app()
    initial_state = GlobalState(topic="AI for Scalability")

    # Run to Ideation interrupt
    result_dict = app.invoke(initial_state)

    ideas_iter = result_dict["generated_ideas"]
    assert isinstance(ideas_iter, LazyIdeaIterator)

    # Verify consumption logic (paging)
    page_size = 5
    page_1 = list(itertools.islice(ideas_iter, page_size))

    assert len(page_1) == 5
    assert page_1[0].id == 0
    assert page_1[4].id == 4

    # Check that we can continue consuming (it wasn't exhausted or closed)
    next_item = next(ideas_iter)
    assert next_item.id == 5


@patch.dict(os.environ, DUMMY_ENV_VARS)
@patch("src.core.factory.IdeatorAgent")
@patch("src.core.factory.get_llm")
def test_gate_transitions_data_integrity(
    mock_get_llm: MagicMock, mock_ideator_cls: MagicMock
) -> None:
    """
    Verify that state transitions through gates maintain data integrity
    and validation rules hold.
    """
    get_settings.cache_clear()

    # Setup initial state simulating post-Ideation (Gate 1 passed)
    # We construct a valid state manually as if we just picked an idea.
    selected_idea = LeanCanvas(
        id=1,
        title="Selected Idea",
        problem="Problem statement text",
        customer_segments="Customer Segments",
        unique_value_prop="Unique Value Proposition",
        solution="Solution description text",
    )

    state_after_gate_1 = GlobalState(
        topic="AI Integrity",
        generated_ideas=None,  # Consumed or irrelevant for next phase
        selected_idea=selected_idea,
    )

    # 1. Validate Transition to Verification
    dummy_persona = Persona(
        name="Valid Persona",
        occupation="Tester",
        demographics="Data Center Worker",
        goals=["Pass tests"],
        frustrations=["Failures"],
        bio="Test Bio",
        empathy_map=EmpathyMap(says=["Hi"], thinks=["Logic"], does=["Code"], feels=["Good"]),
    )

    state_ready_for_verification = state_after_gate_1.model_copy()
    state_ready_for_verification.target_persona = dummy_persona
    state_ready_for_verification.phase = Phase.VERIFICATION

    # Should pass
    GlobalState.model_validate(state_ready_for_verification.model_dump())

    # 2. Validate Transition to Solution
    dummy_mvp = MVP(
        type=MVPType.LANDING_PAGE,
        core_features=[
            Feature(name="Feature1", description="Description", priority=Priority.MUST_HAVE)
        ],
        success_criteria="Criteria",
        v0_url="https://v0.dev/test",
    )

    state_ready_for_solution = state_ready_for_verification.model_copy()
    state_ready_for_solution.mvp_definition = dummy_mvp
    state_ready_for_solution.phase = Phase.SOLUTION

    GlobalState.model_validate(state_ready_for_solution.model_dump())

    # 3. Validate Transition to PMF
    state_ready_for_pmf = state_ready_for_solution.model_copy()
    state_ready_for_pmf.phase = Phase.PMF

    GlobalState.model_validate(state_ready_for_pmf.model_dump())
