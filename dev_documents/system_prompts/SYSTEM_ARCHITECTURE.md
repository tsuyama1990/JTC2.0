# System Architecture: The JTC 2.0 (Remastered Edition)

## 1. Summary

The "JTC 2.0" is a cutting-edge simulation platform designed to modernise and streamline the new business creation process within traditional large Japanese corporations (JTCs). The system employs Large Language Models (LLMs) and a robust multi-agent architecture to emulate internal politics, rigorous approval processes, and rapid product prototyping. In this Remastered Edition, the architecture shifts away from direct, hardcoded UI generation via external APIs towards creating universally compatible, flawless prompts (AgentPromptSpec) and Minimum Viable Product (MVP) experimental plans. These outputs can be seamlessly digested by any autonomous AI coding agent. The architecture strictly enforces a "Schema-Driven Generation" pattern, utilising Pydantic to ensure a rigorous Chain of Thought, thereby eliminating the common AI pitfall of hallucination. The user interface maintains a retro, 16-colour RPG aesthetic using Pyxel to "gamify" the often harsh feedback loop, creating a psychologically safe environment for users to iterate their ideas.

## 2. System Design Objectives

The overarching goal of the JTC 2.0 architecture is to forge a "perfect requirements definition engine" that completely eradicates logical leaps and hallucinations typically associated with LLM text generation. The system is designed not just to automate, but to elevate the rigorous, often painful process of discovering product-market fit into a deterministic, scientifically sound software pipeline. This pipeline must serve as the absolute source of truth for all subsequent engineering efforts.

Firstly, the system must guarantee the absolute integrity of the Chain of Thought, a foundational objective. AI agents in this platform are strictly prohibited from jumping to conclusions or inventing features out of thin air based on superficial prompts. Instead, they must follow a mandated, highly structured sequence derived from proven startup methodologies: transitioning meticulously from an initial Alternative Analysis to a comprehensive Value Proposition Canvas (VPC), subsequently constructing a Mental Model Diagram of the target user, mapping that model to a detailed Customer Journey, and finally deriving a concrete Sitemap and actionable User Stories. By enforcing strict Pydantic schemas at the output boundary of every LangGraph node, we compel the LLM to populate these structured canvases sequentially. The output of one schema must serve as the incontrovertible, immutable input for the next phase. This architecture ensures that every single proposed feature or UI element is firmly rooted in verified customer pain points, creating an unbroken chain of evidence from problem to solution.

Secondly, the architecture must support robust Human-in-the-Loop (HITL) interventions without breaking or destabilising the automated, stateful flow. The system is designed with specific, predefined feedback gates strategically placed after major canvas generations. This requirement necessitates an architecture capable of safely suspending its complex internal state, rendering the generated Pydantic models into a human-readable, highly visual format (such as a high-resolution PDF report and a celebratory Pyxel 'approval' stamp animation), and gracefully accepting detailed user corrections before resuming the workflow. This crucial objective ensures that the human operator retains ultimate strategic control and domain authority, while the AI continuously handles the cognitive heavy lifting of formatting, cross-referencing, and generating the dense underlying documentation.

Thirdly, the system aims to achieve absolute "Decoupled UI Generation," moving away from fragile dependencies. The previous iteration's reliance on specific, volatile UI-generation APIs created an unacceptable lock-in effect and a constant single point of failure. The new, paramount objective is to produce a universally applicable, immaculate `AgentPromptSpec.md`. This requires the system to act as a highly sophisticated context aggregator. It must compile all validated business assumptions, documented UX friction points, and agreed-upon technical constraints into a single, comprehensive, and perfectly formatted markdown document. This document must be designed so that any modern autonomous AI coding assistant (like Cursor, Windsurf, or Google Antigravity) can process it immediately to build the actual application without requiring further clarification.

