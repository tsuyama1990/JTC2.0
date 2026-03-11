from src.domain_models.state import GlobalState


class ContextBuilderService:
    """Service to build prompt context from state."""

    @staticmethod
    def build_debate_context(state: GlobalState) -> str:
        """Construct the conversation history context."""
        context_parts = ["\nDEBATE HISTORY:"]

        if state.selected_idea:
            context_parts.insert(0, f"UVP: {state.selected_idea.unique_value_prop}")
            context_parts.insert(0, f"SOLUTION: {state.selected_idea.solution}")
            context_parts.insert(0, f"PROBLEM: {state.selected_idea.problem}")
            context_parts.insert(0, f"IDEA: {state.selected_idea.title}")

        context_parts.extend(f"{msg.role}: {msg.content}" for msg in state.debate_history)

        return "\n".join(context_parts)
