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

        if current_phase_idx >= phase_order[Phase.CPF]:
            # Before going to CPF, we must have selected an idea
            if state.selected_idea is None:
                raise ValueError("Must select an idea before proceeding to CPF Phase.")

        if current_phase_idx >= phase_order[Phase.PSF]:
            # Before going to PSF, we must have CPF artifacts
            if state.target_persona is None:
                raise ValueError(settings.errors.missing_persona)
            if state.value_proposition_canvas is None:
                 raise ValueError("Must have Value Proposition Canvas before proceeding to PSF Phase.")

        if current_phase_idx >= phase_order[Phase.VALIDATION]:
            # Before going to Validation, we must have PSF artifacts
            if state.mental_model_diagram is None or state.sitemap_and_story is None:
                 raise ValueError("Must have Mental Model and Sitemap before proceeding to Validation Phase.")

        if current_phase_idx >= phase_order[Phase.OUTPUT]:
             pass # MVP is created *during* OUTPUT, so we can't require it beforehand

        if current_phase_idx >= phase_order[Phase.GOVERNANCE]:
             if state.agent_prompt_spec is None or state.experiment_plan is None:
                 raise ValueError("Must have Agent Prompt Spec and Experiment Plan before proceeding to Governance Phase.")

        return state
