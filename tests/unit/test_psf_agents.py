from unittest.mock import MagicMock

from src.agents.psf import MentalModelJourneyAgent, SitemapWireframeAgent
from src.domain_models.customer_journey import CustomerJourney, JourneyPhase
from src.domain_models.mental_model_diagram import MentalModelDiagram, MentalTower
from src.domain_models.persona import EmpathyMap, Persona
from src.domain_models.sitemap_and_story import Route, SitemapAndStory, UserStory
from src.domain_models.state import GlobalState
from src.domain_models.value_proposition_canvas import (
    CustomerProfile,
    ValueMap,
    ValuePropositionCanvas,
)


def _setup_base_state() -> GlobalState:
    return GlobalState(
        topic="test",
        target_persona=Persona(
            name="Test Name",
            occupation="Test Occ",
            demographics="Test Demo",
            goals=["A", "B"],
            frustrations=["C", "D"],
            bio="A valid bio string.",
            empathy_map=EmpathyMap(says=["A"], thinks=["B"], does=["C"], feels=["D"]),
        ),
        value_proposition_canvas=ValuePropositionCanvas(
            customer_profile=CustomerProfile(customer_jobs=["A"], pains=["B"], gains=["C"]),
            value_map=ValueMap(
                products_and_services=["A"], pain_relievers=["B"], gain_creators=["C"]
            ),
            fit_evaluation="Good",
        ),
    )


def test_mental_model_agent_receives_context() -> None:
    state = _setup_base_state()

    mock_llm = MagicMock()
    mock_structured = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured

    agent = MentalModelJourneyAgent(llm=mock_llm)

    # Mock return values for the two chains
    mock_mm = MentalModelDiagram(
        towers=[MentalTower(belief="A", cognitive_tasks=["B"])], feature_alignment="C"
    )
    mock_cj = CustomerJourney(
        phases=[
            JourneyPhase(
                phase_name="P1",
                touchpoint="T1",
                customer_action="A1",
                mental_tower_ref="A",
                pain_points=["P1"],
                emotion_score=1,
            ),
            JourneyPhase(
                phase_name="P2",
                touchpoint="T2",
                customer_action="A2",
                mental_tower_ref="A",
                pain_points=["P2"],
                emotion_score=2,
            ),
            JourneyPhase(
                phase_name="P3",
                touchpoint="T3",
                customer_action="A3",
                mental_tower_ref="A",
                pain_points=["P3"],
                emotion_score=3,
            ),
        ],
        worst_pain_phase="P1",
    )
    mock_structured.invoke.side_effect = [mock_mm, mock_cj]

    result = agent.run(state)  # type: ignore[arg-type]  # type: ignore  # type: ignore  # type: ignore[arg-type]  # type: ignore[arg-type]

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


def test_mental_model_agent_retry_success() -> None:
    """Test that the agent retries generating the journey if validation fails, and succeeds."""
    state = _setup_base_state()
    mock_llm = MagicMock()
    mock_structured = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured
    agent = MentalModelJourneyAgent(llm=mock_llm)

    mock_mm = MentalModelDiagram(
        towers=[MentalTower(belief="CorrectBelief", cognitive_tasks=["A"])], feature_alignment="C"
    )

    # Invalid journey: ref doesn't match
    invalid_cj = CustomerJourney(
        phases=[
            JourneyPhase(
                phase_name="P1",
                touchpoint="T1",
                customer_action="A1",
                mental_tower_ref="WrongBelief",
                pain_points=["P1"],
                emotion_score=1,
            ),
            JourneyPhase(
                phase_name="P2",
                touchpoint="T2",
                customer_action="A2",
                mental_tower_ref="CorrectBelief",
                pain_points=["P2"],
                emotion_score=2,
            ),
            JourneyPhase(
                phase_name="P3",
                touchpoint="T3",
                customer_action="A3",
                mental_tower_ref="CorrectBelief",
                pain_points=["P3"],
                emotion_score=3,
            ),
        ],
        worst_pain_phase="P1",
    )

    # Valid journey
    valid_cj = CustomerJourney(
        phases=[
            JourneyPhase(
                phase_name="P1",
                touchpoint="T1",
                customer_action="A1",
                mental_tower_ref="CorrectBelief",
                pain_points=["P1"],
                emotion_score=1,
            ),
            JourneyPhase(
                phase_name="P2",
                touchpoint="T2",
                customer_action="A2",
                mental_tower_ref="CorrectBelief",
                pain_points=["P2"],
                emotion_score=2,
            ),
            JourneyPhase(
                phase_name="P3",
                touchpoint="T3",
                customer_action="A3",
                mental_tower_ref="CorrectBelief",
                pain_points=["P3"],
                emotion_score=3,
            ),
        ],
        worst_pain_phase="P1",
    )

    # The LLM returns the MM diagram first, then the invalid journey, then the valid journey
    mock_structured.invoke.side_effect = [mock_mm, invalid_cj, valid_cj]

    result = agent.run(state)  # type: ignore[arg-type]  # type: ignore  # type: ignore  # type: ignore[arg-type]  # type: ignore[arg-type]

    # 1 call for MM, 2 calls for CJ
    assert mock_structured.invoke.call_count == 3
    assert "mental_model_diagram" in result
    assert "customer_journey" in result
    assert result["customer_journey"] == valid_cj