Furthermore, the system design prioritises the psychological safety of the user through a deliberate "De-identification" strategy. The harsh realities of JTC internal politics, the often brutal feedback from simulated corporate boards, and the critical responses from virtual customers are abstracted behind a charming, retro, 16-colour Pyxel interface. The design objective here is to maintain an impenetrable separation of concerns between the complex, state-heavy, and potentially anxiety-inducing LangGraph backend and the lightweight, game-like Pyxel frontend. The frontend should act purely as a passive observer, only polling the state and rendering predefined events. This ensures the user experiences the rigorous validation process as a challenging but engaging simulation game, complete with satisfying visual and auditory feedback (e.g., the resounding thud of the red 'approval' stamp), rather than a stressful corporate review.

Finally, the system must be relentlessly maintainable, highly observable, and horizontally scalable. It must adhere to strict cyclomatic complexity limits (enforced by tools like Ruff) to prevent the accumulation of unmaintainable, AI-generated spaghetti code. All domain models must be cleanly separated, adhering strictly to SOLID principles. Crucially, long-running multi-agent interactions must possess robust, foolproof circuit breakers and hard token limits, strictly enforced by observability tools like LangSmith, to definitively prevent infinite debate loops and runaway cloud costs. The architecture must elegantly integrate these new, demanding requirements into the existing `src/core` and `src/domain_models` structures without requiring a full, disruptive rewrite, maximising the intelligent reuse of current, proven assets.

## 3. System Architecture

The architecture of The JTC 2.0 is built around a stateful, graph-based workflow managed by LangGraph, enforcing a strict and uncompromising separation between the data domain, core processing logic, external services, and the user interface. This separation ensures that each layer can be tested, modified, and scaled entirely independently of the others.

The core processing engine orchestrates the entire lifecycle through a compiled `StateGraph` where the `GlobalState` object acts as the single, immutable source of truth for the entire application. The system processes data sequentially through six distinct, highly regulated phases, invoking specialised, prompt-engineered AI agents at each specific node. To definitively prevent hallucinations and enforce the required Chain of Thought, the flow of data between nodes is strictly typed using comprehensive Pydantic models with `extra="forbid"` configurations. A processing node is only permitted to mutate the `GlobalState` if, and only if, its output successfully validates against the rigidly required schema for that specific phase.

Boundary management and the separation of concerns are absolute, inviolable rules in this architecture:

1. **Domain Models (`src/domain_models/`)**: All business logic, data structures, validation rules, and schema definitions must remain entirely pure and completely free from any UI rendering logic, external API dependencies, or framework-specific side effects. They must strictly inherit from `pydantic.BaseModel` and act solely as the data contract for the system.
2. **Core Workflow (`src/core/nodes.py`, `src/core/graph.py`)**: The LangGraph nodes are uniquely responsible for interacting with external LLMs, invoking tools, and executing the core business logic. They must absolutely not contain any direct rendering logic or UI manipulation code. They receive the current state, perform a focused, atomic task using a specifically instructed agent, and return a dictionary containing only the validated state updates. The graph itself defines the routing and the Human-in-the-Loop (HITL) interrupt points.
3. **User Interface (`src/ui/`)**: The Pyxel frontend is entirely decoupled from the core workflow execution. It runs in a separate thread or process, asynchronously polling the `GlobalState` (or a specific UI state subset) to render visual representations and animations. It must never directly mutate the core state except through explicitly designated API endpoints or controlled Human-in-the-Loop interrupt resumes.

The multi-agent orchestration involves three primary, sophisticated sub-graphs, each designed to simulate a different aspect of the corporate and market validation process:
*   **The JTC Board:** Simulates the internal approval process, featuring agents acting as the CFO (focusing on financial viability) and the Head of Sales (focusing on market cannibalization), providing rigorous political and financial validation.
*   **Virtual Market:** Deploys simulated customer agents based directly on the generated Persona and Mental Model to provide harsh, realistic feedback on the proposed solution, evaluating the true "willingness to pay" and identifying UX friction.
*   **The 3H Review:** Engages three distinct agents (Hacker for technical feasibility, Hipster for user experience, and Hustler for unit economics) to rigorously pressure-test the generated wireframes and sitemaps before finalizing the specification.

