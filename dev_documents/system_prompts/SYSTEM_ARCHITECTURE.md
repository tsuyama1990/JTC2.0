# System Architecture: The JTC 2.0 (Remastered Edition)

## 1. Summary

The "JTC 2.0" is a cutting-edge simulation platform designed to modernise and streamline the new business creation process within traditional large Japanese corporations (JTCs). The system employs Large Language Models (LLMs) and a robust multi-agent architecture to emulate internal politics, rigorous approval processes, and rapid product prototyping. In this Remastered Edition, the architecture shifts away from direct, hardcoded UI generation via external APIs towards creating universally compatible, flawless prompts (AgentPromptSpec) and Minimum Viable Product (MVP) experimental plans. These outputs can be seamlessly digested by any autonomous AI coding agent. The architecture strictly enforces a "Schema-Driven Generation" pattern, utilising Pydantic to ensure a rigorous Chain of Thought, thereby eliminating the common AI pitfall of hallucination. The user interface maintains a retro, 16-colour RPG aesthetic using Pyxel to "gamify" the often harsh feedback loop, creating a psychologically safe environment for users to iterate their ideas.

## 2. System Design Objectives

The overarching goal of the JTC 2.0 architecture is to forge a "perfect requirements definition engine" that completely eradicate logical leaps and hallucinations typically associated with LLM text generation.

Firstly, the system must guarantee the absolute integrity of the Chain of Thought. AI agents must not jump to conclusions or invent features out of thin air. Instead, they must follow a strictly mandated sequence: from Alternative Analysis to Value Proposition Canvas, then Mental Model Diagram, Customer Journey, and finally Sitemap and User Stories. By enforcing Pydantic schemas at every LangGraph node, we compel the LLM to fill in these structured canvases sequentially. The output of one schema must serve as the incontrovertible input for the next, ensuring that every proposed feature is firmly rooted in verified customer pain points.

Secondly, the architecture must support robust Human-in-the-Loop (HITL) interventions without breaking the automated flow. The system is designed with specific feedback gates after major canvas generations. This requires an architecture capable of safely suspending its state, rendering the generated Pydantic models into a human-readable format (such as a high-resolution PDF and a Pyxel 'approval' stamp), and gracefully accepting user corrections before resuming the workflow. This objective ensures that the human operator retains ultimate strategic control while the AI handles the cognitive heavy lifting.

Thirdly, the system aims to achieve "Decoupled UI Generation". The previous version's reliance on specific UI-generation APIs created a lock-in effect and a single point of failure. The new objective is to produce a universally applicable `AgentPromptSpec.md`. This requires the system to act as a sophisticated context aggregator, compiling all the validated business assumptions, UX friction points, and technical constraints into a single, comprehensive markdown document that any modern AI coding assistant (like Cursor or Windsurf) can process to build the actual application.

Furthermore, the system design prioritises psychological safety through "De-identification". The harsh realities of JTC internal politics and critical customer feedback are abstracted behind a retro, 16-colour Pyxel interface. The design objective here is to maintain a strict separation of concerns between the complex, state-heavy LangGraph backend and the lightweight, game-like Pyxel frontend. The frontend should only poll state and render predefined events, ensuring the user experiences the rigorous validation process as a challenging but engaging simulation game, complete with satisfying visual and auditory feedback (e.g., the red 'approval' stamp).

Finally, the system must be maintainable, observable, and scalable. It must adhere to strict cyclomatic complexity limits to prevent AI-generated spaghetti code. All domain models must be cleanly separated, and long-running agent interactions must have robust circuit breakers and token limits enforced by tools like LangSmith to prevent infinite loops and runaway costs. The architecture must elegantly integrate these new requirements into the existing `src/core` and `src/domain_models` structures without requiring a full rewrite, maximising the reuse of current assets.

## 3. System Architecture

The architecture of The JTC 2.0 is built around a stateful, graph-based workflow managed by LangGraph, with a strict separation between the data domain, core processing logic, and user interface.

The core processing is orchestrating through a `StateGraph` where the `GlobalState` acts as the single source of truth. The system processes data through six distinct phases, invoking specialised AI agents at each node. To prevent hallucinations, the flow of data between nodes is strictly typed using Pydantic models. A node is only permitted to mutate the `GlobalState` if its output successfully validates against the required schema.

