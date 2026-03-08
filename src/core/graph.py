import logging
from typing import Any

from langgraph.graph.state import CompiledStateGraph

from src.core.workflow_builder import WorkflowBuilder

logger = logging.getLogger(__name__)


def create_app() -> CompiledStateGraph[Any, Any]:
    """
    Create and compile the LangGraph application.
    """
    builder = WorkflowBuilder()
    return builder.build()
