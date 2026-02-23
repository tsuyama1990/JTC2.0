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
        Implements chunking for large inputs to prevent memory overload.
        """
        if not solution_description or len(solution_description) < 10:
            logger.warning("Solution description too short for feature extraction.")
            return []

        # Chunking logic for memory safety
        CHUNK_SIZE = 2000
        all_features: list[str] = []

        chunks = [
            solution_description[i : i + CHUNK_SIZE]
            for i in range(0, len(solution_description), CHUNK_SIZE)
        ]

        for chunk in chunks:
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", "You are a product manager. Extract distinct features from the solution description."),
                    ("user", f"Solution Description: {chunk}\n\nList the features:")
                ]
            )
            chain = prompt | self.llm.with_structured_output(FeatureList)
            try:
                result = chain.invoke({})
                if isinstance(result, FeatureList):
                    all_features.extend(result.features)
            except Exception:
                logger.exception("Failed to extract features from chunk")
                continue

        # Deduplicate features while preserving order
        seen = set()
        unique_features = []
        for f in all_features:
            if f not in seen:
                seen.add(f)
                unique_features.append(f)

        return unique_features

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

    def propose_features(self, state: GlobalState) -> dict[str, Any]:
        """
        Gate 3 Preparation: Extract features for user selection.
        """
        if not state.selected_idea:
            logger.warning("No idea selected for Builder Agent.")
            return {}

        candidate_features = state.candidate_features
        if not candidate_features:
            candidate_features = self._extract_features(state.selected_idea.solution)

        if not candidate_features:
            logger.warning("No features extracted from solution.")
            return {}

        logger.info(f"Proposed features: {candidate_features}")
        return {"candidate_features": candidate_features}

    def generate_mvp(self, state: GlobalState) -> dict[str, Any]:
        """
        Execute MVP Generation (Cycle 5) for the selected feature.
        """
        if not state.selected_idea:
            logger.warning("No idea selected for MVP Generation.")
            return {}

        selected_feature = state.selected_feature
        if not selected_feature:
            # Fallback: Check if there's only one candidate
            if state.candidate_features and len(state.candidate_features) == 1:
                selected_feature = state.candidate_features[0]
            else:
                logger.error("No feature selected for MVP Generation.")
                return {}

        logger.info(f"Generating MVP for feature: {selected_feature}")

        spec = self._create_mvp_spec(
            app_name=state.selected_idea.title,
            feature=selected_feature,
            idea_context=f"{state.selected_idea.problem} -> {state.selected_idea.unique_value_prop}"
        )

        # Construct a prompt for v0 from the spec
        v0_prompt = (
            f"Create a {spec.ui_style} React component using Tailwind CSS for '{spec.app_name}'. "
            f"Core Feature: {spec.core_feature}. "
            f"Include components: {', '.join(spec.components)}."
        )
        spec.v0_prompt = v0_prompt

        try:
            v0_client = V0Client(api_key=self.settings.v0_api_key.get_secret_value() if self.settings.v0_api_key else None)
            url = v0_client.generate_ui(v0_prompt)
        except Exception:
            logger.exception("Failed to generate MVP via v0")
            # Return partial state (spec created but generation failed)
            return {
                "mvp_spec": spec,
                "selected_feature": selected_feature,
            }
        else:
            logger.info(f"MVP Generated: {url}")

            return {
                "mvp_spec": spec,
                "mvp_url": url,
                "selected_feature": selected_feature,
            }

    def run(self, state: GlobalState) -> dict[str, Any]:
        """
        Legacy run method. Delegates to propose_features (default behavior).
        """
        return self.propose_features(state)
