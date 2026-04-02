# Cycle 5 Specification: MVP Generation (Agent Prompt Spec)

## 1. Summary

The primary objective of **Cycle 5** is to bridge the gap between "Idea" and "Execution" by automating the creation of a **Minimum Viable Product (MVP)**. We will generate the `AgentPromptSpec` and `ExperimentPlan` which can be consumed by AI coders (like Cursor, Windsurf) to generate high-fidelity React/Tailwind CSS user interfaces. This correctly aligns with the Remastered Edition architecture.

This cycle implements **Gate 3 (Problem-Solution Fit)**, where the user must prune the feature list down to a single "Must-Have" feature before generation. The system then constructs a detailed prompt for AI coders and returns the generated plan.

## 2. System Architecture

### 2.1. File Structure

This cycle adds the Code Generation Layer. **Bold** files are new or modified.

```ascii
.
├── dev_documents/
├── src/
│   ├── agents/
│   │   ├── ...
│   │   └── **builder.py**      # MVP Architect Agent
│   ├── core/
│   │   ├── ...
│   │   └── state.py        # GlobalState with AgentPromptSpec and ExperimentPlan
│   └── main.py
├── tests/
│   └── **test_builder_agent.py**          # Unit Tests for Builder Agent
├── .env.example
├── pyproject.toml
└── README.md
```

### 2.2. Component Interaction

1.  **User** confirms the single "Core Feature" to build.
2.  **Builder Agent** constructs an `AgentPromptSpec` and `ExperimentPlan` based on all prior contexts.
3.  **System** displays the generated outputs in the console/UI.

## 3. Design Architecture

### 3.1. Domain Models (`src/domain_models/state.py`, `src/domain_models/agent_spec.py`, `src/domain_models/experiment.py`)

```python
class StateMachine(BaseModel):
    success: str
    loading: str
    error: str
    empty: str

class AgentPromptSpec(BaseModel):
    sitemap: str
    routing_and_constraints: str
    core_user_story: UserStory
    state_machine: StateMachine
    validation_rules: str
    mermaid_flowchart: str

class MetricTarget(BaseModel):
    metric_name: str
    target_value: str
    measurement_method: str

class ExperimentPlan(BaseModel):
    riskiest_assumption: str
    experiment_type: str
    acquisition_channel: str
    aarrr_metrics: list[MetricTarget]
    pivot_condition: str

class GlobalState(BaseModel):
    # ... previous fields ...
    agent_prompt_spec: Optional[AgentPromptSpec] = None
    experiment_plan: Optional[ExperimentPlan] = None
```

## 4. Implementation Approach

1.  **Domain Setup**: Create `AgentPromptSpec`, `StateMachine`, `MetricTarget`, and `ExperimentPlan` Pydantic models.
2.  **Builder Agent**: Implement `BuilderAgent`. Its job is to take all generated context (`ValuePropositionCanvas`, `MentalModelDiagram`, `CustomerJourney`, `SitemapAndStory`) and turn it into a concrete AI coder prompt and experiment plan. It must use exponential backoff and circuit breakers for resilience.
3.  **Integration**: Add the spec generation node to the LangGraph workflow.

## 5. Test Strategy

### 5.1. Unit Testing
-   **File**: `tests/unit/test_builder_agent.py`
-   **Scope**:
    -   Verify the prompt construction logic.
    -   Verify error handling and circuit breaker logic.
    -   Ensure >= 85% coverage.

### 5.2. Integration Testing
-   **Scope**:
    -   Run the Builder Agent with a sample idea.
    -   Verify it produces a valid `AgentPromptSpec` and `ExperimentPlan`.
