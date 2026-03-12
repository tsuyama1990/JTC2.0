from unittest.mock import MagicMock

from src.agents.reviewers import The3HReviewAgent
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
        sitemap_and_story=SitemapAndStory(
            sitemap=[Route(path="/", name="Home", purpose="Landing", is_protected=False)],
            core_story=UserStory(
                as_a="User",
                i_want_to="do something",
                so_that="value",
                acceptance_criteria=["A"],
                target_route="/",
            ),
        ),
    )


def test_3h_review_immediate_consensus() -> None:
    state = _setup_base_state()
    mock_llm: MagicMock = MagicMock()
    mock_response: MagicMock = MagicMock()
    mock_response.content = "Looks good. [APPROVED]"
    mock_llm.invoke.return_value = mock_response

    agent = The3HReviewAgent(llm=mock_llm)
    updates = agent.run(state)  # type: ignore[arg-type] # type: ignore[arg-type]

    assert mock_llm.invoke.call_count == 3
    assert updates["hacker_review"] == "Looks good. [APPROVED]"
    assert updates["hipster_review"] == "Looks good. [APPROVED]"
    assert updates["hustler_review"] == "Looks good. [APPROVED]"
    assert "messages" not in updates


def test_3h_review_circuit_breaker() -> None:
    state = _setup_base_state()
    mock_llm: MagicMock = MagicMock()
    mock_response1: MagicMock = MagicMock()
    mock_response1.content = "Looks good. [APPROVED]"
    mock_response2: MagicMock = MagicMock()
    mock_response2.content = "Wait, 平行線ですね this won't work."
    mock_llm.invoke.side_effect = [mock_response1, mock_response2]

    agent = The3HReviewAgent(llm=mock_llm)
    updates = agent.run(state)  # type: ignore[arg-type]

    # Hacker passed, Hipster hit circuit breaker
    assert mock_llm.invoke.call_count == 2
    assert "hacker_review" in updates
    assert "messages" not in updates  # Circuit break doesn't add the max_turns message


def test_3h_review_max_turns_no_consensus() -> None:
    state = _setup_base_state()
    mock_llm: MagicMock = MagicMock()
    mock_response: MagicMock = MagicMock()
    mock_response.content = "I disagree."
    mock_llm.invoke.return_value = mock_response

    agent = The3HReviewAgent(llm=mock_llm)
    agent.settings.simulation.max_turns = 2
    updates = agent.run(state)  # type: ignore[arg-type]

    # 2 turns * 3 roles = 6 invokes
    assert mock_llm.invoke.call_count == 6
    assert "messages" in updates
    assert updates["messages"][-1] == "3H Review: Consensus not reached. Please review the debate."