def test_mental_model_agent_retry_exhausted() -> None:
    """Test that the agent falls back when retries are exhausted."""
    state = _setup_base_state()
    mock_llm = MagicMock()
    mock_structured = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured
    agent = MentalModelJourneyAgent(llm=mock_llm)

    mock_mm = MentalModelDiagram(
        towers=[MentalTower(belief="CorrectBelief", cognitive_tasks=["A"])], feature_alignment="C"
    )

    # Invalid journey: ref doesn't match
    invalid_cj = CustomerJourney(
        phases=[
            JourneyPhase(
                phase_name="P1",
                touchpoint="T1",
                customer_action="A1",
                mental_tower_ref="WrongBelief",
                pain_points=["P1"],
                emotion_score=1,
            ),
            JourneyPhase(
                phase_name="P2",
                touchpoint="T2",
                customer_action="A2",
                mental_tower_ref="WrongBelief",
                pain_points=["P2"],
                emotion_score=2,
            ),
            JourneyPhase(
                phase_name="P3",
                touchpoint="T3",
                customer_action="A3",
                mental_tower_ref="WrongBelief",
                pain_points=["P3"],
                emotion_score=3,
            ),
        ],
        worst_pain_phase="P1",
    )

    # MM + 3 failed CJ attempts
    mock_structured.invoke.side_effect = [mock_mm, invalid_cj, invalid_cj, invalid_cj]

    result = agent.run(state)  # type: ignore[arg-type]  # type: ignore  # type: ignore  # type: ignore[arg-type]  # type: ignore[arg-type]

    # 1 call for MM, 3 calls for CJ
    assert mock_structured.invoke.call_count == 4
    assert "mental_model_diagram" in result
    assert "customer_journey" not in result
    assert "messages" in result
    assert "Please simplify the Persona complexity" in result["messages"][-1]


def test_sitemap_wireframe_agent_success() -> None:
    """Test SitemapWireframeAgent successfully generates a sitemap and story."""
    state = GlobalState(
        topic="test",
        customer_journey=CustomerJourney(
            phases=[
                JourneyPhase(
                    phase_name="P1",
                    touchpoint="T1",
                    customer_action="A1",
                    mental_tower_ref="R1",
                    pain_points=["P1"],
                    emotion_score=1,
                ),
                JourneyPhase(
                    phase_name="P2",
                    touchpoint="T2",
                    customer_action="A2",
                    mental_tower_ref="R1",
                    pain_points=["P2"],
                    emotion_score=2,
                ),
                JourneyPhase(
                    phase_name="P3",
                    touchpoint="T3",
                    customer_action="A3",
                    mental_tower_ref="R1",
                    pain_points=["P3"],
                    emotion_score=3,
                ),
            ],
            worst_pain_phase="P1",
        ),
    )

    mock_llm = MagicMock()
    mock_structured = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured
    agent = SitemapWireframeAgent(llm=mock_llm)

    expected_result = SitemapAndStory(
        sitemap=[Route(path="/", name="Home", purpose="Landing", is_protected=False)],
        core_story=UserStory(
            as_a="User",
            i_want_to="do something",
            so_that="value",
            acceptance_criteria=["A"],
            target_route="/",
        ),
    )
    mock_structured.invoke.return_value = expected_result

    result = agent.run(state)  # type: ignore[arg-type]  # type: ignore  # type: ignore  # type: ignore[arg-type]  # type: ignore[arg-type]

    assert mock_structured.invoke.call_count == 1
    assert "sitemap_and_story" in result
    assert result["sitemap_and_story"] == expected_result


def test_sitemap_wireframe_agent_missing_journey() -> None:
    """Test SitemapWireframeAgent raises ValueError when missing customer journey."""
    state = GlobalState(topic="test")

    mock_llm = MagicMock()
    agent = SitemapWireframeAgent(llm=mock_llm)

    import pytest

    with pytest.raises(ValueError, match="Missing Customer Journey for Sitemap generation."):
        agent.run(state)  # type: ignore[arg-type]  # type: ignore  # type: ignore  # type: ignore[arg-type]  # type: ignore[arg-type]


def test_mental_model_agent_missing_context() -> None:
    """Test MentalModelJourneyAgent raises ValueError when missing context."""
    state = GlobalState(topic="test")
    mock_llm = MagicMock()
    agent = MentalModelJourneyAgent(llm=mock_llm)

    import pytest

    with pytest.raises(
        ValueError, match="Missing required context for Mental Model & Journey Mapping"
    ):
        agent.run(state)  # type: ignore[arg-type]  # type: ignore  # type: ignore  # type: ignore[arg-type]  # type: ignore[arg-type]