Critically, all these agents are strictly constrained by the context provided to them in their prompts; they are explicitly forbidden from generating novel ideas or features that fall outside the boundaries defined by the preceding Pydantic canvases.

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

The project directory is meticulously structured to ensure a clean separation between domain logic, core orchestration, external services, and the user interface. We are adopting a strict "additive mindset": the existing, tested domain models and workflows will be safely extended to support the new schemas defined in the Remastered specification, rather than executing a risky, full-scale rewrite.

**File Structure Overview:**
```text
jtc2-0/
├── src/
│   ├── core/
│   │   ├── config.py          # Configuration, feature flags, and settings
│   │   ├── exceptions.py      # Custom business logic exceptions
│   │   ├── graph.py           # LangGraph workflow definition and routing
│   │   ├── llm.py             # LLM client wrappers and structured output parsers
│   │   ├── nodes.py           # LangGraph atomic node implementations
│   │   └── utils.py           # Shared, pure utilities (e.g., text chunking)
│   ├── domain_models/
│   │   ├── common.py          # Base schemas and generic iterators
│   │   ├── enums.py           # Phase, Role, and status definitions
│   │   ├── mvp.py             # Legacy MVP and Spec schemas
│   │   ├── persona.py         # Persona and Empathy Map schemas
│   │   ├── state.py           # The immutable GlobalState definition
│   │   └── remastered.py      # NEW: VPC, Mental Model, Journey, Spec schemas
│   ├── services/
│   │   ├── file_service.py    # Safe file I/O operations and path validation
│   │   └── pdf_service.py     # NEW: Pydantic to visual PDF generation
│   └── ui/
│       ├── app.py             # Main application entry point and bootstrapping
│       └── nemawashi_view.py  # Pyxel rendering logic and state polling
├── tests/
│   ├── unit/                  # Isolated testing of models and pure functions
│   └── integration/           # Graph routing and mock-LLM state transitions
├── tutorials/
│   └── UAT_AND_TUTORIAL.py    # The single, comprehensive Marimo tutorial file
├── pyproject.toml             # Dependency and strict linter configuration
└── README.md                  # Project overview and quick start guide
```

**Core Domain Pydantic Models Structure:**
The system's integrity absolutely relies on strict, unforgiving Pydantic models. We will introduce a new, dedicated module, `src/domain_models/remastered.py`, to house the highly structured new models defined in the requirements (e.g., `ValuePropositionCanvas`, `MentalModelDiagram`, `CustomerJourney`, `SitemapAndStory`, `ExperimentPlan`, `AgentPromptSpec`).

These new, rigorous objects will extend the existing `GlobalState` located in `src/domain_models/state.py`. We will meticulously modify `GlobalState` to include these new fields as `Optional` components. This is a critical design decision to ensure backward compatibility with existing tests and workflows, while seamlessly integrating the new, rigorous Chain of Thought process.

```python
from pydantic import BaseModel, ConfigDict
from src.domain_models.remastered import (
    ValuePropositionCanvas,
    MentalModelDiagram,
    CustomerJourney,
    SitemapAndStory,
    ExperimentPlan,
    AgentPromptSpec
)
from src.domain_models.persona import Persona
from src.domain_models.enums import Phase

class GlobalState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Existing fields remain untouched...
    phase: Phase = Phase.IDEATION
    target_persona: Persona | None = None

    # New Remastered fields appended safely
    vpc: ValuePropositionCanvas | None = None
    mental_model: MentalModelDiagram | None = None
    customer_journey: CustomerJourney | None = None
    sitemap_story: SitemapAndStory | None = None
    experiment_plan: ExperimentPlan | None = None
    prompt_spec: AgentPromptSpec | None = None
```

By appending these fields as optional components, the LangGraph workflow in `src/core/graph.py` can be carefully and incrementally adjusted to route data through the new nodes (`alternative_analysis_node`, `vpc_node`, etc.) which will populate these new state fields sequentially. The system will rely on the `validate_state` model validator to ensure that, for instance, the `vpc` field is populated before the system is allowed to transition to the `Phase.PSF` (Problem-Solution Fit) state.

