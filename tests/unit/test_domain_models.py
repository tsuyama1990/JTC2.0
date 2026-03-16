from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from src.core.validators import ConfigValidators
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.persona import EmpathyMap, Persona
from src.domain_models.state import GlobalState, Phase
from src.domain_models.validators import StateValidator


@pytest.fixture
def valid_lean_canvas_data() -> dict[str, str | int]:
    return {
        "id": 1,
        "title": "Test Idea",
        "problem": "Test Problem Problem Problem",
        "customer_segments": "Test Segment",
        "unique_value_prop": "Test UVP UVP UVP",
        "solution": "Test Solution Solution Solution",
    }


def test_lean_canvas_valid(valid_lean_canvas_data: dict[str, str | int]) -> None:
    """Test valid LeanCanvas creation."""
    canvas = LeanCanvas(**valid_lean_canvas_data)
    assert canvas.id == 1
    assert canvas.title == "Test Idea"
    assert canvas.status == "draft"


def test_lean_canvas_invalid_missing_field(valid_lean_canvas_data: dict[str, str | int]) -> None:
    """Test LeanCanvas validation error for missing fields."""
    del valid_lean_canvas_data["problem"]
    with pytest.raises(ValidationError):
        LeanCanvas(**valid_lean_canvas_data)


def test_lean_canvas_extra_field(valid_lean_canvas_data: dict[str, str | int]) -> None:
    """Test LeanCanvas validation error for extra fields."""
    valid_lean_canvas_data["extra_field"] = "Should fail"
    with pytest.raises(ValidationError):
        LeanCanvas(**valid_lean_canvas_data)


@pytest.mark.parametrize("invalid_title", ["", "A", "Hi"])
def test_lean_canvas_short_title(
    valid_lean_canvas_data: dict[str, str | int], invalid_title: str
) -> None:
    """Test validation for short title."""
    valid_lean_canvas_data["title"] = invalid_title
    with pytest.raises(ValidationError):
        LeanCanvas(**valid_lean_canvas_data)


@pytest.mark.parametrize("invalid_content", ["", "Short"])
def test_lean_canvas_short_content(
    valid_lean_canvas_data: dict[str, str | int], invalid_content: str
) -> None:
    """Test validation for short content."""
    valid_lean_canvas_data["problem"] = invalid_content
    with pytest.raises(ValidationError):
        LeanCanvas(**valid_lean_canvas_data)


def test_global_state_defaults() -> None:
    """Test GlobalState default values."""
    state = GlobalState()
    assert state.phase == Phase.IDEATION
    assert state.generated_ideas is None
    assert state.selected_idea is None
    assert state.messages == []


@pytest.fixture
def mock_persona() -> Persona:
    return Persona(
        name="Test",
        occupation="Tester",
        demographics="30, Testland, Test City, 12345",
        goals=["Test"],
        frustrations=["Bugs"],
        bio="A tester.",
        empathy_map=EmpathyMap(says=["Hi"], thinks=["Hmm"], does=["Test"], feels=["Good"]),
    )


from src.domain_models.agent_spec import AgentPromptSpec
from src.domain_models.experiment import ExperimentPlan
from src.domain_models.journey import CustomerJourney
from src.domain_models.mental_model import MentalModelDiagram
from src.domain_models.sitemap import SitemapAndStory


@pytest.fixture
def mock_mental_model() -> MentalModelDiagram:
    return MentalModelDiagram.model_construct()  # type: ignore[call-arg]


@pytest.fixture
def mock_customer_journey() -> CustomerJourney:
    return CustomerJourney.model_construct()  # type: ignore[call-arg]


@pytest.fixture
def mock_sitemap() -> SitemapAndStory:
    return SitemapAndStory.model_construct()  # type: ignore[call-arg]


@pytest.fixture
def mock_agent_spec() -> AgentPromptSpec:
    return AgentPromptSpec.model_construct()  # type: ignore[call-arg]


@pytest.fixture
def mock_experiment_plan() -> ExperimentPlan:
    return ExperimentPlan.model_construct()  # type: ignore[call-arg]