Boundary management and separation of concerns are critical rules in this architecture.
1. **Domain Models**: All business logic and data structures (`src/domain_models/`) must remain pure and free from any UI or external API dependencies. They must strictly inherit from `pydantic.BaseModel` with `extra="forbid"`.
2. **Core Workflow**: The LangGraph nodes (`src/core/nodes.py`) are responsible for interacting with LLMs and external APIs. They must not contain rendering logic. They retrieve the state, perform a focused task using an agent, and return a dictionary containing state updates.
3. **User Interface**: The Pyxel frontend (`src/ui/`) is entirely decoupled from the core logic. It runs in a separate thread or process, polling the `GlobalState` to render visual representations. It must never directly mutate the state except through designated Human-in-the-Loop interrupt resumes.

The multi-agent orchestration involves three main sub-graphs: The JTC Board (for financial and political validation), the Virtual Market (for customer validation), and the 3H Review (for technical, UX, and business feasibility). These agents are strictly constrained by the context provided to them; they are forbidden from generating ideas outside the provided Pydantic canvases.

```mermaid
graph TD
    subgraph Frontend [Pyxel UI]
        UI[Retro 16-Color UI]
        Stamp[Approval Stamp Animation]
    end

    subgraph Backend [LangGraph Core]
        State[(GlobalState)]

        N1[Ideator Node]
        N2[Persona & Empathy Node]
        N3[Alternative & VPC Node]
        N4[Mental Model & Journey Node]
        N5[Sitemap & Wireframe Node]
        N6[Virtual Customer Node]
        N7[JTC Simulation Node]
        N8[3H Review Node]
        N9[Spec Generation Node]

        N1 -->|LeanCanvas| N2
        N2 -->|Persona| N3
        N3 -->|VPC| N4
        N4 -->|Journey| N5
        N5 -->|Sitemap| N6
        N6 -->|Feedback| N7
        N7 -->|Approval| N8
        N8 -->|Refined Spec| N9

        N1 -.-> State
        N2 -.-> State
        N3 -.-> State
        N4 -.-> State
        N5 -.-> State
        N6 -.-> State
        N7 -.-> State
        N8 -.-> State
        N9 -.-> State
    end

    subgraph External
        LLM[OpenAI GPT-4]
        Tavily[Tavily Search]
        PDF[PDF Generator]
    end

    Backend <--> LLM
    Backend <--> Tavily
    N3 --> PDF
    N5 --> PDF
    N9 --> PDF

    UI <..> State
    UI --> Stamp
```

## 4. Design Architecture

The project directory is structured to separate domain logic, core orchestration, external services, and the user interface. We are adopting an additive mindset: the existing domain models will be safely extended to support the new schemas defined in the Remastered specification.

**File Structure Overview:**
```text
jtc2-0/
├── src/
│   ├── core/
│   │   ├── config.py          # Configuration and settings
│   │   ├── exceptions.py      # Custom exceptions
│   │   ├── graph.py           # LangGraph workflow definition
│   │   ├── llm.py             # LLM client wrappers
│   │   ├── nodes.py           # LangGraph node implementations
│   │   └── utils.py           # Shared utilities
│   ├── domain_models/
│   │   ├── common.py          # Base schemas
│   │   ├── enums.py           # Phase and Role definitions
│   │   ├── mvp.py             # MVP and Spec schemas
│   │   ├── persona.py         # Persona schemas
│   │   ├── state.py           # GlobalState definition
│   │   └── remastered.py      # NEW: VPC, Mental Model, Journey schemas
│   ├── services/
│   │   ├── file_service.py    # File I/O operations
│   │   └── pdf_service.py     # NEW: Canvas to PDF generation
│   └── ui/
│       ├── app.py             # Main application entry point
│       └── nemawashi_view.py  # Pyxel rendering logic
├── tests/
├── tutorials/
│   └── UAT_AND_TUTORIAL.py    # Marimo tutorial file
├── pyproject.toml
└── README.md
```

**Core Domain Pydantic Models Structure:**
The system's integrity relies on strict Pydantic models. We will introduce a new module, `src/domain_models/remastered.py`, to house the new structures (e.g., `ValuePropositionCanvas`, `MentalModelDiagram`, `CustomerJourney`, `SitemapAndStory`, `ExperimentPlan`, `AgentPromptSpec`).