## 5. Implementation Plan

The project is strictly divided into exactly 6 sequential implementation cycles. Each cycle is designed to be fully testable and independent, ensuring steady, verifiable progress without introducing unmanageable technical debt or circular dependencies. Every cycle builds upon the validated state of the previous one.

### Cycle 01: Core Schemas and State Extension
**Objective**: Establish the absolute foundational data structures and validation logic required for the Remastered workflow, ensuring perfect schema integrity before any processing logic is written. This is the bedrock of the hallucination-prevention strategy.

**Detailed Implementation Strategy**:
This cycle focuses entirely on the `src/domain_models` directory. The primary task is to create `src/domain_models/remastered.py`. Within this file, the developer must meticulously translate the requirements into exact Pydantic `BaseModel` classes. This includes defining `CustomerProfile`, `ValueMap`, and `ValuePropositionCanvas` for the CPF phase. It includes defining `MentalTower` and `MentalModelDiagram` for the cognitive mapping. It includes defining `AlternativeTool` and `AlternativeAnalysis`. Furthermore, it involves defining the chronological `JourneyPhase` and `CustomerJourney`, the architectural `Route`, `UserStory`, and `SitemapAndStory`, the analytical `MetricTarget` and `ExperimentPlan`, and finally, the comprehensive `StateMachine` and `AgentPromptSpec`.

A critical requirement is that every single one of these models must explicitly declare `model_config = ConfigDict(extra="forbid")`. This prevents the LLM from injecting undefined fields and breaking the data contract. Field descriptions must be highly detailed, as these descriptions directly guide the LLM's structured output generation via OpenAI's function calling API.

Once the models are defined, `src/domain_models/state.py` must be updated. The new models will be added as `Optional` fields to the `GlobalState`. The developer must also update the `StateValidator` in `src/domain_models/validators.py` to ensure that if the `GlobalState.phase` transitions to `Phase.PSF`, the `vpc` and `alternative_analysis` fields are definitively not `None`. If new phases (e.g., `Phase.OUTPUT_GENERATION`) are required by the new workflow, they must be safely appended to the `Phase` enum in `src/domain_models/enums.py`. This cycle involves absolutely no LangGraph node implementation or LLM API calls; it is purely data architecture.

### Cycle 02: Phase 1 & 2 Node Implementation (Ideation & CPF)
**Objective**: Implement the initial data generation and processing nodes, taking the workflow from raw ideation up to a validated Customer-Problem Fit (CPF), culminating in the first major Human-in-the-Loop intervention point.

**Detailed Implementation Strategy**:
This cycle focuses on `src/core/nodes.py` and `src/core/graph.py`. First, the developer must review and slightly modify the existing `ideator_node` to ensure its output perfectly matches the expected `LeanCanvas` format required as the seed for the subsequent steps.

The core work involves creating three completely new nodes. The `persona_node` must be implemented to generate a high-resolution `Persona` and `EmpathyMap` based strictly on the selected `LeanCanvas`. Following this, the `alternative_analysis_node` must be created. This node will prompt the LLM to evaluate current market alternatives and calculate a compelling "10x Value" proposition. Crucially, the prompt for this node must explicitly inject the previously generated `Persona` to ensure relevance. Next, the `vpc_node` will be implemented. This is the most complex node of this cycle; it must ingest the `Persona` and `AlternativeAnalysis` and synthesize a structurally perfect `ValuePropositionCanvas`.

Every new node must be decorated with the existing `@safe_node` decorator to guarantee standardized exception handling, correlation ID injection, and state preservation upon failure. The nodes must use the structured output capabilities of the LLM client (e.g., `llm.with_structured_output(ValuePropositionCanvas)`).

