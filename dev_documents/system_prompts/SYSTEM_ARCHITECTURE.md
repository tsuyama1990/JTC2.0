# The JTC 2.0 (Remastered Edition): System Architecture

## 1. Summary

The JTC 2.0 (Remastered Edition) is a paradigm-shifting multi-agent simulation platform designed to radically streamline and enhance the new business creation process within Traditional Japanese Companies (JTCs). By leveraging the rigorous "Startup Science" methodology—specifically the transition from Customer Problem Fit (CPF) to Problem Solution Fit (PSF)—the system orchestrates a complex role-playing environment. Here, business ideas are not just brainstormed; they are subjected to realistic "Gekizume" (harsh feedback) by AI agents representing internal stakeholders (Finance, Sales, CPO), validated against real customer interview transcripts using Retrieval-Augmented Generation (RAG), and ultimately transformed into actionable outputs. The final output has been redefined to generate a "Perfect Agent Prompt Specification" (AgentPromptSpec.md) and an "MVP Experiment Plan" (EXPERIMENT_PLAN.md), completely bypassing direct reliance on specific UI generation APIs like v0.dev. This shift ensures the system acts as a universal, future-proof requirements engineering engine capable of feeding any autonomous AI coding agent. The architecture prioritizes strict schema validation via Pydantic to enforce "Chain of Thought" reasoning and eliminate AI hallucinations, all while maintaining a gamified, retro 16-color Pyxel interface to ensure user psychological safety through "de-identification".

## 2. System Design Objectives

The overarching goal of the JTC 2.0 (Remastered Edition) is to provide an ultra-reliable, hallucination-free simulation platform for enterprise intrapreneurs. The system aims to simulate the harsh, often bureaucratic reality of traditional corporate decision-making whilst applying cutting-edge startup methodologies. To achieve this, the system design is governed by several critical objectives, constraints, and success criteria, meticulously formulated to guarantee a robust, scalable, and user-centric experience.

### Primary Goals
1. **Hallucination Elimination via Schema-Driven Generation:** The foremost objective is to eradicate the logical leaps and "hallucinations" commonly associated with Large Language Models. By enforcing a strict "Chain of Thought" methodology, every AI interaction is constrained by Pydantic models with `extra="forbid"`. The system mandates a sequential progression: from Empathy Mapping to Alternative Analysis, Value Proposition Design, Mental Model Diagramming, Customer Journey Mapping, and finally Sitemap and User Story creation. Each step acts as an absolute prerequisite for the next, ensuring that the AI cannot generate solutions without mathematically sound problem definitions.
2. **Universal Compatibility (The "Perfect Prompt"):** Moving away from direct API integrations for UI generation, the system must produce a universally applicable `AgentPromptSpec.md` and `EXPERIMENT_PLAN.md`. This ensures that the output can be seamlessly digested by any modern autonomous coding agent (such as Cursor, Windsurf, or Google Antigravity). This architectural pivot guarantees longevity, preventing the platform from becoming obsolete when specific proprietary APIs evolve or deprecate.
3. **Psychological Safety through De-identification:** Enterprise innovation is fraught with emotional resistance and fear of failure. The system must utilise a gamified, retro 16-color RPG-style interface (powered by Pyxel). This deliberate abstraction transforms harsh critique ("Gekizume") from AI stakeholders into harmless "game events", significantly lowering the emotional barrier for the user and fostering a culture of fearless experimentation.
4. **Human-in-the-Loop (HITL) Co-creation:** The system must not act as a black box. At critical junctures (e.g., after the generation of the Value Proposition Canvas or the Mental Model), the system must present the intermediate artifacts to the user, allowing for course correction. This collaborative approach ensures the final output remains perfectly aligned with the user's initial vision whilst benefiting from the AI's rigorous analytical capabilities.

