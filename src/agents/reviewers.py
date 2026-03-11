import logging
from typing import Any

from src.agents.base import BaseAgent
from src.core.config import get_settings
from src.core.interfaces import ILLMClient
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


class The3HReviewAgent(BaseAgent):
    """
    Agent responsible for Phase 4, Step 10: 3H Review.
    Executes Hacker, Hipster, and Hustler reviews.
    """

    def __init__(self, llm: ILLMClient) -> None:
        self.llm = llm
        self.settings = get_settings()

    def run(self, state: GlobalState) -> dict[str, Any]:
        updates = {}

        if not state.sitemap_and_story or not state.value_proposition_canvas:
            logger.warning("Missing required context for 3H Review.")
            return {}

        from langchain_core.prompts import ChatPromptTemplate

        # Hacker Review
        hacker_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "【前提とするサイトマップと機能要件を遵守しつつ】技術的負債、スケーラビリティ、セキュリティの観点からワイヤーフレームをレビューせよ。不要に複雑なDB構造やリアルタイム通信を避け、スプレッドシートや既存APIのモックで代替できないか追求せよ。",
                ),
                ("user", f"Context: {state.sitemap_and_story.model_dump_json()}"),
            ]
        )
        try:
            hacker_result = (hacker_prompt | self.llm).invoke({})
            updates["hacker_review"] = str(hacker_result.content)
        except Exception:
            logger.exception("Failed Hacker review")

        # Hipster Review
        hipster_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "【前提とするメンタルモデルとペルソナを遵守しつつ】ユーザーの『Don't make me think（考えさせるな）』の原則に基づきUXをレビューせよ。メンタルモデルに反するオンボーディングの摩擦、タップ回数の多さ、エラー時の不親切さを指摘せよ。",
                ),
                ("user", f"Context: {state.sitemap_and_story.model_dump_json()}"),
            ]
        )
        try:
            hipster_result = (hipster_prompt | self.llm).invoke({})
            updates["hipster_review"] = str(hipster_result.content)
        except Exception:
            logger.exception("Failed Hipster review")

        # Hustler Review
        hustler_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "【前提とする代替品分析とVPCを遵守しつつ】ユニットエコノミクス（LTV > 3x CAC）の観点からビジネスモデルをレビューせよ。誰がどうやって見つけるのか、なぜ継続してお金を払うのかを厳しく問いただせ。",
                ),
                ("user", f"Context: {state.value_proposition_canvas.model_dump_json()}"),
            ]
        )
        try:
            hustler_result = (hustler_prompt | self.llm).invoke({})
            updates["hustler_review"] = str(hustler_result.content)
        except Exception:
            logger.exception("Failed Hustler review")

        return updates
