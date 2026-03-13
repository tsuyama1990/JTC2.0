import re
from typing import TYPE_CHECKING

from src.domain_models.enums import Phase

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

        if not isinstance(state.phase, Phase):
            msg = f"Invalid phase enum value: {state.phase}"
            raise TypeError(msg)

        def _check(field_name: str, phase_name: str) -> None:
            if getattr(state, field_name, None) is None:
                msg = f"Missing field '{field_name}' required for the {phase_name} phase."
                raise ValueError(msg)

        # Basic topic sanitization
        if state.topic:
            sanitized = re.sub(r"<[^>]*>", "", state.topic)
            sanitized = sanitized.replace("\x00", "")
            sanitized = re.sub(
                r"(?i)\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|EXEC)\b",
                "[REDACTED]",
                sanitized,
            )
            sanitized = sanitized.replace("--", "").replace(";", "")
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
