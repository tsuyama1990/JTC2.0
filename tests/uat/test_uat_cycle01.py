import itertools
import os
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest

# We import create_app but we will mock the LLM and Tools inside it
from src.core.graph import create_app
from src.domain_models.common import LazyIdeaIterator
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.mvp import MVP, Feature, MVPType, Priority
from src.domain_models.persona import EmpathyMap, Persona
from src.domain_models.state import GlobalState, Phase
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
                status="draft",
                title=f"Idea {i}",
                problem="Problem statement text",
                customer_segments="Customer Segments",
                unique_value_prop="Unique Value Proposition",
                solution="Solution description text",
            )

    return _gen()


def test_ideation_scalability(limited_lean_canvas_generator: Iterator[LeanCanvas]) -> None: # noqa: PLR0915
    """
    Verify that the Ideation phase handles large/infinite iterators safely
    by consuming only what is needed (pagination).
    """
    from src.core.config import clear_settings_cache

    clear_settings_cache()
    os.environ.update(DUMMY_ENV_VARS)

    mock_ideator_instance = MagicMock()
    # Return wrapped iterator as expected by strict validation
    mock_ideator_instance.run.return_value = {
        "generated_ideas": LazyIdeaIterator(limited_lean_canvas_generator)
    }

    import src.core.nodes
    from src.core.factory import AgentFactory
    from src.core.workflow_builder import node_registry

    # Quick fix for test specifically: ensure node is registered for test
    if "ideator" not in node_registry.nodes:
        # Mock factory
        factory = MagicMock(spec=AgentFactory)
        factory.get_ideator_agent.return_value = mock_ideator_instance
        from src.core.config import Settings
        mock_settings = MagicMock(spec=Settings)
        node_registry.nodes["ideator"] = src.core.nodes.make_ideator_node(factory.get_ideator_agent(), mock_settings)

        # Provide a mock for persona as well to avoid undefined node error during build
        if "persona" not in node_registry.nodes:
            node_registry.nodes["persona"] = MagicMock()
        if "verification" not in node_registry.nodes:
            node_registry.nodes["verification"] = MagicMock()
        if "alternative_analysis" not in node_registry.nodes:
            node_registry.nodes["alternative_analysis"] = MagicMock()
        if "vpc" not in node_registry.nodes:
            node_registry.nodes["vpc"] = MagicMock()
        if "transcript_ingestion" not in node_registry.nodes:
            node_registry.nodes["transcript_ingestion"] = MagicMock()
        if "mental_model_journey" not in node_registry.nodes:
            node_registry.nodes["mental_model_journey"] = MagicMock()
        if "sitemap_wireframe" not in node_registry.nodes:
            node_registry.nodes["sitemap_wireframe"] = MagicMock()
        if "virtual_customer" not in node_registry.nodes:
            node_registry.nodes["virtual_customer"] = MagicMock()
        if "simulation_round" not in node_registry.nodes:
            node_registry.nodes["simulation_round"] = MagicMock()
        if "review_3h" not in node_registry.nodes:
            node_registry.nodes["review_3h"] = MagicMock()
        if "spec_generation" not in node_registry.nodes:
            node_registry.nodes["spec_generation"] = MagicMock()
        if "experiment_planning" not in node_registry.nodes:
            node_registry.nodes["experiment_planning"] = MagicMock()
        if "governance" not in node_registry.nodes:
            node_registry.nodes["governance"] = MagicMock()

    app = create_app(registry=node_registry, settings=mock_settings)
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


def test_gate_transitions_data_integrity() -> None:
    """
    Verify that state transitions through gates maintain data integrity
    and validation rules hold.
    """
    from src.core.config import clear_settings_cache

    clear_settings_cache()
    os.environ.update(DUMMY_ENV_VARS)

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
        bio="Test Bio long enough",
        empathy_map=EmpathyMap(says=["Hi this is long enough"], thinks=["Logic is sound here"], does=["Code a lot of code"], feels=["Good about this plan"]),
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
        success_criteria="Criteria long enough to pass",
    )

    state_ready_for_solution = state_ready_for_verification.model_copy()
    state_ready_for_solution.mvp_definition = dummy_mvp
    state_ready_for_solution.phase = Phase.SOLUTION

    GlobalState.model_validate(state_ready_for_solution.model_dump())

    # 3. Validate Transition to PMF
    state_ready_for_pmf = state_ready_for_solution.model_copy()
    state_ready_for_pmf.phase = Phase.PMF

    GlobalState.model_validate(state_ready_for_pmf.model_dump())


@patch.dict(os.environ, DUMMY_ENV_VARS)
def test_large_dataset_iterator_safety() -> None:
    from src.core.config import get_settings
    get_settings().resiliency.iterator_safety_limit = 5
    def infinite_generator() -> Iterator[LeanCanvas]:
        """Yields infinite sequence."""
        i = 0
        while True:
            yield LeanCanvas(
                id=i,
                status="draft",
                title=f"Idea {i}",
                problem="Problem text is long enough",
                customer_segments="Segments text is long enough",
                unique_value_prop="UVP text is long enough",
                solution="Solution text is long enough",
            )
            i += 1

    # Wrap infinite gen
    lazy_iter = LazyIdeaIterator(infinite_generator())

    # Consume a large chunk but finite
    chunk_size = 5
    chunk = list(itertools.islice(lazy_iter, chunk_size))

    assert len(chunk) == 5
    assert chunk[-1].id == 4

    # Ensure next is still valid (state preserved)
