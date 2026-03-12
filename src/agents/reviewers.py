import logging
from dataclasses import dataclass
from typing import Any

from src.agents.base import BaseAgent
from src.core.config import Settings, get_settings
from src.core.constants import PROMPT_HACKER, PROMPT_HIPSTER, PROMPT_HUSTLER
from src.core.interfaces import ILLMClient, IStateContext

logger = logging.getLogger(__name__)


@dataclass
class ReviewContext:
    sitemap_json: str
    vpc_json: str
    sys_prompts: dict[str, str]
    circuit_breakers: list[str]


class The3HReviewAgent(BaseAgent):
    """
    Agent responsible for Phase 4, Step 10: 3H Review.
    Executes Hacker, Hipster, and Hustler reviews.
    """

    def __init__(self, llm: ILLMClient, settings: Settings | None = None) -> None:
        self.llm = llm
        self.settings: Settings = settings or get_settings()

    def _invoke_review(self, role: str, other_feedback: str, ctx: ReviewContext) -> str:
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", ctx.sys_prompts[role]),
                (
                    "user",
                    "Context:\nSitemap & Story: {sitemap}\nVPC: {vpc}\n\nPrevious Feedback:\n{other_feedback}\n\nProvide your review:",
                ),
            ]
        )
        try:
            res = self.llm.invoke(
                prompt.format_messages(
                    sitemap=ctx.sitemap_json,
                    vpc=ctx.vpc_json,
                    other_feedback=other_feedback,
                )
            )
            return str(getattr(res, "content", res))
        except Exception:
            logger.exception(f"Failed {role} review")
            return ""

    def _check_circuit_breaker(self, role: str, response: str, breakers: list[str]) -> bool:
        for breaker in breakers:
            if breaker in response:
                logger.warning(f"Circuit breaker '{breaker}' triggered by {role}.")
                return True
        return False

    def _run_turn(
        self,
        reviews: dict[str, str],
        ctx: ReviewContext,
    ) -> bool:
        # Immutable copy of reviews for the current turn context to prevent race conditions/inconsistencies
        frozen_reviews = dict(reviews)

        for role in ["Hacker", "Hipster", "Hustler"]:
            other_feedback = "\n".join(
                [f"{k}: {v}" for k, v in frozen_reviews.items() if k != role]
            )
            reviews[role] = self._invoke_review(role, other_feedback, ctx)

            if self._check_circuit_breaker(role, reviews[role], ctx.circuit_breakers):
                return True

        return False

    def run(self, state: IStateContext) -> dict[str, Any]:
        updates: dict[str, Any] = {}

        if not state.sitemap_and_story or not state.value_proposition_canvas:
            logger.warning("Missing required context for 3H Review.")
            return {}

        max_turns = self.settings.simulation.max_turns
        turn = 0
        circuit_breakers = self.settings.simulation.circuit_breakers
        consensus_reached = False
        circuit_broken = False

        sitemap_json = state.sitemap_and_story.model_dump_json()
        vpc_json = state.value_proposition_canvas.model_dump_json()

        sys_prompts = {
            "Hacker": PROMPT_HACKER,
            "Hipster": PROMPT_HIPSTER,
            "Hustler": PROMPT_HUSTLER,
        }
        reviews = {"Hacker": "", "Hipster": "", "Hustler": ""}

        ctx = ReviewContext(
            sitemap_json=sitemap_json,
            vpc_json=vpc_json,
            sys_prompts=sys_prompts,
            circuit_breakers=circuit_breakers,
        )

        while turn < max_turns:
            logger.info(f"3H Review Turn {turn + 1}/{max_turns}")

            circuit_broken = self._run_turn(reviews, ctx)

            if circuit_broken:
                break

            if all("[APPROVED]" in text for text in reviews.values()):
                consensus_reached = True
                break

            turn += 1

        updates["hacker_review"] = reviews["Hacker"]
        updates["hipster_review"] = reviews["Hipster"]
        updates["hustler_review"] = reviews["Hustler"]

        if not consensus_reached and not circuit_broken and turn >= max_turns:
            updates["messages"] = [
                *state.messages,
                "3H Review: Consensus not reached. Please review the debate.",
            ]

        return updates