def test_global_state_phase_enum(mock_persona: Persona) -> None:
    """Test GlobalState uses Phase enum."""
    state = GlobalState(phase=Phase.VERIFICATION, target_persona=mock_persona)
    assert state.phase == Phase.VERIFICATION
    assert state.phase.value == "verification"
    assert isinstance(state.phase, Phase)


INVALID_PHASE = "INVALID_PHASE"


def test_state_validator_invalid_phase() -> None:
    """Test StateValidator handling invalid phase type."""
    state = GlobalState()
    # Mypy strictly enforces phase types, so we bypass to test the internal runtime validation check
    state.__dict__["phase"] = INVALID_PHASE

    with pytest.raises(TypeError, match="Invalid phase enum value"):
        StateValidator.validate_phase_requirements(state)


def test_state_validator_missing_requirements_verification() -> None:
    """Test StateValidator VERIFICATION phase missing target_persona."""
    # Create valid state then modify dict directly to bypass Pydantic validation on init
    state = GlobalState(phase=Phase.IDEATION)
    state.__dict__["phase"] = Phase.VERIFICATION
    state.__dict__["target_persona"] = None

    with pytest.raises(
        ValueError, match="Missing field 'target_persona' required for the VERIFICATION phase"
    ):
        StateValidator.validate_phase_requirements(state)


def test_state_validator_missing_requirements_solution(
    mock_mental_model: MentalModelDiagram, mock_customer_journey: CustomerJourney
) -> None:
    """Test StateValidator SOLUTION phase missing requirements."""
    state = GlobalState(phase=Phase.IDEATION)
    state.__dict__["phase"] = Phase.SOLUTION
    state.__dict__["mental_model"] = None
    with pytest.raises(
        ValueError, match="Missing field 'mental_model' required for the SOLUTION phase"
    ):
        StateValidator.validate_phase_requirements(state)

    state.__dict__["mental_model"] = mock_mental_model
    state.__dict__["customer_journey"] = None
    with pytest.raises(
        ValueError, match="Missing field 'customer_journey' required for the SOLUTION phase"
    ):
        StateValidator.validate_phase_requirements(state)

    state.__dict__["customer_journey"] = mock_customer_journey
    state.__dict__["sitemap_and_story"] = None
    with pytest.raises(
        ValueError, match="Missing field 'sitemap_and_story' required for the SOLUTION phase"
    ):
        StateValidator.validate_phase_requirements(state)


def test_state_validator_missing_requirements_pmf() -> None:
    """Test StateValidator PMF phase missing agent_prompt_spec."""
    state = GlobalState(phase=Phase.IDEATION)
    state.__dict__["phase"] = Phase.PMF
    state.__dict__["agent_prompt_spec"] = None

    with pytest.raises(
        ValueError, match="Missing field 'agent_prompt_spec' required for the PMF phase"
    ):
        StateValidator.validate_phase_requirements(state)


def test_state_validator_missing_requirements_governance(
    mock_experiment_plan: ExperimentPlan,
) -> None:
    """Test StateValidator GOVERNANCE phase missing experiment_plan."""
    state = GlobalState(phase=Phase.IDEATION)
    state.__dict__["phase"] = Phase.GOVERNANCE
    state.__dict__["experiment_plan"] = None

    with pytest.raises(
        ValueError, match="Missing field 'experiment_plan' required for the GOVERNANCE phase"
    ):
        StateValidator.validate_phase_requirements(state)

    state.__dict__["experiment_plan"] = mock_experiment_plan
    state.__dict__["agent_prompt_spec"] = None
    with pytest.raises(
        ValueError, match="Missing field 'agent_prompt_spec' required for the GOVERNANCE phase"
    ):
        StateValidator.validate_phase_requirements(state)


@pytest.fixture
def mock_dirty_topic() -> str:
    return "Clean <script>alert(1)</script> \x00 Topic\n"