### System Constraints
1. **Strict Context Inheritance:** AI agents are strictly forbidden from generating ideas or features "zero-based" or relying solely on their pre-trained weights. Every agent must ingest the previously generated structural data (the "canvases") as absolute foundational context before producing any output.
2. **Deterministic Outputs over Creativity:** While ideation requires some flexibility, the structural progression of the business models must be highly deterministic. The integration of LangGraph for orchestration ensures predictable state transitions and prevents agents from skipping essential verification steps.
3. **Additive Architecture:** The current codebase is functional and valuable. A fundamental constraint is to adopt an "additive mindset." New requirements must be integrated by extending existing domain models and LangGraph nodes, strictly avoiding full rewrites of operational modules unless absolutely necessitated by insurmountable technical debt.
4. **Resilience and Observability:** The system must be highly resilient to API failures or unexpected inputs. LangSmith integration is mandatory to monitor token consumption, trace execution paths, and prevent infinite loops (deadlocks) during the multi-agent debates (e.g., the JTC Board Simulation).

### Success Criteria
1. **End-to-End Execution:** The system must successfully traverse all 14 steps across the 6 phases without unhandled exceptions or state corruption, ultimately generating the expected PDF canvases, the `AgentPromptSpec.md`, and the `EXPERIMENT_PLAN.md`.
2. **Schema Adherence:** Every single output generated by the LLM must successfully validate against its respective Pydantic schema without triggering a `ValidationError`. This is the ultimate proof that hallucination has been suppressed.
3. **User Acceptance:** The user must be able to seamlessly intervene at the designated HITL gates, modify the trajectory of the generation, and observe these modifications accurately reflected in all subsequent artifacts. The gamified Pyxel UI must remain responsive and stable throughout the heavy backend processing.
4. **Test Coverage and Quality:** The implementation must maintain high test coverage, particularly for the strict validation logic and the state transitions within the LangGraph orchestrator. The code must strictly adhere to the enforced `ruff` and `mypy` configurations, guaranteeing long-term maintainability.

## 3. System Architecture

The system architecture of the JTC 2.0 (Remastered Edition) is built upon a foundation of multi-agent orchestration, strict schema enforcement, and robust separation of concerns. The architecture is designed to handle complex, non-linear workflows while maintaining a deterministic state, ensuring that the rigorous process of business validation is executed flawlessly.

### High-Level Components

1.  **LangGraph Orchestrator (The State Machine):** At the core of the system lies LangGraph, acting as the ultimate state machine and orchestrator. It manages the flow of execution across the 6 distinct phases, ensuring that each node (step) receives the correct input context and produces the required output before transitioning to the next state. The orchestrator maintains a `GlobalState` object, which acts as the single source of truth for the entire simulation, holding all generated canvases, user inputs, and agent feedback.
2.  **Pydantic Domain Models (The Schema Engine):** All data flowing between the LangGraph nodes and the LLM is strictly typed using Pydantic V2 models. These models are not merely data containers; they are active enforcement mechanisms. By utilizing `extra="forbid"` and custom validators, the domain models ensure that the LLM cannot inject hallucinated fields or skip mandatory reasoning steps. This engine is the primary defense against AI unreliability.
3.  **LLM Service & Tools (The Cognitive Layer):** This layer encapsulates all interactions with external APIs, primarily OpenAI (for LLM inference) and Tavily (for market research). The LLM service is abstracted behind a factory pattern, allowing for potential future swapping of models. Crucially, this layer is completely decoupled from the business logic; it merely executes prompts and returns structured data.
4.  **RAG Engine (The Reality Check):** The Retrieval-Augmented Generation (RAG) engine utilizes LlamaIndex to ingest, vectorize, and query customer interview transcripts. This component grounds the simulation in reality, providing the CPO Agent with factual data to challenge the user's assumptions. It ensures that decisions are based on evidence rather than mere speculation.
5.  **Pyxel UI & Event Bus (The Presentation Layer):** The gamified retro interface is powered by Pyxel. To ensure the UI remains responsive during long-running LLM inferences, the frontend is entirely decoupled from the backend. They communicate via a state-polling mechanism or a dedicated event bus. The UI is responsible for rendering the "Gekizume" dialogues, displaying the "Approval" stamps, and presenting the HITL intervention prompts.
6.  **File Generation Service (The Output Engine):** Responsible for compiling the final artifacts, this service takes the validated Pydantic models from the `GlobalState` and transforms them into high-resolution PDFs (the canvases), the markdown `AgentPromptSpec.md`, and the `EXPERIMENT_PLAN.md`.

