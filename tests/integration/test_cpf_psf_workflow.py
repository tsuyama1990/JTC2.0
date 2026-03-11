import os
from unittest.mock import MagicMock, patch

from src.core.graph import create_app
from src.domain_models.alternative_analysis import AlternativeAnalysis, AlternativeTool
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.state import GlobalState, Phase
from tests.conftest import DUMMY_ENV_VARS


@patch.dict(os.environ, DUMMY_ENV_VARS)
@patch("src.core.factory.get_llm")
def test_full_workflow_state_mutation(mock_get_llm: MagicMock) -> None:
    """
    Test that the workflow properly mutates the expanded state
    and handles transitions properly.
    """
    _app = create_app()

    # We construct a state that starts from IDEATION
    _initial_state = GlobalState(topic="Enterprise AI", phase=Phase.IDEATION)

    _app = create_app()

    idea = LeanCanvas(
        id=1,
        title="Test Idea",
        problem="Long enough problem",
        customer_segments="Long enough segments",
        unique_value_prop="Long enough prop",
        solution="Long enough solution",
    )

    # Simulate Ideator node being executed and interrupted
    state = GlobalState(topic="Test Idea", phase=Phase.IDEATION)

    # We'll just test the state mutation and LangGraph nodes directly
    # since we want to ensure the graph connections are intact.
    from src.core.nodes import (
        alternative_analysis_node,
        persona_node,
        verification_node,
        vpc_node,
    )
    from src.domain_models.persona import EmpathyMap, Persona
    from src.domain_models.value_proposition_canvas import (
        CustomerProfile,
        ValueMap,
        ValuePropositionCanvas,
    )

    # 1. Verification
    state.selected_idea = idea
    updates = verification_node(state)
    state.phase = updates["phase"]
    assert state.phase == Phase.VERIFICATION

    # Mock LLM outputs for the following nodes
    mock_llm_instance = mock_get_llm.return_value
    mock_structured_llm = MagicMock()
    mock_llm_instance.with_structured_output.return_value = mock_structured_llm

    # 2. Persona
    mock_persona = Persona(
        name="John Doe",
        occupation="Software Engineer",
        demographics="30s, Urban",
        goals=["Build better software", "Save time"],
        frustrations=["Slow tools", "Bugs"],
        bio="Experienced software engineer looking for efficiency.",
        empathy_map=EmpathyMap(says=["A", "B"], thinks=["C", "D"], does=["E", "F"], feels=["G", "H"])
    )
    mock_structured_llm.invoke.return_value = mock_persona

    updates = persona_node(state)
    assert "target_persona" in updates
    state.target_persona = updates["target_persona"]

    # 3. Alternative Analysis
    mock_analysis = AlternativeAnalysis(
        current_alternatives=[
            AlternativeTool(name="A", financial_cost="B", time_cost="C", ux_friction="D")
        ],
        switching_cost="E",
        ten_x_value="F",
    )
    mock_structured_llm.invoke.return_value = mock_analysis

    updates = alternative_analysis_node(state)
    assert "alternative_analysis" in updates
    state.alternative_analysis = updates["alternative_analysis"]

    # 4. Value Proposition Canvas
    mock_vpc = ValuePropositionCanvas(
        customer_profile=CustomerProfile(
            customer_jobs=["A", "B"],
            pains=["C", "D"],
            gains=["E", "F"]
        ),
        value_map=ValueMap(
            products_and_services=["G", "H"],
            pain_relievers=["I", "J"],
            gain_creators=["K", "L"]
        ),
        fit_evaluation="Good fit"
    )
    mock_structured_llm.invoke.return_value = mock_vpc

    with patch("src.core.services.file_service.FileService.generate_vpc_pdf") as mock_pdf:
        updates = vpc_node(state)
        assert "value_proposition_canvas" in updates
        state.value_proposition_canvas = updates["value_proposition_canvas"]
        mock_pdf.assert_called_once()

    # Assert validation passes on final accumulated state
    validated = GlobalState.model_validate(state.model_dump())
    assert validated.target_persona is not None
    assert validated.alternative_analysis is not None
    assert validated.value_proposition_canvas is not None