Finally, the `src/core/graph.py` must be updated to route the flow sequentially through these nodes. The critical addition here is defining an `interrupt_after` condition on the `vpc_node` to establish the "HITL Gate 1.5". This ensures the LangGraph engine pauses execution, allowing the system state to be inspected and modified by the user before proceeding to Phase 3.

### Cycle 03: Phase 3 Node Implementation (PSF)
**Objective**: Implement the Problem-Solution Fit generation nodes, taking the validated customer pain points and translating them directly into a mental model, a customer journey, and a concrete software architecture (sitemap and wireframes).

**Detailed Implementation Strategy**:
Building upon the paused state from Cycle 02, this cycle continues the work in `src/core/nodes.py`. The developer will implement the `mental_model_journey_node`. This node requires highly specialized prompt engineering. It must be instructed to read the `ValuePropositionCanvas` and `Persona` from the `GlobalState` and deduce the underlying beliefs ("Towers of Thought") of the user, formatting them into the `MentalModelDiagram`. Within the same node, or a sequentially linked node, the system must then generate the `CustomerJourney`, mapping the mental model to chronological touchpoints and explicitly identifying the "worst pain phase".

The next major implementation is the `sitemap_wireframe_node`. This node is strictly forbidden from inventing arbitrary application features. Its prompt must mandate that it only designs routes and user stories that directly address the "worst pain phase" identified in the previous step. It will output the `SitemapAndStory` Pydantic model.

The prompt engineering in this cycle is critical: the instructions must clearly define the boundaries, ensuring the LLM acts purely as a translator of the validated pain points into a structural design, rather than a creative ideator. Once these nodes are implemented, `src/core/graph.py` must be updated to wire them into the sequence, immediately following the resumption from the VPC HITL gate. Another interrupt must be defined after the `sitemap_wireframe_node` to establish "HITL Gate 1.8", allowing the user to review the proposed application structure and story before the rigorous multi-agent reviews begin.

### Cycle 04: Phase 4 Review Agent Orchestration
**Objective**: Implement the rigorous, multi-agent review and validation sub-graphs. This cycle simulates the hostile environment of the market and the corporate boardroom to pressure-test the generated wireframes and business logic.

**Detailed Implementation Strategy**:
This cycle focuses heavily on the orchestration capabilities of LangGraph and the prompt engineering of specific personas. The developer will implement the `virtual_customer_node`. This agent's prompt must dynamically inject the entire `Persona` profile and `MentalModelDiagram`. The agent must be instructed to act as a harsh, unforgiving critic, evaluating the `SitemapAndStory` strictly against its defined switching costs and pain points.

Next, the developer will integrate the existing `jtc_simulation_node` (The Board) into the new sequential workflow. The existing logic must be carefully audited to ensure it correctly consumes the new schema data (like the VPC and Alternative Analysis) rather than relying on obsolete, legacy fields.

The most complex component is the implementation of the `3h_review_node`. This requires establishing a sub-graph or a controlled loop within a node where three distinct agents (Hacker, Hipster, Hustler) review the proposal. The Hacker's prompt must focus on technical debt and simplicity, the Hipster on UX friction against the mental model, and the Hustler on unit economics.

A mandatory technical requirement for this cycle is the implementation of robust circuit breakers. Multi-agent debates can easily enter infinite loops, rapidly consuming API tokens. The developer must implement a moderator logic within the review nodes. This logic will track the number of conversational turns (`max_turns`) and analyze the text for stalemate conditions. If a limit is reached, the moderator must force the node to return a finalized state, preventing infinite loops and ensuring the workflow can progress to the final output generation.

### Cycle 05: Phase 5 & 6 Final Output Generation
**Objective**: Implement the final synthesis of all accumulated context into the ultimate deliverables: the pristine `AgentPromptSpec.md` and the actionable `ExperimentPlan` schema, followed by secure file I/O operations.

