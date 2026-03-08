import os
from unittest.mock import MagicMock, patch

import pytest

from src.agents.builder import BuilderAgent
from src.core.config import get_settings
from src.domain_models.agent_prompt import AgentPromptSpec, StateMachine
from src.domain_models.sitemap import Route, SitemapAndStory, UserStory
from src.domain_models.state import GlobalState
from tests.conftest import DUMMY_ENV_VARS


@patch.dict(os.environ, DUMMY_ENV_VARS)
class TestCycle05UAT:
    @pytest.fixture
    def initial_state(self) -> GlobalState:
        story = UserStory(
            as_a="User",
            i_want_to="Login",
            so_that="I can access my dashboard",
            acceptance_criteria=["Must have email", "Must have password"],
            target_route="/login",
        )
        sitemap = SitemapAndStory(
            sitemap=[
                Route(path="/", name="Home", purpose="Landing", is_protected=False),
                Route(path="/login", name="Login", purpose="Auth", is_protected=False),
            ],
            core_story=story,
        )
        return GlobalState(sitemap_and_story=sitemap)

    def test_uat_c05_01_agent_prompt_spec_generation(self, initial_state: GlobalState) -> None:
        """
        Scenario 1: Agent Prompt Spec Generation Integration
        Verify BuilderAgent generates AgentPromptSpec using structured LLM output.
        """
        get_settings.cache_clear()

        mock_llm = MagicMock()
        agent = BuilderAgent(llm=mock_llm)

        assert initial_state.sitemap_and_story is not None
        mock_spec = AgentPromptSpec(
            sitemap="Mapped Routes",
            routing_and_constraints="No server components",
            core_user_story=initial_state.sitemap_and_story.core_story,
            state_machine=StateMachine(
                success="Success UI",
                loading="Loading Spinner",
                error="Error Toast",
                empty="Empty State",
            ),
            validation_rules="Zod schemas",
            mermaid_flowchart="graph TD;",
        )

        mock_llm.generate_structured.return_value = mock_spec

        # Execute
        result = agent.generate_agent_prompt_spec(initial_state)

        assert "agent_prompt_spec" in result
        assert result["agent_prompt_spec"].sitemap == "Mapped Routes"
        assert result["agent_prompt_spec"].validation_rules == "Zod schemas"

        # Verify network call was made
        mock_llm.generate_structured.assert_called_once()
