from langgraph.graph import END

from src.core.graph import route_after_pmf
from src.domain_models.mvp import MVP, Feature, MVPType, Priority
from src.domain_models.persona import Persona
from src.domain_models.state import GlobalState, Phase


def test_route_after_pmf_ideator():
    state = GlobalState(phase=Phase.IDEATION)
    assert route_after_pmf(state) == "ideator"

def test_route_after_pmf_verification():
    # To instantiate valid Verification state, we need target_persona
    persona = Persona(
        name="Test Persona",
        occupation="Tester",
        demographics="Age 25, Male, Developer",
        goals=["Test the app"],
        frustrations=["Bugs"],
        bio="A simple test persona.",
        interview_insights=["Verified with user."]
    )
    # Pass target_persona to constructor to satisfy validation
    state = GlobalState(phase=Phase.VERIFICATION, target_persona=persona)
    assert route_after_pmf(state) == "verification"

def test_route_after_pmf_end():
    # Valid PMF state requires MVP
    mvp = MVP(
        type=MVPType.LANDING_PAGE,
        core_features=[Feature(name="Test", description="Test", priority=Priority.MUST_HAVE)],
        success_criteria="Test"
    )
    state = GlobalState(phase=Phase.PMF, mvp_definition=mvp)
    assert route_after_pmf(state) == END

def test_route_after_pmf_invalid_phase():
    # Test case: Phase is not one of the explicitly handled ones (e.g., SOLUTION)
    # The current logic defaults to END for any unknown phase.
    # We verify this behavior.
    mvp = MVP(
        type=MVPType.LANDING_PAGE,
        core_features=[Feature(name="Test", description="Test", priority=Priority.MUST_HAVE)],
        success_criteria="Test"
    )
    state = GlobalState(phase=Phase.SOLUTION, mvp_definition=mvp)
    assert route_after_pmf(state) == END