### Data Flow and Interactions

The data flow is strictly sequential and additive. The user initiates the process with a core topic. The LangGraph orchestrator passes this topic to the first node, which generates the initial Lean Canvas. This canvas is appended to the `GlobalState` and subsequently injected into the prompt for the next node. This "Chain of Thought" data flow continues, with each node consuming the accumulated state and appending its specific output (e.g., Empathy Map, Value Proposition Canvas). At the HITL gates, the flow pauses, allowing the user to mutate the `GlobalState` before execution resumes. External interactions, such as Tavily searches or RAG queries, are isolated within specific nodes and their results are strictly typed before being added to the state.

### Explicit Rules on Boundary Management and Separation of Concerns

To prevent the emergence of "God Classes" and tightly coupled logic, the following explicit architectural rules are strictly enforced:

1.  **Node Independence:** A LangGraph node must never directly instantiate an LLM client, access the filesystem, or interact with the Pyxel UI. Nodes must purely contain business logic: receiving state, calling abstracted services (injected via dependency injection), and returning state updates.
2.  **Immutable State Transitions:** The `GlobalState` within LangGraph should be treated as functionally immutable during a node's execution. Nodes must return a dictionary representing the *updates* to the state, which LangGraph then merges. Direct mutation of the state object within a node is strictly prohibited to prevent race conditions and unpredictable behavior.
3.  **UI/Backend Decoupling:** The Pyxel main loop must run independently of the LangGraph execution thread. The UI must only read from a thread-safe copy of the state or listen to discrete events (e.g., `NodeCompletedEvent`, `ApprovalStampEvent`). It must never trigger backend logic directly outside of the designated HITL input gates.
4.  **Configuration Centralisation:** All configurable parameters, API keys, and environment variables must be managed through a centralized Pydantic `Settings` model. Deeply nested configuration validation must be handled by dedicated validator classes (e.g., in `validators.py`), keeping the configuration models clean and declarative.
5.  **Mockability:** Every external dependency (LLM, RAG, File System) must be defined by an interface (Protocol) and injected into the services. This guarantees that all unit tests can run in complete isolation without requiring real API keys or filesystem access.

### Mermaid Diagram

```mermaid
graph TD
    subgraph Presentation Layer
        UI[Pyxel Gamified UI]
        HITL[Human-in-the-Loop Gateway]
    end

    subgraph Orchestration Layer
        LG[LangGraph State Machine]
        State[Global Immutable State]
    end

    subgraph Cognitive & Data Layer
        LLM[LLM Service / Factory]
        RAG[LlamaIndex RAG Engine]
        Tools[Tavily / External APIs]
    end

    subgraph Output Engine
        PDF[PDF Generator]
        MD[Markdown Generator]
    end

    UI -->|Polls State/Events| LG
    UI -->|User Feedback| HITL
    HITL -->|State Mutation| State

    LG -->|Read/Write Updates| State
    LG -->|Executes Nodes| Nodes

    subgraph Nodes [Business Logic Nodes]
        N1[Ideator Node]
        N2[Persona Node]
        N3[VPC Node]
        N4[Journey Node]
        N5[Review Nodes]
    end

    Nodes -->|Abstracted Calls| LLM
    Nodes -->|Queries| RAG
    Nodes -->|Searches| Tools

    LG -->|Final State| PDF
    LG -->|Final State| MD

    style UI fill:#f9f,stroke:#333,stroke-width:2px
    style LG fill:#bbf,stroke:#333,stroke-width:2px
    style State fill:#dfd,stroke:#333,stroke-width:2px
```

