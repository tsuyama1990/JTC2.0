from typing import TYPE_CHECKING

from src.core.config import get_settings

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

        settings = get_settings()

        # Phase order defining the strict progression.
        # This mapping is required because Python enum comparison is not strictly ordered by definition.
        phase_order = {
            Phase.IDEATION: 1,
            Phase.CPF: 2,
            Phase.PSF: 3,
            Phase.VALIDATION: 4,
            Phase.OUTPUT: 5,
            Phase.GOVERNANCE: 6,
        }

        current_phase_idx = phase_order.get(state.phase, 0)

        # Enforce that if we are at a higher phase, the requirements of the lower phases must have been met
        # (State progression tracking logic)

        if current_phase_idx >= phase_order[Phase.CPF] and state.selected_idea is None:
            msg = "Must select an idea before proceeding to CPF Phase."
            raise ValueError(msg)

        if current_phase_idx >= phase_order[Phase.PSF]:
            if state.target_persona is None:
                raise ValueError(settings.errors.missing_persona)
            if state.value_proposition_canvas is None:
                msg = "Must have Value Proposition Canvas before proceeding to PSF Phase."
                raise ValueError(msg)

        if current_phase_idx >= phase_order[Phase.VALIDATION] and (
            state.mental_model_diagram is None or state.sitemap_and_story is None
        ):
            msg = "Must have Mental Model and Sitemap before proceeding to Validation Phase."
            raise ValueError(msg)

        if current_phase_idx >= phase_order[Phase.GOVERNANCE] and (
            state.agent_prompt_spec is None or state.experiment_plan is None
        ):
            msg = "Must have Agent Prompt Spec and Experiment Plan before proceeding to Governance Phase."
            raise ValueError(msg)

        return state
