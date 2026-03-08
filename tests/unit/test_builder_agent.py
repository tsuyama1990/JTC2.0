from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from src.agents.builder import BuilderAgent
from src.domain_models.agent_prompt import AgentPromptSpec, StateMachine
from src.domain_models.sitemap import Route, SitemapAndStory, UserStory
from src.domain_models.state import GlobalState


class TestBuilderAgent:
    @pytest.fixture
    def state_with_sitemap(self) -> GlobalState:
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

    @pytest.fixture
    def agent(self) -> BuilderAgent:
        # Mock LLM
        mock_llm = MagicMock()
        return BuilderAgent(llm=mock_llm)

    def test_generate_agent_prompt_spec(
        self, agent: BuilderAgent, state_with_sitemap: GlobalState
    ) -> None:
        """
        Test generate_agent_prompt_spec with mocked LLM response.
        """
        assert state_with_sitemap.sitemap_and_story is not None
        mock_spec = AgentPromptSpec(
            sitemap="Mapped Routes",
            routing_and_constraints="No server components",
            core_user_story=state_with_sitemap.sitemap_and_story.core_story,
            state_machine=StateMachine(
                success="Success UI",
                loading="Loading Spinner",
                error="Error Toast",
                empty="Empty State",
            ),
            validation_rules="Zod schemas",
            mermaid_flowchart="graph TD;",
        )

        mock_llm = cast(MagicMock, agent.llm)
        mock_llm.generate_structured.return_value = mock_spec

        result = agent.generate_agent_prompt_spec(state_with_sitemap)

        assert "agent_prompt_spec" in result
        assert result["agent_prompt_spec"].sitemap == "Mapped Routes"
        assert result["agent_prompt_spec"].validation_rules == "Zod schemas"
        mock_llm.generate_structured.assert_called_once()

    def test_generate_agent_prompt_spec_missing_state(self, agent: BuilderAgent) -> None:
        """
        Test generate_agent_prompt_spec with missing sitemap_and_story.
        """
        state = GlobalState()
        result = agent.generate_agent_prompt_spec(state)
        assert result == {}