## 4. Design Architecture

The design architecture defines the physical organization of the codebase, the structure of the core domain models, and the strategy for integrating new requirements while preserving the integrity of the existing system. The additive mindset is paramount here: we extend rather than replace.

### File Structure Overview

The project adheres to a strict modular structure, ensuring clear boundaries between domain models, business logic (agents/services), configuration, and the presentation layer.

```ascii
.
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── ideator.py         # Extends existing to support new LeanCanvas constraints
│   │   ├── persona.py         # NEW: Persona & Empathy Mapping logic
│   │   ├── cpo.py             # Existing RAG-driven mentor
│   │   ├── reviewers.py       # NEW: The 3H Review Agents (Hacker, Hipster, Hustler)
│   │   └── builder.py         # MODIFIED: Repurposed for AgentPromptSpec generation
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py          # Centralized Pydantic Settings
│   │   ├── constants.py       # Hardcoded strings, prompts, and default paths
│   │   ├── exceptions.py      # Custom business exceptions
│   │   ├── factory.py         # Dependency Injection factory
│   │   ├── graph.py           # The LangGraph workflow definitions (Extended for 14 steps)
│   │   ├── llm.py             # LLM client wrappers
│   │   ├── nodes.py           # LangGraph node implementations (Step 1-14)
│   │   ├── simulation.py      # Main simulation runner
│   │   └── validators.py      # Complex configuration validators
│   ├── data/
│   │   ├── __init__.py
│   │   ├── rag.py             # LlamaIndex transcript ingestion
│   │   └── transcript_service.py # Audio/text processing
│   ├── domain_models/
│   │   ├── __init__.py
│   │   ├── common.py
│   │   ├── lean_canvas.py     # Existing, slightly extended
│   │   ├── persona.py         # NEW: Persona and EmpathyMap schemas
│   │   ├── vpc.py             # NEW: ValuePropositionCanvas schemas
│   │   ├── journey.py         # NEW: MentalModelDiagram and CustomerJourney schemas
│   │   ├── sitemap.py         # NEW: SitemapAndStory schemas
│   │   ├── experiment.py      # NEW: ExperimentPlan schema
│   │   └── spec.py            # NEW: AgentPromptSpec schema
│   ├── services/
│   │   ├── __init__.py
│   │   ├── file_service.py    # Atomic, safe file I/O operations
│   │   └── pdf_service.py     # NEW: PDF Generation for canvases using fpdf2
│   ├── ui/
│   │   ├── __init__.py
│   │   └── app.py             # Pyxel frontend (Extended with Approval animations)
│   └── main.py                # CLI Entry Point
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── dev_documents/
│   ├── system_prompts/
│   │   └── SYSTEM_ARCHITECTURE.md
│   ├── ALL_SPEC.md
│   └── USER_TEST_SCENARIO.md
├── tutorials/
│   └── UAT_AND_TUTORIAL.py    # The unified Marimo executable tutorial
└── pyproject.toml
```

### Core Domain Pydantic Models Structure and Typing

The system relies heavily on Pydantic V2 for schema validation. All core domain models utilize `model_config = ConfigDict(extra="forbid")` to strictly prevent hallucinated fields. The models are designed hierarchically, promoting reuse.

