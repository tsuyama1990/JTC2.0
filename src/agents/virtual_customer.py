import logging
from typing import Any

from src.agents.base import BaseAgent
from src.core.config import get_settings
from src.core.interfaces import ILLMClient, IStateContext

logger = logging.getLogger(__name__)


class VirtualCustomerAgent(BaseAgent):
    """
    Agent responsible for Phase 4, Step 8: Virtual Solution Interview.
    """

    def __init__(self, llm: ILLMClient) -> None:
        self.llm = llm
        self.settings = get_settings()

    def run(self, state: IStateContext) -> dict[str, Any]:
        if (
            not state.target_persona
            or not state.mental_model_diagram
            or not state.alternative_analysis
            or not state.sitemap_and_story
        ):
            logger.warning("Missing required context for Virtual Customer Interview.")
            return {}

        towers = [t.belief for t in state.mental_model_diagram.towers]
        alternatives = [a.name for a in state.alternative_analysis.current_alternatives]
        pains = state.target_persona.frustrations

        prompt_system = (
            f"あなたは {state.target_persona.name} です。"
            f"あなたの思考の根底には {towers} のような信念があり、現在は {alternatives} を使っていますが、{pains} に深く悩んでいます。"
            "今から提案される機能について、絶対に忖度せず、自分がお金を払ってでも使いたいか、それとも不要かを厳しくフィードバックしてください。"
            "特に『面倒くささ（スイッチングコスト）』には敏感に反応してください。"
        )

        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", prompt_system),
                (
                    "user",
                    f"Sitemap and User Story: {state.sitemap_and_story.model_dump_json()}\n"
                    "Provide your harsh feedback:",
                ),
            ]
        )

        try:
            messages = prompt.format_messages()
            result = self.llm.invoke(messages)
            return {"virtual_customer_review": str(getattr(result, "content", result))}
        except Exception:
            logger.exception("Failed to generate Virtual Customer feedback")

        return {}
