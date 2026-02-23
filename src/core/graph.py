from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.agents.ideator import IdeatorAgent
from src.core.llm import get_llm
from src.domain_models.state import GlobalState


def create_app() -> CompiledStateGraph:  # type: ignore[type-arg]
    """Create and compile the LangGraph application."""
    llm = get_llm()
    ideator = IdeatorAgent(llm)

    workflow = StateGraph(GlobalState)

    # Add Nodes
    workflow.add_node("ideator", ideator.run)

    # Edges
    workflow.set_entry_point("ideator")
    workflow.add_edge("ideator", END)

    return workflow.compile()