*   `ValuePropositionCanvas`: Integrates `CustomerProfile` (pains, gains, jobs) and `ValueMap`. This serves as the foundational validation that the proposed solution actually addresses the identified problems.
*   `MentalModelDiagram`: Composed of multiple `MentalTower` objects representing beliefs and cognitive tasks. This model provides the psychological grounding for the customer journey.
*   `AlternativeAnalysis`: Evaluates `AlternativeTool` objects against switching costs to derive a '10x Value' proposition.
*   `CustomerJourney`: A sequential list of `JourneyPhase` objects. Crucially, each phase must explicitly reference a `MentalTower` (via `mental_tower_ref`), enforcing logical continuity.
*   `SitemapAndStory`: Combines the navigational structure (`Route`) with the single most critical `UserStory` required for the MVP.
*   `AgentPromptSpec`: The ultimate output schema, detailing routing constraints, state machines (loading, error, empty), and mermaid flowchart representations.
*   `ExperimentPlan`: Defines the AARRR metrics (`MetricTarget`) necessary to validate the MVP in the real world.

### Integration Points (Additive Mindset)

The integration of these new Pydantic models with the existing architecture is handled with strict adherence to the Open-Closed Principle.

1.  **Extending `GlobalState`:** The existing LangGraph `GlobalState` dictionary (or TypedDict) will be extended to include optional keys for the new models (e.g., `vpc: Optional[ValuePropositionCanvas] = None`). Existing nodes will not be broken, as they only read the keys they are aware of.
2.  **Repurposing `BuilderAgent`:** The existing `BuilderAgent`, which previously called the v0.dev API, will be safely repurposed. Instead of making an external API call, its internal implementation will be swapped (via the factory pattern) to utilize the new `spec.py` domain models and generate the `AgentPromptSpec.md` file locally using the `FileService`. The external interface of the agent remains consistent.
3.  **Inserting New Nodes:** The LangGraph workflow in `graph.py` will be carefully modified to insert the new steps (e.g., `vpc_node`, `journey_node`) between the existing ideation and simulation phases. The edges of the graph will be updated to route the execution flow through these new nodes, applying the HITL feedback gates appropriately.
4.  **UI Augmentation:** The Pyxel UI will not be rewritten. Instead, a new event listener will be added to the existing game loop to detect when a new canvas is added to the `GlobalState`. Upon detection, the new "Approval Stamp" animation subroutine will be triggered, gracefully extending the user experience without disrupting the core rendering logic.

## 5. Implementation Plan

The project development is meticulously decomposed into exactly 6 implementation cycles. Each cycle represents a self-contained, verifiable increment of value, strictly following the AC-CDD methodology and the additive architectural mindset. This approach mitigates risk and ensures steady progress towards the final requirements.

### Cycle 01: Core Schemas and Foundational Infrastructure

**Objective:** To lay the absolute groundwork for the schema-driven generation process by implementing all new Pydantic domain models and extending the core configuration and state management.

**Detailed Features:**
This cycle begins by translating the rigorous requirements of `ALL_SPEC.md` into executable Python code. We will implement the complete suite of Pydantic models within the `src/domain_models/` directory. This includes `ValuePropositionCanvas.py`, `MentalModelDiagram.py`, `AlternativeAnalysis.py`, `CustomerJourney.py`, `SitemapAndStory.py`, `ExperimentPlan.py`, and `AgentPromptSpec.py`. Every model must utilize `ConfigDict(extra="forbid")` and employ strict field validators (e.g., ensuring string lengths, validating regex patterns for URLs, and enforcing numerical ranges for emotion scores). Following the schema definition, the `GlobalState` type definition in `src/core/state.py` will be extended to accommodate these new data structures as optional fields. The centralized `Settings` model in `src/core/config.py` will be updated to include configuration for the new PDF generation paths and updated LLM prompts. Finally, the `FileService` will be hardened to ensure atomic, cross-platform file writes using `tempfile` and `os.replace`, preparing the infrastructure for robust document generation later in the workflow. This cycle establishes the unbreakable contract that the rest of the system will rely upon.

### Cycle 02: Phase 1 & 2 Workflow Integration (Ideation to CPF)

**Objective:** To construct the first half of the LangGraph workflow, guiding the system from initial ideation through the generation of the Value Proposition Canvas and the first Human-in-the-Loop (HITL) gateway.

