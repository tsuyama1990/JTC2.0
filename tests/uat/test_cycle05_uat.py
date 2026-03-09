import os
from unittest.mock import MagicMock, patch

import pytest

from src.agents.builder import BuilderAgent
from src.domain_models.agent_prompt import AgentPromptSpec, StateMachine
from src.domain_models.sitemap import Route, SitemapAndStory, UserStory
from src.domain_models.state import GlobalState
from tests.conftest import DUMMY_ENV_VARS


@patch.dict(os.environ, DUMMY_ENV_VARS)
class TestCycle05UAT:
    @pytest.fixture
    def initial_state(self) -> GlobalState:
        state = GlobalState(topic="UAT Cycle 5")

        # Setup prerequisite: Sitemap and Story
        story = UserStory(
            as_a="User",
            i_want_to="Action something big enough",
            so_that="I can achieve my goal.",
            acceptance_criteria=["Criterion 1", "Criterion 2"],
            target_route="/dashboard",
        )
        route = Route(
            path="/dashboard", name="Dashboard", purpose="Manage things", is_protected=True
        )
        state.sitemap_and_story = SitemapAndStory(sitemap=[route], core_story=story)

        return state

    def test_uat_c05_01_agent_prompt_spec_generation(self, initial_state: GlobalState) -> None:
        """
        Scenario 1: AgentPromptSpec Generation Integration
        Verify that BuilderAgent properly generates AgentPromptSpec.
        """
        from src.core.config import clear_settings_cache

        clear_settings_cache()

        mock_llm = MagicMock()
        mock_chain = MagicMock()

        # Mock structured output
        mock_spec = AgentPromptSpec(
            sitemap="Sitemap details go here, must be long enough to pass validation.",
            routing_and_constraints="Constraints details go here, must be long enough.",
            core_user_story=initial_state.sitemap_and_story.core_story,  # type: ignore
            state_machine=StateMachine(
                success="Success UI state description here",
                loading="Loading UI state description here",
                error="Error UI state description here",
                empty="Empty UI state description here",
            ),
            validation_rules="Validation rules description goes here, enough length.",
            mermaid_flowchart="flowchart TD; A-->B; flowchart details goes here.",
        )
        mock_chain.invoke.return_value = mock_spec

        # We must mock `with_structured_output` correctly since it is used in the code
        mock_llm.with_structured_output.return_value = mock_chain
        # Also need to mock the `|` operator for the prompt and LLM
        mock_prompt_chain = MagicMock()
        mock_prompt_chain.__or__.return_value = mock_chain

        agent = BuilderAgent(llm=mock_llm)

        with patch(
            "src.agents.builder.ChatPromptTemplate.from_messages", return_value=mock_prompt_chain
        ):
            result = agent.generate_agent_prompt_spec(initial_state)

        assert "agent_prompt_spec" in result
        assert result["agent_prompt_spec"].sitemap == mock_spec.sitemap

    def test_uat_c05_02_error_handling(self, initial_state: GlobalState) -> None:
        """
        Scenario 2: Error Handling
        Simulate LLM failure.
        """
        mock_llm = MagicMock()
        mock_chain = MagicMock()

        # Simulate exception
        mock_chain.invoke.side_effect = Exception("LLM Error")
        mock_llm.with_structured_output.return_value = mock_chain

        mock_prompt_chain = MagicMock()
        mock_prompt_chain.__or__.return_value = mock_chain

        agent = BuilderAgent(llm=mock_llm)

        with patch(
            "src.agents.builder.ChatPromptTemplate.from_messages", return_value=mock_prompt_chain
        ):
            result = agent.generate_agent_prompt_spec(initial_state)

        # Should handle error gracefully and return empty dict
        assert result == {}
