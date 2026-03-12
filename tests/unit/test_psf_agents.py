from unittest.mock import MagicMock, patch

from src.agents.psf import MentalModelJourneyAgent
from src.domain_models.customer_journey import CustomerJourney, JourneyPhase
from src.domain_models.mental_model_diagram import MentalModelDiagram, MentalTower
from src.domain_models.persona import EmpathyMap, Persona
from src.domain_models.state import GlobalState
from src.domain_models.value_proposition_canvas import (
    CustomerProfile,
    ValueMap,
    ValuePropositionCanvas,
)


def test_mental_model_agent_receives_context() -> None:
    state = GlobalState(
        topic="test",
        target_persona=Persona(
            name="Test Name", occupation="Test Occ", demographics="Test Demo", goals=["A", "B"], frustrations=["C", "D"], bio="A valid bio string.",
            empathy_map=EmpathyMap(says=["A"], thinks=["B"], does=["C"], feels=["D"])
        ),
        value_proposition_canvas=ValuePropositionCanvas(
            customer_profile=CustomerProfile(customer_jobs=["A"], pains=["B"], gains=["C"]),
            value_map=ValueMap(products_and_services=["A"], pain_relievers=["B"], gain_creators=["C"]),
            fit_evaluation="Good"
        )
    )

    mock_llm = MagicMock()
    mock_structured = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured

    agent = MentalModelJourneyAgent(llm=mock_llm)

    # Mock return values for the two chains
    mock_mm = MentalModelDiagram(towers=[MentalTower(belief="A", cognitive_tasks=["B"])], feature_alignment="C")
    mock_cj = CustomerJourney(
        phases=[
            JourneyPhase(phase_name="P1", touchpoint="T1", customer_action="A1", mental_tower_ref="R1", pain_points=["P1"], emotion_score=1),
            JourneyPhase(phase_name="P2", touchpoint="T2", customer_action="A2", mental_tower_ref="R2", pain_points=["P2"], emotion_score=2),
            JourneyPhase(phase_name="P3", touchpoint="T3", customer_action="A3", mental_tower_ref="R3", pain_points=["P3"], emotion_score=3)
        ],
        worst_pain_phase="P1"
    )
    mock_structured.invoke.side_effect = [mock_mm, mock_cj]

    result = agent.run(state)

    # Verify the context was passed to the invokes
    assert mock_structured.invoke.call_count == 2

    # First call: MM prompt
    call_1_args = mock_structured.invoke.call_args_list[0][0][0]
    user_msg_1 = call_1_args[1]["content"]
    assert "Persona" in user_msg_1
    assert "VPC" in user_msg_1

    # Second call: Journey prompt
    call_2_args = mock_structured.invoke.call_args_list[1][0][0]
    user_msg_2 = call_2_args[1]["content"]
    assert "Mental Model" in user_msg_2
    assert "Persona" in user_msg_2

    assert "mental_model_diagram" in result
    assert "customer_journey" in result