**Detailed Features:**
This cycle focuses on building the LangGraph nodes for Phase 1 (Idea Verification) and Phase 2 (Customer / Problem Fit). We will implement the `ideator_node` to leverage Tavily search and generate Lean Canvases. Next, we will implement the `persona_node` to generate detailed customer profiles based on the selected canvas. Subsequently, the `alternative_analysis_node` and `vpc_node` will be developed. A critical challenge here is ensuring strict context inheritance: the prompt for the `vpc_node` must dynamically ingest the output of the `persona_node`. We will then wire these nodes together in `src/core/graph.py`, establishing the sequential state transitions. Crucially, we will implement the logic for `[HITL Gate 1.5 - CPF Feedback]`. This involves pausing the LangGraph execution, utilizing the newly integrated `fpdf2` library to generate a high-resolution PDF of the Value Proposition Canvas, and extending the Pyxel UI to trigger the "Approval" stamp animation. The UI will then present an input prompt to capture user feedback, which will be injected back into the state before execution resumes.

### Cycle 03: Phase 3 Workflow Integration (Problem / Solution Fit)

**Objective:** To implement the complex reasoning required to map psychological mental models to concrete user journeys and wireframes, completing the core problem-solution fit sequence.

**Detailed Features:**
Building upon the context established in Cycle 02, this cycle tackles Phase 3. We will implement the `mental_model_journey_node`. This is highly complex as it requires the LLM to construct abstract `MentalTower` structures and then logically map a sequential `CustomerJourney` where every action references a specific tower. The prompt engineering here must be exceptionally tight to prevent hallucinations. Following this, the `sitemap_wireframe_node` will be implemented to translate the worst pain points identified in the journey into a concrete URL structure and text-based wireframes. We will define the `SitemapAndStory` Pydantic models to enforce this structure. The LangGraph edges will be updated to connect Phase 2 to Phase 3. We will implement `[HITL Gate 1.8 - PSF Feedback]`, repeating the PDF generation, Pyxel "Approval" animation, and user feedback capture process for the Mental Model and Journey maps. This cycle ensures the system can successfully navigate the most logically demanding portion of the methodology.

### Cycle 04: The 3H Review and Virtual Market Simulation

**Objective:** To introduce the specialized AI agents (Virtual Customer, Hacker, Hipster, Hustler) and orchestrate the multi-agent review process (Phase 4), ensuring the proposed solution is thoroughly scrutinized.

**Detailed Features:**
This cycle introduces the critical "Gekizume" (harsh feedback) elements. We will implement the `virtual_customer_node`, instantiating an agent that assumes the exact persona and mental model generated in previous cycles to ruthlessly critique the wireframes. Next, we will implement the `3h_review_node`, which orchestrates a sub-graph involving the Hacker (technical feasibility), Hipster (UX friction), and Hustler (unit economics) agents. Each agent will be provided with specific prompts that strictly bind them to the previously generated context (e.g., the Hustler must reference the Alternative Analysis). The system will be configured to handle the potentially iterative nature of this review process, utilizing LangSmith to trace the execution and implementing circuit breakers (e.g., `max_turns` limits and specific termination phrases) to prevent infinite loops during the agent debates. The Pyxel UI will be updated to render these specialized dialogues, ensuring the "de-identification" principle is maintained as the user observes the AI agents arguing over the product specifications.

### Cycle 05: Final Specification and Experiment Planning

**Objective:** To repurpose the build phase, completely removing external UI API dependencies and instead generating the universal `AgentPromptSpec.md` and the rigorous `EXPERIMENT_PLAN.md`.

