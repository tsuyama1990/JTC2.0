from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from src.core.validators import ConfigValidators
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.persona import EmpathyMap, Persona
from src.domain_models.state import GlobalState, Phase
from src.domain_models.validators import StateValidator


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
    # Note: VERIFICATION phase requires a target_persona
    persona = Persona(
        name="Test",
        occupation="Tester",
        demographics="30, Testland, Test City, 12345",
        goals=["Test"],
        frustrations=["Bugs"],
        bio="A tester.",
        empathy_map=EmpathyMap(says=["Hi"], thinks=["Hmm"], does=["Test"], feels=["Good"]),
    )
    state = GlobalState(phase=Phase.VERIFICATION, target_persona=persona)
    assert state.phase == "verification"
    assert isinstance(state.phase, Phase)


def test_state_validator_invalid_phase() -> None:
    """Test StateValidator handling invalid phase type."""
    state = GlobalState()
    # Mypy strictly enforces phase types, so we bypass to test the internal runtime validation check
    state.__dict__["phase"] = "INVALID_PHASE"

    with pytest.raises(TypeError, match="Invalid phase enum value"):
        StateValidator.validate_phase_requirements(state)


def test_state_validator_missing_requirements_verification() -> None:
    """Test StateValidator VERIFICATION phase missing target_persona."""
    # Bypass GlobalState constructor validation
    state = GlobalState.model_construct(phase=Phase.VERIFICATION, target_persona=None)

    with pytest.raises(
        ValueError, match="Missing field 'target_persona' required for the VERIFICATION phase"
    ):
        StateValidator.validate_phase_requirements(state)


def test_state_validator_missing_requirements_solution() -> None:
    """Test StateValidator SOLUTION phase missing requirements."""
    state = GlobalState.model_construct(phase=Phase.SOLUTION, mental_model=None)

    with pytest.raises(
        ValueError, match="Missing field 'mental_model' required for the SOLUTION phase"
    ):
        StateValidator.validate_phase_requirements(state)

    state = GlobalState.model_construct(
        phase=Phase.SOLUTION,
        mental_model="exists",  # type: ignore[arg-type]
        customer_journey=None,
    )
    with pytest.raises(
        ValueError, match="Missing field 'customer_journey' required for the SOLUTION phase"
    ):
        StateValidator.validate_phase_requirements(state)

    state = GlobalState.model_construct(
        phase=Phase.SOLUTION,
        mental_model="exists",  # type: ignore[arg-type]
        customer_journey="exists",  # type: ignore[arg-type]
        sitemap_and_story=None,
    )
    with pytest.raises(
        ValueError, match="Missing field 'sitemap_and_story' required for the SOLUTION phase"
    ):
        StateValidator.validate_phase_requirements(state)


def test_state_validator_missing_requirements_pmf() -> None:
    """Test StateValidator PMF phase missing agent_prompt_spec."""
    state = GlobalState.model_construct(phase=Phase.PMF, agent_prompt_spec=None)

    with pytest.raises(
        ValueError, match="Missing field 'agent_prompt_spec' required for the PMF phase"
    ):
        StateValidator.validate_phase_requirements(state)


def test_state_validator_missing_requirements_governance() -> None:
    """Test StateValidator GOVERNANCE phase missing experiment_plan."""
    state = GlobalState.model_construct(phase=Phase.GOVERNANCE, experiment_plan=None)

    with pytest.raises(
        ValueError, match="Missing field 'experiment_plan' required for the GOVERNANCE phase"
    ):
        StateValidator.validate_phase_requirements(state)

    state = GlobalState.model_construct(
        phase=Phase.GOVERNANCE,
        experiment_plan="exists",  # type: ignore[arg-type]
        agent_prompt_spec=None,
    )
    with pytest.raises(
        ValueError, match="Missing field 'agent_prompt_spec' required for the GOVERNANCE phase"
    ):
        StateValidator.validate_phase_requirements(state)


