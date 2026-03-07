# Cycle 2 Specification: JTC Simulation (The Meeting)

## 1. Summary

The primary objective of **Cycle 2** is to implement the **JTC Simulation Engine**, specifically the "Gekizume" (harsh grilling) meeting. This involves creating distinct **Persona Agents** (Finance Manager, Sales Manager, New Employee Proxy) and a **Debate Orchestrator** that facilitates a turn-based argument about the user's selected business plan.

We will also introduce the **Pyxel UI** (Retro RPG interface) as a viewing window. The user will not participate directly in the debate but will watch their "New Employee" proxy defend the idea against skeptical department heads. This implements the "De-identification" psychological safety mechanism.

## 2. System Architecture

### 2.1. File Structure

This cycle builds upon Cycle 1. **Bold** files are new or modified.

```ascii
.
├── dev_documents/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── ideator.py
│   │   └── **personas.py**     # Finance, Sales, New Employee Agents
│   ├── core/
│   │   ├── config.py
│   │   ├── graph.py        # Updated with Simulation Sub-graph
│   │   ├── state.py        # Updated GlobalState with Debate History
│   │   ├── llm.py
│   │   └── **simulation.py**   # Debate Logic / Turn Management
│   ├── tools/
│   │   ├── __init__.py
│   │   └── search.py
│   ├── **ui/**
│   │   ├── **__init__.py**
│   │   ├── **renderer.py**     # Pyxel: Window & Text Rendering
│   │   └── **assets/**         # Placeholder for sprites
│   └── main.py             # Updated to launch Pyxel
├── tests/
│   ├── test_ideation.py
│   └── **test_simulation.py**  # Unit Tests for Debate Logic
├── .env.example
├── pyproject.toml
└── README.md
```

### 2.2. Component Interaction

1.  **Orchestrator** passes the `selected_idea` to the **Simulation Sub-graph**.
2.  **New Employee Agent** presents the idea (Initial Pitch).
3.  **Finance Manager** analyzes the idea using **Tavily** for market data and critiques costs/risks.
4.  **Sales Manager** critiques feasibility/cannibalization.
5.  **Debate Loop** continues for 3-5 turns.
6.  **Pyxel UI** polls the `GlobalState` and renders the dialogue as RPG text boxes.

## 3. Design Architecture

### 3.1. Domain Models (`src/core/state.py`)

```python
from pydantic import BaseModel, Field
from typing import List, Literal

class Role(str, Enum):
    NEW_EMPLOYEE = "New Employee"
    FINANCE = "Finance Manager"
    SALES = "Sales Manager"
    CPO = "CPO"

class DialogueMessage(BaseModel):
    role: Role
    content: str
    timestamp: float

class GlobalState(BaseModel):
    # ... previous fields ...
    debate_history: List[DialogueMessage] = []
    simulation_active: bool = False
```

### 3.2. Agent Design (`src/agents/personas.py`)

-   **Finance Manager**:
    -   **Persona**: Risk-averse, obsessed with ROI, skeptical of unproven markets.
    -   **System Prompt**: "You are a conservative Finance Manager at a large Japanese traditional company. You always ask about cost, risk, and timeline. You use Tavily to find reasons why new ideas will fail."
-   **Sales Manager**:
    -   **Persona**: Pragmatic, focused on existing customers, hates channel conflict.
    -   **System Prompt**: "You are an aggressive Sales Manager. You worry about cannibalizing existing products and whether the sales force can actually sell this."
-   **New Employee (Proxy)**:
    -   **Persona**: Enthusiastic but inexperienced. Tries to defend the idea but gets overwhelmed.
    -   **System Prompt**: "You are a new employee presenting a startup idea. You are nervous. You try to answer questions but often falter."

## 4. Implementation Approach

1.  **Agent Logic**: Implement `PersonaAgent` class inheriting from `BaseAgent`. Configure system prompts for Finance, Sales, and New Employee.
2.  **Simulation Graph**: In `src/core/simulation.py`, define a sub-graph that cycles between:
    -   `NewEmployee` (Pitch) -> `Finance` (Critique) -> `NewEmployee` (Defense) -> `Sales` (Critique) -> `NewEmployee` (Defense).
3.  **Pyxel Integration**:
    -   Create `src/ui/renderer.py`. Initialize a Pyxel window (160x120 or similar).
    -   Implement a loop that reads `GlobalState.debate_history` and displays the latest message.
    -   Use simple colored rectangles to represent agents if sprites are unavailable.
4.  **Main Loop Update**: Modify `main.py` to run the LangGraph in a background thread while the main thread runs the Pyxel `App.run()` loop.

## 5. Test Strategy

### 5.1. Unit Testing
-   **File**: `tests/test_simulation.py`
-   **Scope**:
    -   Verify `FinanceAgent` calls Tavily when presented with a claim.
    -   Verify `PersonaAgent` outputs match the expected role (e.g., Finance mentions "ROI").

### 5.2. Integration Testing
-   **Scope**:
    -   Run the simulation with a mock idea.
    -   Verify that the conversation history grows.
    -   Verify that the turn-taking logic functions (Finance doesn't speak twice in a row).