**Detailed Features:**
This cycle represents a major architectural pivot. We will completely refactor the `spec_generation_node` (formerly the Builder Agent). Instead of calling an external API, this node will aggregate the entire `GlobalState`—the VPC, Mental Model, Journey, Sitemap, and 3H Review feedback. It will then apply "subtraction thinking" via a specialized prompt to strip away unnecessary features. The output will be strictly constrained by the `AgentPromptSpec` Pydantic model, ensuring the generation of valid Mermaid state machines and precise routing constraints. Concurrently, the `experiment_planning_node` will be implemented to generate the `ExperimentPlan` schema, focusing on AARRR metrics and pivot conditions. We will implement `[HITL Gate 3]`, triggering the final Pyxel approval animation and generating the corresponding PDFs. Finally, the `FileService` will write the beautifully formatted Markdown files to the local directory. This ensures the system produces the ultimate required outputs flawlessly.

### Cycle 06: Observability, Refinement, and Marimo Tutorials

**Objective:** To harden the system for production use by integrating comprehensive telemetry, finalizing the RAG integration, and building the executable Marimo tutorials for user onboarding.

**Detailed Features:**
The final cycle focuses on system robustness and user experience. We will ensure LangSmith tracing is fully operational across all LangGraph nodes, validating that token consumption and context propagation are properly monitored. The existing RAG functionality (the `transcript_ingestion_node` and CPO mentor) will be thoroughly tested against the newly structured data flow to ensure it correctly fact-checks the Value Proposition Canvas based on ingested transcripts. We will finalize the `governance_node` to output the final JTC "Ringi-Sho" document. Crucially, we will develop the `tutorials/UAT_AND_TUTORIAL.py` Marimo notebook. This single file will encapsulate all User Acceptance Testing (UAT) scenarios. It will demonstrate how to initialize the system, mock external dependencies for CI testing, and step through the entire 6-phase process, allowing users to interactively verify the system's capabilities and understand the complex methodology. We will conduct extensive end-to-end testing, applying the strictest `ruff` and `mypy` constraints to ensure the entire codebase is pristine and ready for enterprise deployment.

## 6. Test Strategy

The testing strategy is designed to rigorously validate the highly complex, multi-agent architecture while strictly adhering to the principles of isolation, determinism, and side-effect-free execution. We employ a comprehensive approach spanning Unit, Integration, and End-to-End (E2E) testing across all 6 cycles.

### Cycle 01: Core Schemas and Foundational Infrastructure

**Testing Approach:**
*   **Unit Testing (Pydantic Models):** This cycle is heavily focused on strict validation. We will write extensive pytest suites to intentionally trigger `ValidationError` exceptions by passing invalid data types, exceeding length constraints, and testing the `extra="forbid"` configuration. Crucially, as per our internal guidelines, we will test `ValidationError` exceptions using `<ModelClass>.model_validate({"field": valid_value, "extra_field": "bad"})` to avoid strict MyPy `[call-arg]` errors. We will verify all regex whitelisting and sanitization logic.
*   **Unit Testing (File Service):** The `FileService` must be tested for atomic writes. We will use the `unittest.mock.patch` to simulate `OSError` and `ImportError` scenarios to ensure fallback mechanisms for cross-platform file locking function correctly. We will use `tempfile.TemporaryDirectory()` to ensure filesystem tests leave no artifacts.
*   **Configuration Testing:** We will test the centralized configuration by mocking environment variables. To reset the configuration state during unit testing, we will explicitly use `src.core.config.clear_settings_cache()` instead of `Settings.reload()` to properly manage the singleton pattern.

### Cycle 02: Phase 1 & 2 Workflow Integration (Ideation to CPF)

**Testing Approach:**
*   **Unit Testing (Nodes):** Individual LangGraph nodes (e.g., `persona_node`, `vpc_node`) will be tested in absolute isolation. We will mock the LLM factory (`src.core.llm.LLMFactory.get_llm`) to return deterministic, pre-configured Pydantic models. We will assert that the node correctly receives the simulated state, applies the mocked LLM output, and returns the expected state update dictionary.
*   **Integration Testing (LangGraph Edges):** We will instantiate a partial LangGraph containing only Phases 1 and 2. We will inject a mocked LLM and verify that the state transitions correctly from node to node, ensuring that the outputs of one node are successfully passed as inputs to the next.
*   **Side-Effect Mitigation:** All PDF generation calls within the HITL gates will be mocked using `patch` during standard test runs to prevent disk I/O bottlenecks. Specific PDF generation tests will use temporary directories.