def test_state_validator_sanitization(mock_dirty_topic: str) -> None:
    """Test StateValidator topic sanitization."""
    state = GlobalState.model_construct(phase=Phase.IDEATION, topic=mock_dirty_topic)

    validated = StateValidator.validate_phase_requirements(state)
    # bleach.clean removes tags, resulting in "Clean alert(1)   Topic\n"
    # depending on exact regexes/replacements. Let's assert '<script>' is gone.
    assert "<script>" not in validated.topic
    assert "\x00" not in validated.topic


@pytest.fixture
def valid_openai_key() -> SecretStr:
    return SecretStr("sk-12345678901234567890")


@pytest.fixture
def valid_tavily_key() -> SecretStr:
    return SecretStr("tvly-12345678901234567890")


@pytest.fixture
def valid_v0_key() -> SecretStr:
    return SecretStr("v0-12345678901234567890")


@pytest.mark.parametrize(
    ("invalid_key", "error_msg"),
    [
        ("   ", "cannot be empty or whitespace"),
        ("sk-short", "too short"),
        ("sk-" + "a" * 130, "too long"),
        ("tv-12345678901234567890", "must start with 'sk-'"),
    ],
)
def test_config_validators_openai_key(
    valid_openai_key: SecretStr, invalid_key: str, error_msg: str
) -> None:
    ConfigValidators.validate_openai_key(valid_openai_key)
    with pytest.raises(ValueError, match=error_msg):
        ConfigValidators.validate_openai_key(SecretStr(invalid_key))


@pytest.mark.parametrize(
    ("invalid_key", "error_msg"),
    [
        ("   ", "cannot be empty or whitespace"),
        ("tvly-short", "too short"),
        ("tvly-" + "a" * 130, "too long"),
        ("sk-12345678901234567890", "must start with 'tvly-'"),
    ],
)
def test_config_validators_tavily_key(
    valid_tavily_key: SecretStr, invalid_key: str, error_msg: str
) -> None:
    ConfigValidators.validate_tavily_key(valid_tavily_key)
    with pytest.raises(ValueError, match=error_msg):
        ConfigValidators.validate_tavily_key(SecretStr(invalid_key))


@pytest.mark.parametrize(
    ("invalid_key", "error_msg"),
    [
        ("   ", "cannot be empty or whitespace"),
        ("v0-short", "between 20 and 128 characters"),
        ("v0-" + "a" * 130, "between 20 and 128 characters"),
        ("v0-1234567890123456789!", "must start with 'v0-' and contain only alphanumeric"),
    ],
)
def test_config_validators_v0_key(
    valid_v0_key: SecretStr, invalid_key: str, error_msg: str
) -> None:
    ConfigValidators.validate_v0_key(valid_v0_key)
    with pytest.raises(ValueError, match=error_msg):
        ConfigValidators.validate_v0_key(SecretStr(invalid_key))


@pytest.mark.parametrize(("val", "is_valid"), [(10, True), (0, False), (-1, False)])
def test_config_validators_resolution(val: int, is_valid: bool) -> None:
    if is_valid:
        assert ConfigValidators.validate_resolution(val) == val
    else:
        with pytest.raises(ValueError, match="strictly positive"):
            ConfigValidators.validate_resolution(val)


@pytest.mark.parametrize(("val", "is_valid"), [(30, True), (0, False), (-1, False)])
def test_config_validators_fps(val: int, is_valid: bool) -> None:
    if is_valid:
        assert ConfigValidators.validate_fps(val) == val
    else:
        with pytest.raises(ValueError, match="strictly positive"):
            ConfigValidators.validate_fps(val)


@pytest.mark.parametrize(("val", "is_valid"), [(10, True), (16, False), (-1, False)])
def test_config_validators_color(val: int, is_valid: bool) -> None:
    if is_valid:
        assert ConfigValidators.validate_color(val) == val
    else:
        with pytest.raises(ValueError, match="between 0 and 15"):
            ConfigValidators.validate_color(val)


@pytest.mark.parametrize(("val", "is_valid"), [(10, True), (0, False), (-1, False)])
def test_config_validators_dimension(val: int, is_valid: bool) -> None:
    if is_valid:
        assert ConfigValidators.validate_dimension(val) == val
    else:
        with pytest.raises(ValueError, match="positive"):
            ConfigValidators.validate_dimension(val)


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
