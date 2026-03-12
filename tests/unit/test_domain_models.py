from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from src.agents.personas import (
    AlternativeAnalysisAgent,
    PersonaGeneratorAgent,
    ValuePropositionAgent,
)
from src.domain_models.alternative_analysis import AlternativeAnalysis, AlternativeTool
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.persona import EmpathyMap, Persona
from src.domain_models.state import GlobalState, Phase
from src.domain_models.value_proposition_canvas import (
    CustomerProfile,
    ValueMap,
    ValuePropositionCanvas,
)


def test_lean_canvas_valid() -> None:
    """Test valid LeanCanvas creation."""
    canvas = LeanCanvas(
        id=1,
        title="Test Idea",
        problem="Test Problem Problem Problem",  # > 3 words
        customer_segments="Test Segment",
        unique_value_prop="Test UVP UVP UVP",  # > 3 words
        solution="Test Solution Solution Solution",  # > 3 words
    )
    assert canvas.id == 1
    assert canvas.title == "Test Idea"
    assert canvas.status == "draft"


def test_lean_canvas_invalid_missing_field() -> None:
    """Test LeanCanvas validation error for missing fields."""
    with pytest.raises(ValidationError):
        LeanCanvas(
            id=1,
            title="Test Idea",
            # Missing problem
            customer_segments="Test Segment",
            unique_value_prop="Test UVP",
            solution="Test Solution",
        )  # type: ignore[call-arg]


def test_lean_canvas_extra_field() -> None:
    """Test LeanCanvas validation error for extra fields."""
    with pytest.raises(ValidationError):
        LeanCanvas(
            id=1,
            title="Test Idea",
            problem="Test Problem",
            customer_segments="Test Segment",
            unique_value_prop="Test UVP",
            solution="Test Solution",
            extra_field="Should fail",  # Extra field
        )  # type: ignore[call-arg]


def test_lean_canvas_short_title() -> None:
    """Test validation for short title."""
    with pytest.raises(ValidationError):
        LeanCanvas(
            id=1,
            title="Hi",  # Too short
            problem="Test Problem Problem",
            customer_segments="Test Segment",
            unique_value_prop="Test UVP UVP UVP",
            solution="Test Solution Solution",
        )


def test_lean_canvas_short_content() -> None:
    """Test validation for short content."""
    with pytest.raises(ValidationError):
        LeanCanvas(
            id=1,
            title="Test Idea",
            problem="Short",  # Too short
            customer_segments="Test Segment",
            unique_value_prop="Test UVP UVP UVP",
            solution="Test Solution Solution",
        )


def test_global_state_defaults() -> None:
    """Test GlobalState default values."""
    state = GlobalState()
    assert state.phase == Phase.IDEATION
    assert state.generated_ideas is None
    assert state.selected_idea is None


def test_global_state_phase_enum() -> None:
    """Test GlobalState uses Phase enum."""
    # Note: CPF phase requires a target_persona
    persona = Persona(
        name="Test Name",
        occupation="Tester",
        demographics="30, Testland, Test City, 12345",
        goals=["Test", "B"],
        frustrations=["Bugs", "C"],
        bio="A tester bio.",
        empathy_map=EmpathyMap(says=["Hi"], thinks=["Hmm"], does=["Test"], feels=["Good"]),
    )
    state = GlobalState(
        phase=Phase.CPF,
        target_persona=persona,
        selected_idea=LeanCanvas(id=1, title="Test Idea Name", problem="Problem description long enough", customer_segments="Customer segments defined", unique_value_prop="UVP that passes checks", solution="Solution string enough")
    )
    assert state.phase == "cpf"
    assert isinstance(state.phase, Phase)


def test_value_proposition_canvas_schema() -> None:
    """Test that extra fields are strictly forbidden."""
    with pytest.raises(ValidationError):
        ValuePropositionCanvas.model_validate(
            {
                "customer_profile": {
                    "customer_jobs": ["Job"],
                    "pains": ["Pain"],
                    "gains": ["Gain"],
                },
                "value_map": {
                    "products_and_services": ["Product"],
                    "pain_relievers": ["Relief"],
                    "gain_creators": ["Creator"],
                },
                "fit_evaluation": "Good",
                "extra_field": "Should fail",
            }
        )


def test_persona_generator_agent_success() -> None:
    mock_llm = MagicMock()
    mock_structured = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured

    expected_persona = Persona(
        name="Test",
        occupation="Test",
        demographics="Test Demographics",
        goals=["A", "B"],
        frustrations=["C", "D"],
        bio="Test Bio",
        empathy_map=EmpathyMap(
            says=["A", "B"], thinks=["C", "D"], does=["E", "F"], feels=["G", "H"]
        ),
    )
    mock_structured.invoke.return_value = expected_persona

    agent = PersonaGeneratorAgent(mock_llm)
    idea = LeanCanvas(
        id=1,
        title="Test Idea",
        problem="Test Problem Problem",
        customer_segments="Test Segment Segment",
        unique_value_prop="Test UVP UVP UVP",
        solution="Test Solution Solution",
    )
    state = GlobalState(topic="Test Idea", selected_idea=idea)

    result = agent.run(state)
    assert "target_persona" in result
    assert result["target_persona"] == expected_persona


