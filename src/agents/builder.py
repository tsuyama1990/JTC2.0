import logging
from collections.abc import Iterator
from itertools import islice
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from src.agents.base import BaseAgent
from src.core.config import get_settings
from src.core.utils import chunk_text
from src.domain_models.mvp import MVPSpec
from src.domain_models.state import GlobalState
from src.tools.v0_client import V0Client

logger = logging.getLogger(__name__)


class FeatureList(BaseModel):
    """List of extracted features."""

    features: list[str] = Field(
        ..., description="List of distinct features found in the solution description"
    )


class BuilderAgent(BaseAgent):
    """
    Agent responsible for MVP Construction (Cycle 5).
    It parses the solution into features, enforcing Gate 3 (Problem-Solution Fit),
    and generates a UI using v0.dev.
    """

    def __init__(self, llm: ChatOpenAI) -> None:
        self.llm = llm
        self.settings = get_settings()
        if not self.settings.v0_api_key:
            msg = "Missing required API configuration"
            raise ValueError(msg)

    def _create_content_stream(
        self, solution_description: str | Iterator[str], chunk_size: int
    ) -> Iterator[str]:
        """Normalize input to an iterator of validated text chunks."""
        if isinstance(solution_description, str):
            stream = chunk_text(solution_description, chunk_size)
        else:
            stream = solution_description

        for chunk in stream:
            if not chunk or not chunk.strip():
                continue
            if len(chunk.strip()) < 5:
                logger.warning(f"Chunk too short, skipping: {chunk}")
                continue
            yield chunk

    def _extract_features(self, solution_description: str | Iterator[str]) -> Iterator[str]:
        """
        Extract discrete features from the solution description using LLM.
        Implements chunking for large inputs to prevent memory overload.
        Accepts string or iterator for scalability.
        Yields unique features as they are found to avoid loading all into memory.
        """
        # Chunking logic for memory safety using generator
        chunk_size = self.settings.feature_chunk_size

        # Use a set to stream deduplication as we process chunks
        unique_features: set[str] = set()

        for chunk in self._create_content_stream(solution_description, chunk_size):
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", "You are a product manager. Extract distinct features from the solution description."),
                    ("user", f"Solution Description: {chunk}\n\nList the features:"),
                ]
            )
            chain = prompt | self.llm.with_structured_output(FeatureList)
            try:
                result: FeatureList | Any = chain.invoke({})
                if isinstance(result, FeatureList):
                    # Yield unique features immediately
                    for feature in result.features:
                        if feature not in unique_features:
                            unique_features.add(feature)
                            yield feature
            except Exception as e:
                logger.exception("Failed to extract features from chunk")
                err_msg = f"Feature extraction failed: {e}"
                raise RuntimeError(err_msg) from e

    def _create_mvp_spec(self, app_name: str, feature: str, idea_context: str) -> MVPSpec:
        """
        Create a detailed MVP Spec for the selected feature.
        """
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.settings.prompts.v0_system),
                ("user", self.settings.prompts.v0_user.format(
                    app_name=app_name,
                    feature=feature,
                    idea_context=idea_context
                )),
            ]
        )
        chain = prompt | self.llm.with_structured_output(MVPSpec)
        try:
            result: MVPSpec | Any = chain.invoke({})
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
            # Consume generator up to a reasonable limit to prevent unbounded memory usage
            # even if the LLM hallucinates an infinite stream (unlikely but safe).
            MAX_FEATURES = 100
            feature_gen = self._extract_features(state.selected_idea.solution)

            # Safely yield an iterator limited to MAX_FEATURES, avoiding list cast (OOM safety)
            logger.debug("Finished extracting features")
            return {"candidate_features": islice(feature_gen, MAX_FEATURES)}

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
            idea_context=f"{state.selected_idea.problem} -> {state.selected_idea.unique_value_prop}",
        )

        def sanitize_input(text: str) -> str:
            """Sanitize user input to prevent prompt injection."""
            import html
            import re

            # HTML escape to prevent markup injection
            text = html.escape(text)
            # Remove brackets that could be used for template injection
            return re.sub(r"[{}]", "", text)

        sanitized_app_name = sanitize_input(spec.app_name)
        sanitized_core_feature = sanitize_input(spec.core_feature)
        sanitized_components = [sanitize_input(c) for c in spec.components]

        # Use ChatPromptTemplate to properly format the prompt with sanitized inputs
        prompt_template = ChatPromptTemplate.from_template(
            "Create a {ui_style} React component using Tailwind CSS for '{app_name}'. "
            "Core Feature: {core_feature}. "
            "Include components: {components}."
        )
        v0_prompt = prompt_template.format(
            ui_style=spec.ui_style,
            app_name=sanitized_app_name,
            core_feature=sanitized_core_feature,
            components=", ".join(sanitized_components),
        )
        spec.v0_prompt = v0_prompt

        # We rely on exceptions propagating to the caller (safe_node wrapper)
        # Standardized Error Handling: Do not swallow critical failures here.
        if not self.settings.v0_api_key:
            msg = "V0 API Key is missing. Cannot generate UI."
            logger.error(msg)
            raise ValueError(msg)

        try:
            v0_client = V0Client(api_key=self.settings.v0_api_key.get_secret_value())
            url = v0_client.generate_ui(v0_prompt)
        except Exception:
            logger.exception("V0 generation failed due to network or API error")
            # Re-raise the original exception to preserve standard error types (like V0GenerationError)
            raise

        logger.info(f"MVP Generated: {url}")

        return {
            "mvp_spec": spec,
            "mvp_url": url,
            "selected_feature": selected_feature,
        }

    def run(self, state: GlobalState) -> dict[str, Any]:
        """
        Agent entry point. Orchestrates the MVP generation process.
        Validates state prerequisites and handles overall execution errors.
        """
        if not state.selected_idea:
            logger.error("BuilderAgent requires a selected_idea in the state.")
            return {}

        if not state.selected_feature and not state.candidate_features:
            logger.info("No features selected or proposed yet. Proposing features...")
            return self.propose_features(state)

        try:
            logger.info("Executing MVP generation...")
            return self.generate_mvp(state)
        except Exception:
            logger.exception("BuilderAgent run failed during MVP generation.")
            # Return current state unchanged on failure, relying on outer loop/circuit breaker
            return {}
