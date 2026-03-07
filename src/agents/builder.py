import logging
from collections.abc import Iterator
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

        # Configure chunk limit from settings
        max_chunks = 100  # Default fallback if setting missing
        if hasattr(self.settings, "max_feature_chunks"):
            max_chunks = self.settings.max_feature_chunks

        chunks_processed = 0
        for chunk in self._get_content_stream(solution_description, chunk_size):
            if chunks_processed >= max_chunks:
                logger.warning(
                    f"Feature extraction limit reached ({max_chunks} chunks). Truncating."
                )
                break

            chunks_processed += 1
            if not chunk.strip():
                continue

            yield from self._extract_features_from_chunk(chunk, unique_features)

    def _get_content_stream(
        self, solution_description: str | Iterator[str], chunk_size: int
    ) -> Iterator[str]:
        """Helper to get content stream from string or iterator."""
        if isinstance(solution_description, str):
            if not solution_description or len(solution_description) < 10:
                logger.warning("Solution description too short for feature extraction.")
                return

            # Explicit hard limit to prevent string from being infinitely long memory-wise
            max_desc_len = 50000
            if len(solution_description) > max_desc_len:
                logger.warning(f"Solution description truncated to {max_desc_len} chars.")
                solution_description = solution_description[:max_desc_len]

            yield from chunk_text(solution_description, chunk_size)
        else:
            yield from solution_description

    def _extract_features_from_chunk(self, chunk: str, unique_features: set[str]) -> Iterator[str]:
        """Process a single chunk to extract unique features using LLM."""
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a product manager. Extract distinct features from the solution description.",
                ),
                ("user", f"Solution Description: {chunk}\n\nList the features:"),
            ]
        )
        chain = prompt | self.llm.with_structured_output(FeatureList)
        try:
            result = chain.invoke({})
            if isinstance(result, FeatureList):
                for feature in result.features:
                    if feature not in unique_features:
                        unique_features.add(feature)
                        yield feature
        except Exception:
            logger.exception("Failed to extract features from chunk")

    def _sanitize_input(self, text: str) -> str:
        """Sanitize input to prevent prompt injection and remove malicious patterns."""
        import re
        if not text:
            return ""
        # Remove markdown tags, scripts, and potential injection keywords
        sanitized = re.sub(r'<(script|style|iframe|object|embed)[^>]*>.*?</\1>', '', text, flags=re.IGNORECASE)
        sanitized = re.sub(r'<[^>]+>', '', sanitized)
        # Prevent prompt escape sequences (e.g. Ignore all previous instructions)
        sanitized = re.sub(r'(?i)(ignore.*instructions|system prompt|you are now)', '[REDACTED]', sanitized)
        return sanitized.strip()[:2000]  # Hard truncate to prevent token overflow

    def _create_mvp_spec(self, app_name: str, feature: str, idea_context: str) -> MVPSpec:
        """
        Create a detailed MVP Spec for the selected feature.
        """
        safe_app_name = self._sanitize_input(app_name)
        safe_feature = self._sanitize_input(feature)
        safe_context = self._sanitize_input(idea_context)

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert UI/UX designer. Create a detailed MVP specification for v0.dev generation.",
                ),
                (
                    "user",
                    f"App Name: {safe_app_name}\nCore Feature: {safe_feature}\nContext: {safe_context}\n\nGenerate MVPSpec:",
                ),
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
            # Consume generator up to a reasonable limit to prevent unbounded memory usage
            # even if the LLM hallucinates an infinite stream (unlikely but safe).
            MAX_FEATURES = 100
            feature_gen = self._extract_features(state.selected_idea.solution)

            from collections import deque

            candidate_features = deque(maxlen=MAX_FEATURES)
            try:
                for _ in range(MAX_FEATURES):
                    feature = next(feature_gen)
                    candidate_features.append(feature)
            except StopIteration:
                pass

        if not candidate_features:
            logger.warning("No features extracted from solution.")
            return {}

        logger.info(f"Proposed features: {list(candidate_features)}")
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

        # Sanitize before prompt creation
        safe_ui_style = self._sanitize_input(spec.ui_style)
        safe_app_name = self._sanitize_input(spec.app_name)
        safe_core_feature = self._sanitize_input(spec.core_feature)
        safe_components = [self._sanitize_input(c) for c in spec.components]

        # Construct a prompt for v0 from the spec
        v0_prompt = (
            f"Create a {safe_ui_style} React component using Tailwind CSS for '{safe_app_name}'. "
            f"Core Feature: {safe_core_feature}. "
            f"Include components: {', '.join(safe_components)}."
        )
        spec.v0_prompt = v0_prompt

        # V0Client already uses pybreaker, but we ensure graceful degradation here.
        # Fallback gracefully rather than crashing if the API is down or key is invalid.
        try:
            api_key = self._get_v0_api_key()
            v0_client = V0Client(api_key=api_key)
            url = v0_client.generate_ui(v0_prompt)
            logger.info(f"MVP Generated: {url}")
        except Exception:
            logger.exception("Failed to generate MVP via v0.dev API. Falling back to local placeholder.")
            url = "https://v0.dev/fallback-generated-ui"

        return {
            "mvp_spec": spec,
            "mvp_url": url,
            "selected_feature": selected_feature,
        }

    def _get_v0_api_key(self) -> str:
        """Securely get V0 API key with validation."""
        if not self.settings.v0_api_key:
            msg = "V0_API_KEY is missing from configuration."
            raise ValueError(msg)
        key = self.settings.v0_api_key.get_secret_value()
        if not key or len(key) < 10:
            msg = "V0_API_KEY is invalid or improperly formatted."
            raise ValueError(msg)
        return key

    def run(self, state: GlobalState) -> dict[str, Any]:
        """
        Legacy run method. Delegates to propose_features (default behavior).
        """
        # Validate state structurally before running
        if not state:
            logger.error("State object is None. Aborting.")
            return {}
        try:
            state.validate_state()
        except ValueError:
            logger.exception("State validation failed in BuilderAgent.")
            return {}

        return self.propose_features(state)