def test_alternative_analysis_agent_success() -> None:
    mock_llm = MagicMock()
    mock_structured = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured

    expected_analysis = AlternativeAnalysis(
        current_alternatives=[
            AlternativeTool(name="A", financial_cost="B", time_cost="C", ux_friction="D")
        ],
        switching_cost="E",
        ten_x_value="F",
    )
    mock_structured.invoke.return_value = expected_analysis

    agent = AlternativeAnalysisAgent(mock_llm)
    idea = LeanCanvas(
        id=1,
        title="Test Idea",
        problem="Test Problem Problem",
        customer_segments="Test Segment Segment",
        unique_value_prop="Test UVP UVP UVP",
        solution="Test Solution Solution",
    )
    persona = Persona(
        name="Test Name",
        occupation="Test Occupation",
        demographics="Test Demographics",
        goals=["A", "B"],
        frustrations=["C", "D"],
        bio="Test Bio",
        empathy_map=EmpathyMap(
            says=["A", "B"], thinks=["C", "D"], does=["E", "F"], feels=["G", "H"]
        ),
    )
    state = GlobalState(topic="Test Idea", selected_idea=idea, target_persona=persona)

    result = agent.run(state)
    assert "alternative_analysis" in result
    assert result["alternative_analysis"] == expected_analysis


def test_vpc_agent_success() -> None:
    mock_llm = MagicMock()
    mock_structured = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured

    expected_vpc = ValuePropositionCanvas(
        customer_profile=CustomerProfile(
            customer_jobs=["A", "B"], pains=["C", "D"], gains=["E", "F"]
        ),
        value_map=ValueMap(
            products_and_services=["G", "H"], pain_relievers=["I", "J"], gain_creators=["K", "L"]
        ),
        fit_evaluation="Good fit",
    )
    mock_structured.invoke.return_value = expected_vpc

    agent = ValuePropositionAgent(mock_llm)
    idea = LeanCanvas(
        id=1,
        title="Test Idea",
        problem="Test Problem Problem",
        customer_segments="Test Segment Segment",
        unique_value_prop="Test UVP UVP UVP",
        solution="Test Solution Solution",
    )
    persona = Persona(
        name="Test Name",
        occupation="Test Occupation",
        demographics="Test Demographics",
        goals=["A", "B"],
        frustrations=["C", "D"],
        bio="Test Bio",
        empathy_map=EmpathyMap(
            says=["A", "B"], thinks=["C", "D"], does=["E", "F"], feels=["G", "H"]
        ),
    )
    state = GlobalState(topic="Test Idea", selected_idea=idea, target_persona=persona)

    result = agent.run(state)
    assert "value_proposition_canvas" in result
    assert result["value_proposition_canvas"] == expected_vpc


def test_persona_agent_failure() -> None:
    mock_llm = MagicMock()
    mock_structured = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured
    mock_structured.invoke.side_effect = Exception("Test failure")

    agent = PersonaGeneratorAgent(mock_llm)
    idea = LeanCanvas(
        id=1,
        title="Test Idea",
        problem="Test Problem Problem",
        customer_segments="Test Segment Segment",
        unique_value_prop="Test UVP UVP UVP",
        solution="Test Solution Solution",
    )
    state = GlobalState(topic="Test Idea", selected_idea=idea)

    result = agent.run(state)
    assert result == {}


def test_alternative_analysis_agent_failure() -> None:
    mock_llm = MagicMock()
    mock_structured = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured
    mock_structured.invoke.side_effect = Exception("Test failure")

    agent = AlternativeAnalysisAgent(mock_llm)
    idea = LeanCanvas(
        id=1,
        title="Test Idea",
        problem="Test Problem Problem",
        customer_segments="Test Segment Segment",
        unique_value_prop="Test UVP UVP UVP",
        solution="Test Solution Solution",
    )
    persona = Persona(
        name="Test Name",
        occupation="Test Occupation",
        demographics="Test Demographics",
        goals=["A", "B"],
        frustrations=["C", "D"],
        bio="Test Bio Test Bio Test Bio",
        empathy_map=EmpathyMap(
            says=["A", "B"], thinks=["C", "D"], does=["E", "F"], feels=["G", "H"]
        ),
    )
    state = GlobalState(topic="Test Idea", selected_idea=idea, target_persona=persona)

    result = agent.run(state)
    assert result == {}


def test_vpc_agent_failure() -> None:
    mock_llm = MagicMock()
    mock_structured = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured
    mock_structured.invoke.side_effect = Exception("Test failure")

    agent = ValuePropositionAgent(mock_llm)
    idea = LeanCanvas(
        id=1,
        title="Test Idea",
        problem="Test Problem Problem",
        customer_segments="Test Segment Segment",
        unique_value_prop="Test UVP UVP UVP",
        solution="Test Solution Solution",
    )
    persona = Persona(
        name="Test Name",
        occupation="Test Occupation",
        demographics="Test Demographics",
        goals=["A", "B"],
        frustrations=["C", "D"],
        bio="Test Bio Test Bio Test Bio",
        empathy_map=EmpathyMap(
            says=["A", "B"], thinks=["C", "D"], does=["E", "F"], feels=["G", "H"]
        ),
    )
    state = GlobalState(topic="Test Idea", selected_idea=idea, target_persona=persona)

    result = agent.run(state)
    assert result == {}