**Detailed Implementation Strategy**:
This cycle fundamentally alters the role of the existing `BuilderAgent`. Instead of attempting to hit external APIs to generate code directly, the `BuilderAgent` logic will be transformed into the `spec_generation_node`. This node acts as the ultimate aggregator. Its prompt must instruct it to read every single canvas and review output generated in the previous phases (VPC, Journey, Sitemap, 3H feedback). It must apply a "subtractive thinking" methodology, explicitly instructed to remove any feature that does not directly contribute to solving the core user pain. It will then structure this massive context into the `AgentPromptSpec` Pydantic model.

Simultaneously, the developer will implement the `experiment_planning_node`. This node focuses on the real-world execution strategy, defining the AARRR metrics and pivot conditions required for the `ExperimentPlan` schema based on the finalized solution. The `governance_node` will also be updated to generate the final `RingiSho` (JTC Approval Document) encompassing all this verified data.

Finally, this cycle involves crucial updates to the `FileService` in `src/core/services/file_service.py`. The service must be expanded to include robust, thread-safe methods for converting the final Pydantic models (specifically the `AgentPromptSpec`) into perfectly formatted Markdown files written securely to the local disk, respecting all path traversal security protocols established in the project.

### Cycle 06: UI Enhancements and PDF Generation Integration
**Objective**: Connect the complex, stateful backend logic to the Pyxel frontend, implement the visual PDF rendering for the HITL gates, and finalize the comprehensive Marimo tutorial to demonstrate the entire system.

**Detailed Implementation Strategy**:
This final cycle brings the user experience together. The developer will create a new `PdfService` within `src/services/`. This service must accept the various Pydantic canvas models (VPC, Mental Model, etc.) and format them into readable, visually structured PDF documents. This is essential for the HITL gates, providing the user with a tangible artifact to review during the pause in execution.

The LangGraph workflow in `src/core/graph.py` must be updated to trigger this PDF generation specifically at the defined interrupt points (Gate 1.5 and Gate 1.8).

Simultaneously, the Pyxel frontend (`src/ui/nemawashi_view.py` or the primary UI loop) must be updated. It must be programmed to listen for the specific state changes indicating that a major canvas has been successfully generated and validated. Upon detecting this state transition, the UI must trigger the "Approval Stamp" animation and play the associated sound effect, fulfilling the gamification requirement.

Lastly, the developer must finalize the interactive Marimo tutorial (`tutorials/UAT_AND_TUTORIAL.py`). This tutorial must demonstrate the entire end-to-end flow, from Ideation to the generation of the `AgentPromptSpec.md`. Crucially, it must feature a robust "Mock Mode" that perfectly simulates the entire journey without requiring API keys, allowing CI systems and new users to verify the workflow instantly.

## 6. Test Strategy

Testing must rigorously ensure absolute schema enforcement, the deterministic flow of the graph, and multi-agent stability, all without incurring unnecessary API costs or introducing flaky side effects. The testing approach relies heavily on isolated unit tests and fully mocked integration tests.

### Cycle 01: Core Schemas and State Extension
- **Unit Tests**: The developer must write exhaustive tests instantiating every new Pydantic model (`ValuePropositionCanvas`, `CustomerJourney`, etc.) with both perfectly valid and intentionally invalid data. These tests must assert that the `extra="forbid"` rule strictly rejects unexpected fields, and that all type constraints and minimum/maximum length validators function flawlessly.
- **Integration Tests**: Instantiate the newly updated `GlobalState` containing all optional fields. Test the full JSON serialization and deserialization lifecycle to guarantee absolute compatibility with LangGraph's internal state management checkpointing system.
- **Strategy**: This cycle requires absolutely zero external APIs or complex mocks. Use standard, fast-running `pytest` features to ensure the foundational data contract is bulletproof. The coverage for `src/domain_models/remastered.py` must be 100%.