def test_state_validator_sanitization() -> None:
    """Test StateValidator topic sanitization."""
    # Inject dirty topic
    state = GlobalState.model_construct(
        phase=Phase.IDEATION, topic="Clean <script>alert(1)</script> \x00 Topic\n"
    )

    validated = StateValidator.validate_phase_requirements(state)
    assert validated.topic == "Clean alert(1)  Topic\n"





def test_config_validators_openai_key() -> None:
    ConfigValidators.validate_openai_key(SecretStr("sk-12345678901234567890"))
    with pytest.raises(ValueError, match="cannot be empty or whitespace"):
        ConfigValidators.validate_openai_key(SecretStr("   "))
    with pytest.raises(ValueError, match="too short"):
        ConfigValidators.validate_openai_key(SecretStr("sk-short"))
    with pytest.raises(ValueError, match="too long"):
        ConfigValidators.validate_openai_key(SecretStr("sk-" + "a" * 130))
    with pytest.raises(ValueError, match="must start with 'sk-'"):
        ConfigValidators.validate_openai_key(SecretStr("tv-12345678901234567890"))


def test_config_validators_tavily_key() -> None:
    ConfigValidators.validate_tavily_key(SecretStr("tvly-12345678901234567890"))
    with pytest.raises(ValueError, match="cannot be empty or whitespace"):
        ConfigValidators.validate_tavily_key(SecretStr("   "))
    with pytest.raises(ValueError, match="too short"):
        ConfigValidators.validate_tavily_key(SecretStr("tvly-short"))
    with pytest.raises(ValueError, match="too long"):
        ConfigValidators.validate_tavily_key(SecretStr("tvly-" + "a" * 130))
    with pytest.raises(ValueError, match="must start with 'tvly-'"):
        ConfigValidators.validate_tavily_key(SecretStr("sk-12345678901234567890"))


def test_config_validators_v0_key() -> None:
    ConfigValidators.validate_v0_key(SecretStr("v0-12345678901234567890"))
    with pytest.raises(ValueError, match="cannot be empty or whitespace"):
        ConfigValidators.validate_v0_key(SecretStr("   "))
    with pytest.raises(ValueError, match="between 20 and 128 characters"):
        ConfigValidators.validate_v0_key(SecretStr("v0-short"))
    with pytest.raises(ValueError, match="between 20 and 128 characters"):
        ConfigValidators.validate_v0_key(SecretStr("v0-" + "a" * 130))
    with pytest.raises(ValueError, match="must start with 'v0-' and contain only alphanumeric"):
        ConfigValidators.validate_v0_key(SecretStr("v0-1234567890123456789!"))


def test_config_validators_numbers() -> None:
    assert ConfigValidators.validate_resolution(10) == 10
    with pytest.raises(ValueError, match="strictly positive"):
        ConfigValidators.validate_resolution(0)

    assert ConfigValidators.validate_fps(30) == 30
    with pytest.raises(ValueError, match="strictly positive"):
        ConfigValidators.validate_fps(-1)

    assert ConfigValidators.validate_color(10) == 10
    with pytest.raises(ValueError, match="positive"):
        ConfigValidators.validate_dimension(0)


def test_config_validators_safe_path(tmp_path: Path) -> None:
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    target = base_dir / "target"

    assert ConfigValidators.is_safe_path(base_dir, target)
    assert not ConfigValidators.is_safe_path(base_dir, tmp_path / "other")
    assert not ConfigValidators.is_safe_path(base_dir, base_dir / "target\x00_poison")
    assert not ConfigValidators.is_safe_path("non_existent_base_123456", target)


def test_config_validators_allowed_directories(tmp_path: Path) -> None:
    base1 = tmp_path / "base1"
    base1.mkdir()
    base2 = tmp_path / "base2"
    base2.mkdir()

    assert ConfigValidators.validate_allowed_directories(base1 / "target", [base1, base2])
    assert ConfigValidators.validate_allowed_directories(base2 / "target", [base1, base2])
    assert not ConfigValidators.validate_allowed_directories(tmp_path / "other", [base1, base2])