These new objects will extend the existing `GlobalState` located in `src/domain_models/state.py`. We will modify `GlobalState` to optionally include these new fields:
```python
class GlobalState(BaseModel):
    # Existing fields...
    phase: Phase = Phase.IDEATION
    target_persona: Persona | None = None

    # New Remastered fields
    vpc: ValuePropositionCanvas | None = None
    mental_model: MentalModelDiagram | None = None
    customer_journey: CustomerJourney | None = None
    sitemap_story: SitemapAndStory | None = None
    experiment_plan: ExperimentPlan | None = None
    prompt_spec: AgentPromptSpec | None = None
```
By appending these fields as optional components, we ensure backward compatibility with existing tests and workflows while seamlessly integrating the new, rigorous Chain of Thought process. The LangGraph workflow in `src/core/graph.py` will be carefully adjusted to route data through the new nodes (`alternative_analysis_node`, `vpc_node`, etc.) which populate these new state fields.

## 5. Implementation Plan

The project is divided strictly into 6 sequential implementation cycles to ensure steady progress and continuous validation.

### Cycle 01: Core Schemas and State Extension
**Objective**: Establish the foundational data structures required for the Remastered workflow.
**Tasks**:
- Create `src/domain_models/remastered.py`.
- Implement all new Pydantic models defined in the specification (`CustomerProfile`, `ValueMap`, `ValuePropositionCanvas`, `MentalTower`, `MentalModelDiagram`, `AlternativeTool`, `AlternativeAnalysis`, `JourneyPhase`, `CustomerJourney`, `Route`, `UserStory`, `SitemapAndStory`, `MetricTarget`, `ExperimentPlan`, `StateMachine`, `AgentPromptSpec`).
- Ensure all models use `ConfigDict(extra="forbid")` to strictly enforce the schema.
- Update `src/domain_models/state.py` to include these new models as optional fields within the `GlobalState`.
- Update `src/domain_models/enums.py` if new phases or roles are required.
- Write unit tests to verify the instantiation and validation of these new models.

### Cycle 02: Phase 1 & 2 Node Implementation (Ideation & CPF)
**Objective**: Implement the initial generation nodes up to Customer-Problem Fit.
**Tasks**:
- Modify `src/core/nodes.py` to update the `ideator_node` to ensure it outputs the `LeanCanvas` format correctly.
- Implement the `persona_node` to generate the Persona and Empathy Map.
- Implement the `alternative_analysis_node` to evaluate current alternatives and calculate the "10x Value".
- Implement the `vpc_node` to generate the Value Proposition Canvas based on previous outputs.
- Ensure each node strictly adheres to the `@safe_node` decorator and returns the appropriate state updates.
- Integrate the Human-in-the-Loop (HITL) pause mechanism after the VPC node to allow user feedback.

### Cycle 03: Phase 3 Node Implementation (PSF)
**Objective**: Implement the Problem-Solution Fit generation nodes.
**Tasks**:
- Implement the `mental_model_journey_node` in `src/core/nodes.py`. This node must ingest the VPC and Persona to generate the `MentalModelDiagram` and subsequently the `CustomerJourney`.
- Implement the `sitemap_wireframe_node` to generate the `SitemapAndStory` based on the most painful phase identified in the Customer Journey.
- Ensure strict prompt engineering is applied here to prevent the LLM from inventing features that do not directly address the validated pain points.
- Implement the HITL pause mechanism after the Sitemap node.

### Cycle 04: Phase 4 Review Agent Orchestration
**Objective**: Implement the rigorous review and validation sub-graphs.
**Tasks**:
- Implement the `virtual_customer_node` to act as a harsh critic based on the Persona profile.
- Integrate the existing `jtc_simulation_node` (The Board) into the new workflow, ensuring it consumes the new schema data.
- Implement the `3h_review_node` (Hacker, Hipster, Hustler). These agents must be configured with specific prompts to review the technical debt, UX friction, and unit economics respectively, strictly based on the provided canvases.
- Implement circuit breakers to prevent these review agents from entering infinite debate loops.

