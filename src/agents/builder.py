import logging
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from src.agents.base import BaseAgent
from src.core.config import get_settings
from src.domain_models.mvp import MVPSpec
from src.domain_models.state import GlobalState
from src.tools.v0_client import V0Client

logger = logging.getLogger(__name__)


class FeatureList(BaseModel):
    """List of extracted features."""
    features: list[str] = Field(..., description="List of distinct features found in the solution description")


class BuilderAgent(BaseAgent):
    """
    Agent responsible for MVP Construction (Cycle 5).
    It parses the solution into features, enforcing Gate 3 (Problem-Solution Fit),
    and generates a UI using v0.dev.
    """

    def __init__(self, llm: ChatOpenAI) -> None:
        self.llm = llm
        self.settings = get_settings()

    def _extract_features(self, solution_description: str) -> list[str]:
        """
        Extract discrete features from the solution description using LLM.
        """
        if not solution_description or len(solution_description) < 10:
            logger.warning("Solution description too short for feature extraction.")
            return []

        # Sanitize input (basic check)
        if len(solution_description) > 5000:
             logger.warning("Solution description too long, truncating.")
             solution_description = solution_description[:5000]

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a product manager. Extract distinct features from the solution description."),
                ("user", f"Solution Description: {solution_description}\n\nList the features:")
            ]
        )
        chain = prompt | self.llm.with_structured_output(FeatureList)
        try:
            result = chain.invoke({})
            if isinstance(result, FeatureList):
                return result.features
            return []
        except Exception:
            logger.exception("Failed to extract features")
            return []

    def _create_mvp_spec(self, app_name: str, feature: str, idea_context: str) -> MVPSpec:
        """
        Create a detailed MVP Spec for the selected feature.
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are an expert UI/UX designer. Create a detailed MVP specification for v0.dev generation."),
                ("user", f"App Name: {app_name}\nCore Feature: {feature}\nContext: {idea_context}\n\nGenerate MVPSpec:")
            ]
        )
        chain = prompt | self.llm.with_structured_output(MVPSpec)
        try:
            result = chain.invoke({})
            if isinstance(result, MVPSpec):
                return result
            # Fallback
            return MVPSpec(app_name=app_name, core_feature=feature)
        except Exception:
            logger.exception("Failed to create MVP Spec")
            return MVPSpec(app_name=app_name, core_feature=feature)

    def run(self, state: GlobalState) -> dict[str, Any]:
        """
        Execute the Builder Agent logic.

        1. If selected_feature is set, proceed to generation.
        2. If not, extract features.
        3. If multiple features, return them for user selection (Gate 3).
        4. If single feature, auto-select and proceed.
        """
        if not state.selected_idea:
            logger.warning("No idea selected for Builder Agent.")
            return {}

        # 1. Handle Selection Logic
        selected_feature = state.selected_feature
        candidate_features = state.candidate_features

        if not selected_feature:
            if not candidate_features:
                # Extract features if not already done
                candidate_features = self._extract_features(state.selected_idea.solution)

            if not candidate_features:
                logger.warning("No features extracted from solution.")
                return {}

            if len(candidate_features) > 1:
                # Gate 3: Multiple features found, require user selection
                logger.info(f"Multiple features found: {candidate_features}. Waiting for selection.")
                return {"candidate_features": candidate_features}

            # Single feature: Auto-select
            selected_feature = candidate_features[0]
            logger.info(f"Single feature auto-selected: {selected_feature}")
            # We continue execution with this feature, but we also update state return

        # 2. Generation Logic (Optimization: V0 Generation)
        # At this point we have a selected_feature (either from state or auto-selected)

        logger.info(f"Generating MVP for feature: {selected_feature}")

        spec = self._create_mvp_spec(
            app_name=state.selected_idea.title,
            feature=selected_feature,
            idea_context=f"{state.selected_idea.problem} -> {state.selected_idea.unique_value_prop}"
        )

        try:
            v0_client = V0Client(api_key=self.settings.v0_api_key.get_secret_value() if self.settings.v0_api_key else None)

            # Construct a prompt for v0 from the spec
            v0_prompt = (
                f"Create a {spec.ui_style} React component using Tailwind CSS for '{spec.app_name}'. "
                f"Core Feature: {spec.core_feature}. "
                f"Include components: {', '.join(spec.components)}."
            )

            url = v0_client.generate_ui(v0_prompt)
            logger.info(f"MVP Generated: {url}")

            return {
                "mvp_spec": spec,
                "mvp_url": url,
                "selected_feature": selected_feature, # Ensure state reflects selection
                "candidate_features": candidate_features # Ensure candidates are persisted if newly found
            }

        except Exception:
            logger.exception("Failed to generate MVP via v0")
            # Return partial state (spec created but generation failed)
            return {
                "mvp_spec": spec,
                "selected_feature": selected_feature,
                "candidate_features": candidate_features
            }