### Cycle 03: Phase 3 Workflow Integration (Problem / Solution Fit)

**Testing Approach:**
*   **Complex Context Testing:** The primary risk in this cycle is the logical mapping between the Mental Model and the Customer Journey. We will write targeted unit tests that provide the LLM (mocked) with a complex `MentalModelDiagram` and assert that the resulting `CustomerJourney` phases correctly reference the valid `MentalTower` IDs.
*   **Error Boundary Testing:** We will test the `NodeExecutor` wrapper to ensure that if a node implementation raises an unexpected exception (e.g., a parsing error), the executor correctly catches it, logs the defined error message, and prevents the entire graph from crashing.
*   **Integration Testing:** We will expand the partial LangGraph test from Cycle 02 to include Phase 3, running a continuous mocked execution from Ideation through to Sitemap generation, verifying state accumulation.

### Cycle 04: The 3H Review and Virtual Market Simulation

**Testing Approach:**
*   **Multi-Agent Mocking:** Testing multi-agent debates requires careful mock orchestration. We will utilize `side_effect` on the mocked LLM to return a sequence of responses simulating an argument (e.g., Hacker disagrees, Hipster agrees, Hacker concedes).
*   **Circuit Breaker & Timeout Testing:** This is critical. We will explicitly test the `max_turns` limit and the string-matching termination logic to ensure the graph forcibly exits a simulated infinite loop. We will also test timeout scenarios for RAG queries or LLM calls, ensuring resources are cleaned up by asserting that `executor.shutdown(wait=False, cancel_futures=True)` is called.
*   **UI Decoupling Verification:** We will test the event bus mechanism by asserting that state changes correctly emit the expected events, without actually running the Pyxel main loop, guaranteeing the decoupling of the presentation layer.

### Cycle 05: Final Specification and Experiment Planning

**Testing Approach:**
*   **Data Aggregation Testing:** We will construct a massively complex, artificially populated `GlobalState` containing all canvases and review feedback. We will then execute the `spec_generation_node` (with a mocked LLM) and assert that the prompt construction logic correctly parses and includes all necessary context without exceeding token limits or causing recursion depth errors (ensuring iterative traversal of nested structures).
*   **Output Formatting Testing:** We will verify that the generated markdown and Mermaid strings are properly sanitized (stripping unintended HTML) and formatted correctly before being passed to the `FileService`.
*   **E2E Path Traversal Prevention:** We will write specific security tests attempting to pass malicious filenames (e.g., `../../../etc/passwd`) to the output generation nodes, asserting that the strict regex validation and `Path.resolve(strict=True)` logic successfully block the attack.

### Cycle 06: Observability, Refinement, and Marimo Tutorials

**Testing Approach:**
*   **Mock Mode Validation:** We will heavily test the `MOCK_MODE` functionality. By setting `os.environ['MOCK_MODE'] = 'true'`, we will run the entire system pipeline and assert that it successfully bypasses API key validations and returns graceful fallback objects (empty iterators or dummy models) without failing. This is essential for CI environments.
*   **E2E Marimo Execution:** The ultimate test is the execution of the `tutorials/UAT_AND_TUTORIAL.py` file. We will use a script to programmatically execute the Marimo notebook in a headless environment, verifying that all cells run without raising exceptions and that the expected outputs are generated in the designated temporary directories.
*   **Proof of Work Generation:** As mandated, a test execution log will be generated at the end of the E2E suite using `subprocess.run(['pytest'], capture_output=True)` and saved securely to `dev_documents/test_execution_log.txt` to satisfy Auditor requirements.
