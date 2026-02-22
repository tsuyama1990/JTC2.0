# Cycle 1 Specification: Foundation & Ideation

## 1. Summary

The primary objective of **Cycle 1** is to establish the project's foundational architecture and implement the **Ideation Engine**. This cycle focuses on setting up the **LangGraph** orchestrator, defining the core `GlobalState`, and creating the **Ideator Agent** capable of generating 10 valid Lean Canvas drafts based on a user's initial prompt (e.g., "A business for elderly care").

We will also implement **Gate 1 (Idea Verification)**, where the user must select a single "Plan A" from the generated options to proceed. This establishes the pattern for subsequent Human-in-the-Loop (HITL) interactions.

## 2. System Architecture

### 2.1. File Structure

This cycle will create the following file structure. **Bold** files are new or modified in this cycle.

```ascii
.
├── dev_documents/
├── **src/**
│   ├── **__init__.py**
│   ├── **agents/**
│   │   ├── **__init__.py**
│   │   ├── **base.py**         # Base Agent Class
│   │   └── **ideator.py**      # Ideator Agent (Generates Lean Canvases)
│   ├── **core/**
│   │   ├── **__init__.py**
│   │   ├── **config.py**       # Env Vars (OPENAI_API_KEY, TAVILY_API_KEY)
│   │   ├── **graph.py**        # Main LangGraph Definition
│   │   ├── **state.py**        # GlobalState & LeanCanvas Pydantic Models
│   │   └── **llm.py**          # LLM Client Factory (OpenAI)
│   ├── **tools/**
│   │   ├── **__init__.py**
│   │   └── **search.py**       # Tavily Search Tool Wrapper
│   └── **main.py**             # CLI Entry Point for Testing
├── **tests/**
│   ├── **__init__.py**
│   ├── **conftest.py**
│   └── **test_ideation.py**    # Unit Tests for Ideator Agent
├── .env.example
├── pyproject.toml
└── README.md
```

### 2.2. Component Interaction

1.  **User** runs `main.py` with a business topic.
2.  **Graph** initializes `GlobalState`.
3.  **Ideator Agent** receives the state, uses **Tavily** to research the topic.
4.  **Ideator Agent** generates 10 `LeanCanvas` objects.
5.  **Graph** pauses at `Gate 1`.
6.  **User** selects an ID (0-9).
7.  **Graph** updates `GlobalState.selected_canvas` and terminates (for this cycle).

## 3. Design Architecture

### 3.1. Domain Models (`src/core/state.py`)

We will use Pydantic to ensure strict typing and validation.

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class Phase(str, Enum):
    IDEATION = "ideation"
    VERIFICATION = "verification"
    SOLUTION = "solution"
    PMF = "pmf"

class LeanCanvas(BaseModel):
    id: int
    title: str = Field(..., description="A catchy name for the idea")
    problem: str = Field(..., description="Top 3 problems")
    customer_segments: str = Field(..., description="Target customers")
    unique_value_prop: str = Field(..., description="Single clear compelling message")
    solution: str = Field(..., description="Top 3 features")
    status: str = "draft"

class GlobalState(BaseModel):
    """The central state of the LangGraph workflow."""
    phase: Phase = Phase.IDEATION
    topic: str = ""
    generated_ideas: List[LeanCanvas] = []
    selected_idea: Optional[LeanCanvas] = None
    messages: List[str] = []
```

### 3.2. Agent Design (`src/agents/ideator.py`)

-   **Role**: Startup Ideator / Researcher.
-   **Goal**: Generate high-quality, distinct business ideas.
-   **Constraint**: Must produce exactly 10 ideas.
-   **Tools**: `TavilySearch`.

## 4. Implementation Approach

1.  **Project Setup**: Initialize `uv`, install `langgraph`, `langchain-openai`, `pydantic`, `tavily-python`.
2.  **Core Logic**: Implement `GlobalState` and `LeanCanvas` models in `src/core/state.py`.
3.  **LLM Setup**: Create `src/core/llm.py` to configure the ChatOpenAI client.
4.  **Agent Creation**: Implement `IdeatorAgent` in `src/agents/ideator.py`. It should take a topic, search Tavily for trends, and output a JSON list of 10 ideas.
5.  **Graph Construction**: Define the StateGraph in `src/core/graph.py`. Add the `ideator` node and a conditional edge to `selection`.
6.  **CLI Interface**: Create a simple `main.py` to run the graph and print the 10 ideas, prompting for user input.

## 5. Test Strategy

### 5.1. Unit Testing
-   **File**: `tests/test_ideation.py`
-   **Scope**:
    -   Verify `LeanCanvas` validation raises errors on missing fields.
    -   Mock the LLM response to ensure `IdeatorAgent` correctly parses JSON into `List[LeanCanvas]`.
    -   Mock Tavily search to avoid API costs during testing.

### 5.2. Integration Testing
-   **Scope**:
    -   Run the full graph with a mock LLM.
    -   Verify the state transitions from `START` -> `ideator` -> `selection`.
    -   Verify that after selection, the `selected_idea` is correctly populated in the state.