### Cycle 02: Phase 1 & 2 Node Implementation (Ideation & CPF)
- **Unit Tests**: Test the specific prompt templates defined for the new nodes (`persona_node`, `alternative_analysis_node`, `vpc_node`). Ensure that the context variables are injected correctly without raising key errors.
- **Integration Tests**: This is critical. The developer must create highly realistic mock LLM responses that return perfectly formatted JSON strings matching the new schemas. Using these mocks, execute the LangGraph sub-graph from the Ideation phase up to the `vpc_node`. Assert that the `GlobalState` updates sequentially and correctly, and importantly, verify that the graph execution properly halts at the designated HITL interrupt point.
- **Strategy**: Heavily utilize `unittest.mock.patch` to intercept the LLM calls within `src/core/llm.py` or directly on the node functions. No actual network requests should be made to OpenAI. Assert that the `validate_state` function is called and passes after each node execution.

### Cycle 03: Phase 3 Node Implementation (PSF)
- **Unit Tests**: Test the internal data transformation logic within the nodes. For example, write a test ensuring that if the `MentalModelDiagram` contains three specific towers, the prompt for the `CustomerJourney` generation correctly receives and processes all three.
- **Integration Tests**: Similar to the strategy in Cycle 02, extensively mock the LLM responses. Initialize a `GlobalState` that is already populated with a valid VPC and Persona (simulating a resumption from the previous HITL gate). Run the sub-graph through to the `sitemap_wireframe_node`. Assert that the strict Chain of Thought is maintained and the final state contains the `SitemapAndStory` model.
- **Strategy**: Ensure that edge cases are tested. Specifically, test that if the `GlobalState` is missing prerequisite data (e.g., trying to execute the journey node without a VPC in the state), the system raises appropriate, predefined, and gracefully caught exceptions rather than crashing unceremoniously.

### Cycle 04: Phase 4 Review Agent Orchestration
- **Unit Tests**: Rigorously test the specific system prompts assigned to the Virtual Customer and the 3H agents to ensure their personas are strictly defined. Test the moderator logic independently to ensure it correctly identifies stalemate conditions in text strings.
- **Integration Tests**: Simulate the complex multi-agent debate loop. Mock the LLM to return a predefined, escalating sequence of critiques and rebuttals between the Hacker and Hustler agents. Assert that the circuit breaker mechanism correctly activates, terminates the loop exactly when it exceeds the configured `max_turns` limit, and forces a valid fallback state.
- **Strategy**: This phase is absolutely critical for preventing runaway API costs in production. The test suite must explicitly and repeatedly trigger the timeout, loop-detection, and token-limit safeguards to prove their efficacy under simulated duress.

### Cycle 05: Phase 5 & 6 Final Output Generation
- **Unit Tests**: Test the deterministic generation of the final Markdown strings from the Pydantic models. Ensure the Mermaid diagrams are formatted correctly and the markdown headers align properly.
- **Integration Tests**: Execute the final nodes (`spec_generation_node`, `experiment_planning_node`) with a fully, synthetically populated `GlobalState` representing a successful run through all previous phases. Assert that the `FileService` correctly and securely writes the `AgentPromptSpec.md` and `EXPERIMENT_PLAN.md` to the designated output directories.
- **Strategy**: Use `tempfile.TemporaryDirectory()` comprehensively in all tests to ensure file I/O operations do not pollute the actual developer workspace or CI environment. Mock the file system if necessary to test robust error handling for edge cases, such as simulating disk full scenarios or permission denied errors.

### Cycle 06: UI Enhancements and PDF Generation Integration
- **Unit Tests**: Test the pure logic within `PdfService` that maps the structured data from Pydantic models to coordinate-based PDF layouts, ensuring no data loss occurs during translation.
- **Integration Tests**: Run the Pyxel application rendering loop in a headless mode (if supported) or test the state polling logic completely independently of the graphical rendering engine. The most critical test here is verifying that the comprehensive Marimo tutorial file executes flawlessly from start to finish in "Mock Mode".
- **Strategy**: Ensure the "Mock Mode" implemented for the tutorial perfectly and completely simulates the entire user journey. This allows automated CI systems to verify the tutorial's logic, the state transitions, and the final output generation without ever requiring actual OpenAI API keys or graphical display capabilities. This guarantees the tutorial remains functional as the underlying engine evolves.
