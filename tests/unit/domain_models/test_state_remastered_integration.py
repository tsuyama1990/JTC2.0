
from src.domain_models.alternative_analysis import AlternativeAnalysis, AlternativeTool
from src.domain_models.state import GlobalState
from src.domain_models.value_proposition import CustomerProfile, ValueMap, ValuePropositionCanvas


def test_global_state_remastered_fields() -> None:
    state = GlobalState(topic="Test")
    assert state.alternative_analysis is None
    assert state.value_proposition is None
    assert state.mental_model is None
    assert state.customer_journey is None
    assert state.sitemap_and_story is None
    assert state.agent_prompt_spec is None
    assert state.experiment_plan is None

    # Test setting fields
    tool = AlternativeTool(name="Tool Name", financial_cost="Financial Cost", time_cost="Time Cost", ux_friction="UX Friction")
    state.alternative_analysis = AlternativeAnalysis(current_alternatives=[tool], switching_cost="High cost", ten_x_value="Value is huge")
    state.value_proposition = ValuePropositionCanvas(
        customer_profile=CustomerProfile(customer_jobs=["Jobs jobs"], pains=["Pains pains"], gains=["Gains gains"]),
        value_map=ValueMap(products_and_services=["Services"], pain_relievers=["Pain rel"], gain_creators=["Gain creators"]),
        fit_evaluation="Good fit overall"
    )

    assert state.alternative_analysis is not None
    assert state.value_proposition is not None
