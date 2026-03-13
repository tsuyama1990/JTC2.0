from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain_models.state import GlobalState


class StateValidator:
    """
    Validates the GlobalState transitions and requirements.
    Separated from the state model to keep logic clean and testable.
    """

    @staticmethod
    def validate_phase_requirements(state: "GlobalState") -> "GlobalState":
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
            import bleach

            # Use comprehensive HTML sanitization
            sanitized = bleach.clean(state.topic, tags=[], attributes={}, strip=True)
            # Remove null bytes
            sanitized = sanitized.replace("\x00", "")
            # Prevent control character injections
            sanitized = "".join(ch for ch in sanitized if ord(ch) >= 32 or ch in "\n\r\t")

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
            _check("agent_prompt_spec", "PMF")
            _check("experiment_plan", "PMF")

        elif state.phase == Phase.GOVERNANCE:
            _check("experiment_plan", "GOVERNANCE")
            _check("agent_prompt_spec", "GOVERNANCE")

        return state