### Cycle 05: Phase 5 & 6 Final Output Generation
**Objective**: Implement the final generation of the AgentPromptSpec and Experiment Plan.
**Tasks**:
- Update the `BuilderAgent` logic to become the `spec_generation_node`. It must aggregate all context (VPC, Journey, 3H feedback) and generate the flawless `AgentPromptSpec.md`.
- Implement the `experiment_planning_node` to generate the `ExperimentPlan` schema.
- Implement the `governance_node` to generate the final `RingiSho` report.
- Develop the `FileService` methods to write these final Markdown and JSON assets to the local disk safely.

### Cycle 06: UI Enhancements and PDF Generation Integration
**Objective**: Connect the backend logic to the Pyxel frontend and implement PDF rendering.
**Tasks**:
- Implement a `PdfService` in `src/services/` capable of taking the Pydantic canvas models and formatting them into readable PDF documents.
- Update the LangGraph workflow in `src/core/graph.py` to trigger PDF generation at the designated HITL gates.
- Update the Pyxel frontend (`src/ui/nemawashi_view.py` or similar) to listen for these specific state changes and trigger the "Approval Stamp" animation and sound effect.
- Finalise the Marimo tutorial (`tutorials/UAT_AND_TUTORIAL.py`) to demonstrate the entire end-to-end flow.

## 6. Test Strategy

Testing must ensure the strict schema enforcement and multi-agent stability without incurring unnecessary API costs or side effects.

### Cycle 01: Core Schemas and State Extension
- **Unit Tests**: Instantiate every new Pydantic model with valid and invalid data to ensure validation rules (e.g., `extra="forbid"`, field constraints) work perfectly.
- **Integration Tests**: Instantiate the updated `GlobalState` and test the JSON serialization/deserialization to ensure compatibility with LangGraph's state management.
- **Strategy**: No external APIs are required. Use standard pytest features.

### Cycle 02: Phase 1 & 2 Node Implementation (Ideation & CPF)
- **Unit Tests**: Test the prompt templates and input validation for each new node.
- **Integration Tests**: Create mock LLM responses that return valid JSON strings matching the schemas. Run the graph from Ideation to the VPC node, asserting that the state updates correctly without actually calling the OpenAI API.
- **Strategy**: Heavily utilise `unittest.mock.patch` to mock the LLM calls within `src/core/llm.py` or directly on the node functions.

### Cycle 03: Phase 3 Node Implementation (PSF)
- **Unit Tests**: Test the data transformation logic within the nodes (e.g., ensuring the Mental Model correctly links to Journey phases).
- **Integration Tests**: Similar to Cycle 02, mock the LLM and run the sub-graph from VPC to Sitemap generation. Assert that the strict Chain of Thought is maintained.
- **Strategy**: Ensure that missing prerequisites in the state (e.g., trying to generate a Journey without a VPC) raise appropriate, caught exceptions.

### Cycle 04: Phase 4 Review Agent Orchestration
- **Unit Tests**: Test the specific system prompts assigned to the Virtual Customer and the 3H agents.
- **Integration Tests**: Simulate a debate loop. Mock the LLM to return a predefined sequence of critiques and concessions. Assert that the circuit breaker mechanism correctly terminates the loop if it exceeds the `max_turns` limit.
- **Strategy**: This is critical for preventing runaway costs. Tests must explicitly trigger the timeout and loop-detection safeguards.

### Cycle 05: Phase 5 & 6 Final Output Generation
- **Unit Tests**: Test the generation of the final Markdown format.
- **Integration Tests**: Run the final nodes with a fully populated mock `GlobalState`. Assert that the `FileService` correctly writes the `AgentPromptSpec.md` and `EXPERIMENT_PLAN.md` to a temporary directory.
- **Strategy**: Use `tempfile.TemporaryDirectory()` to ensure file I/O tests do not pollute the actual workspace. Mock the file system if necessary to test error handling (e.g., disk full scenarios).

### Cycle 06: UI Enhancements and PDF Generation Integration
- **Unit Tests**: Test the logic that maps Pydantic models to PDF layout coordinates.
- **Integration Tests**: Run the Pyxel application in headless mode (if possible) or test the state polling logic independently of the rendering engine. Verify that the tutorial Marimo file executes successfully in "Mock Mode".
- **Strategy**: Ensure the "Mock Mode" perfectly simulates the entire user journey, allowing CI systems to verify the tutorial without requiring OpenAI keys or graphical displays.
