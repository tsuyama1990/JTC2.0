from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from src.agents.builder import BuilderAgent
from src.domain_models.agent_prompt_spec import AgentPromptSpec, StateMachine
from src.domain_models.sitemap_and_story import Route, SitemapAndStory, UserStory
from src.domain_models.state import GlobalState


class TestBuilderAgent:
    @pytest.fixture
    def state_with_context(self) -> GlobalState:
        sitemap = SitemapAndStory(
            sitemap=[Route(path="/", name="Home", purpose="Landing", is_protected=False)],
            core_story=UserStory(
                as_a="User",
                i_want_to="Test feature",
                so_that="Value",
                acceptance_criteria=["Criteria 1"],
                target_route="/",
            ),
        )
        return GlobalState(topic="Test Topic", sitemap_and_story=sitemap)

    @pytest.fixture
    def agent(self) -> BuilderAgent:
        # Mock LLM
        mock_llm = MagicMock()
        return BuilderAgent(llm=mock_llm)

    def test_generate_spec_with_context(
        self, agent: BuilderAgent, state_with_context: GlobalState
    ) -> None:
        """
        Test generate_spec reads context from state correctly.
        """
        with patch("src.agents.builder.ChatPromptTemplate.from_messages") as mock_prompt:
            mock_prompt_tmpl = MagicMock()
            mock_prompt.return_value = mock_prompt_tmpl

            mock_model_runnable = MagicMock()
            mock_llm = cast(MagicMock, agent.llm)
            mock_llm.with_structured_output.return_value = mock_model_runnable

            mock_chain = MagicMock()
            mock_prompt_tmpl.__or__.return_value = mock_chain

            # Mock the invoke result
            story = UserStory(
                as_a="A", i_want_to="B", so_that="C", acceptance_criteria=["D"], target_route="/"
            )
            sm = StateMachine(success="A", loading="B", error="C", empty="D")
            spec = AgentPromptSpec(
                sitemap="S",
                routing_and_constraints="R",
                core_user_story=story,
                state_machine=sm,
                validation_rules="V",
                mermaid_flowchart="M",
            )
            mock_model_runnable.invoke.return_value = spec

            result = agent.generate_spec(state_with_context)  # type: ignore[arg-type]

            assert "agent_prompt_spec" in result
            assert result["agent_prompt_spec"] == spec
            # Verify context was passed
            call_args = mock_prompt.call_args[0][0]
            user_msg = call_args[1][1]
            assert "Sitemap & Story" in user_msg
