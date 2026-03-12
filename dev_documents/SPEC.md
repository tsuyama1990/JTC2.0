# Cycle 2 Specification: JTC Simulation (The Meeting)

## 1. Summary

The primary objective of **Cycle 2** is to implement the **Gekizume Simulation and Proxy Model** as part of the JTC 2.0. This cycle focuses on setting up the Persona Agents (Finance Manager, Sales Manager, and New Employee), implementing the debate sub-graph orchestrating these agents, and providing a Pyxel-based Retro UI to render the "Meeting Room" scene visually.

The idea is that after selecting a Lean Canvas ("Plan A"), the simulation takes over, showcasing the realistic "Gekizume" (harsh feedback) environment without direct user participation (De-identification), creating a psychological buffer.

## 2. System Architecture

### 2.1. File Structure

This cycle updates or creates the following file structure. **Bold** files are new or heavily modified in this cycle.

```ascii
.
├── dev_documents/
├── src/
│   ├── agents/
│   │   ├── base.py
│   │   ├── ideator.py
│   │   └── **personas.py**     # Finance, Sales, NewEmployee Agents
│   ├── core/
│   │   ├── config.py
│   │   ├── graph.py
│   │   ├── llm.py
│   │   ├── **nodes.py**        # Graph node implementations, including simulation run
│   │   └── **simulation.py**   # Debate sub-graph logic
│   ├── domain_models/
│   │   ├── lean_canvas.py
│   │   ├── state.py
│   │   └── **simulation.py**   # AgentState, DeGrootProfile, DialogueMessage
│   ├── tools/
│   │   └── search.py
│   ├── ui/
│   │   ├── **renderer.py**     # Pyxel simulation render logic
│   │   └── **nemawashi_view.py** # UI view component for influence network
│   └── main.py                 # Uses SimulationRenderer to start Pyxel app loop
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_domain_models.py
│   │   ├── test_ideator_agent.py
│   │   └── **test_simulation_logic.py**
│   └── uat/
│       ├── test_uat_cycle01.py
│       └── **test_uat_cycle02.py**
├── .env.example
├── pyproject.toml
└── README.md
```

### 2.2. Component Interaction

1.  **User** selects a Lean Canvas in `main.py`.
2.  **App** runs `run_simulation_mode()` passing the selected idea to `create_simulation_graph()`.
3.  **Simulation Thread** runs LangGraph nodes asynchronously, updating `GlobalState.debate_history`.
4.  **Persona Agents** (Finance, Sales, New Employee) take turns arguing about the problem, using the LLM and Research tools.
5.  **Pyxel UI** runs on the main thread, polling the `state_getter` periodically to draw the dialogs, colors, and simulation state.
6.  **Simulation** finishes when the defined turns run out or debate logic stops, and UI reflects the final outcomes.

## 3. Design Architecture

### 3.1. Domain Models (`src/domain_models/`)

We strictly use Pydantic models.

**`src/domain_models/simulation.py`**:
```python
from pydantic import BaseModel, ConfigDict, Field
from src.domain_models.enums import Role

class DeGrootProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    self_confidence: float = Field(0.5, ge=0.0, le=1.0)
    influence_weights: dict[str, float] = Field(default_factory=dict)

class AgentState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Role
    degroot_profile: DeGrootProfile = Field(default_factory=DeGrootProfile)

class DialogueMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Role
    content: str = Field(min_length=1)
    timestamp: float
```

**`src/domain_models/state.py`** (Partial additions):
```python
    debate_history: list[DialogueMessage] = Field(default_factory=list)
    simulation_active: bool = False
    agent_states: dict[Role, AgentState] = Field(default_factory=dict)
```

### 3.2. Agent Design (`src/agents/personas.py`)

-   **Role**: Finance Manager
    -   **Goal**: Critiques financial ROI, costs, and market risks.
-   **Role**: Sales Manager
    -   **Goal**: Evaluates sales feasibility, cannibalization, and immediate revenue.
-   **Role**: New Employee
    -   **Goal**: Passionately defends the idea but acknowledges weaknesses, representing the user.

## 4. Implementation Approach

1.  **Domain Setup**: Implement `DialogueMessage`, `AgentState`, and `DeGrootProfile` schemas. Update `GlobalState`.
2.  **Agent Creation**: Implement `PersonaAgent` and its specific subclasses (`FinanceAgent`, `SalesAgent`, `NewEmployeeAgent`) in `src/agents/personas.py`.
3.  **Graph Setup**: Implement `create_simulation_graph()` in `src/core/simulation.py` to route dialogue iteratively according to settings.
4.  **Pyxel UI**: Build `SimulationRenderer` in `src/ui/renderer.py` using Pyxel for retro styling, handling states correctly even in headless contexts.
5.  **Integration**: Connect the `SimulationRenderer` inside `main.py` allowing a graphical review of the generated debate.

## 5. Test Strategy

### 5.1. Unit Testing
-   **File**: `tests/unit/test_simulation_logic.py` and `tests/unit/test_domain_models.py`
-   **Scope**:
    -   Verify `AgentState` and `DialogueMessage` schema validations.
    -   Verify the turns generated by LLM mock update the `debate_history`.

### 5.2. Integration / UAT Testing
-   **File**: `tests/uat/test_uat_cycle02.py`
-   **Scope**:
    -   Run the sequence of a debate (New Employee -> Finance -> New Employee) and verify that state updates correspond correctly to the messages.
