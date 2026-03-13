from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain_models.state import GlobalState


class StateValidator:
    """
    Validates the GlobalState transitions and requirements.
    Separated from the state model to keep logic clean and testable.
    """

    @staticmethod
    def _sanitize_topic(topic: str) -> str:
        """Apply strict whitelisting and HTML sanitization to topic string."""
        import unicodedata

        import bleach

        sanitized = bleach.clean(topic, tags=[], attributes={}, strip=True)
        sanitized = sanitized.replace("\x00", "")

        sanitized_chars = []
        for ch in sanitized:
            cat = unicodedata.category(ch)
            if cat.startswith(("L", "N", "P", "Z")):
                sanitized_chars.append(ch)

        return "".join(sanitized_chars)

    @staticmethod
    def validate_phase_requirements(state: "GlobalState") -> "GlobalState":  # noqa: C901
        """
        Validate that required fields are present for the current phase.

        Args:
            state: The GlobalState instance to validate.

        Returns:
            The validated state if successful.

        Raises:
            ValueError: If requirements for the phase are not met.
        """

        from src.domain_models.enums import Phase

        if not isinstance(state.phase, Phase):
            msg = f"Invalid phase enum value: {state.phase}"
            raise TypeError(msg)

        def _check(field_name: str, phase_name: str) -> None:
            if getattr(state, field_name, None) is None:
                msg = f"Missing field '{field_name}' required for the {phase_name} phase."
                raise ValueError(msg)

        # Basic topic sanitization
        if state.topic:
            import unicodedata

            import bleach

            # Use comprehensive HTML sanitization
            sanitized = bleach.clean(state.topic, tags=[], attributes={}, strip=True)
            # Remove null bytes
            sanitized = sanitized.replace("\x00", "")

            # Comprehensive Unicode and control character validation (Whitelist approach)
            sanitized_chars = []
            for ch in sanitized:
                # Whitelist categories: Letters (L), Numbers (N), Punctuation (P), Space (Z)
                cat = unicodedata.category(ch)
                if cat.startswith(("L", "N", "P", "Z")):
                    sanitized_chars.append(ch)

            sanitized = "".join(sanitized_chars)

            # Note: We removed the naive SQL keyword string replacement as per security audit.
            # State topic is used strictly as an LLM context parameter, not directly within DB queries.
            # If database persistence is added, parameterized queries (e.g. SQLAlchemy) must be used.
            state.topic = sanitized

        if state.phase == Phase.VERIFICATION:
            _check("target_persona", "VERIFICATION")

        elif state.phase == Phase.SOLUTION:
            _check("mental_model", "SOLUTION")
            _check("customer_journey", "SOLUTION")
            _check("sitemap_and_story", "SOLUTION")

        elif state.phase == Phase.PMF:
            _check("mvp_definition", "PMF")

        elif state.phase == Phase.GOVERNANCE:
            _check("experiment_plan", "GOVERNANCE")
            _check("agent_prompt_spec", "GOVERNANCE")

        return state
