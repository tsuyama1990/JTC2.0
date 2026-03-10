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

        if state.phase == Phase.VERIFICATION and state.target_persona is None:
            msg = "Target Persona must be established"
            raise ValueError(msg)

        if state.phase == Phase.SOLUTION and state.mvp_definition is None:
            msg = "MVP Definition is required"
            raise ValueError(msg)

        return state
