# System Architecture: The JTC 2.0 (Remastered Edition)

## 1. Summary

The "JTC 2.0 (Remastered Edition)" represents a multi-agent simulation platform designed to modernise and streamline the creation of new businesses within traditional Japanese enterprises. The previous architecture, although capable of simulating political resistance and generating initial Minimum Viable Products (MVPs), suffered from artificial intelligence "hallucinations" and an over-reliance on a single UI generation application programming interface (API).

This Remastered Edition refines the core methodology, adopting a rigorous, schema-driven approach that completely eliminates contextual leaps. It achieves this by forcing the Language Learning Model (LLM) to populate Pydantic models in a sequential "Chain of Thought" pipeline. The ultimate objective is no longer the direct deployment of code via v0.dev, but the generation of an impeccable "AgentPromptSpec.md" and a precise "Experiment Plan". These artefacts are universally compatible with autonomous coding agents such as Cursor, Windsurf, or Google Antigravity. Consequently, the JTC 2.0 platform functions as an enduring, universally applicable requirements definition engine.

The architecture strictly maintains the "脱同一化" (De-identification) strategy via a Pyxel-based retro user interface, adding visual "Approval" (Ringi-sho stamp) mechanisms at key transition gates to enhance user engagement.

## 2. System Design Objectives

The overarching design objective of the JTC 2.0 Remastered architecture is to construct an autonomous, multi-agent reasoning engine that operates with absolute determinism, strict type enforcement, and profound user psychological safety. To achieve these ambitious goals, the system must adhere to four primary pillars.

Firstly, the system must categorically eliminate AI hallucinations. Large Language Models (LLMs), by their very stochastic nature, frequently skip essential logical steps when tasked with generating complex systems from rudimentary ideas. They suffer from a tendency to invent "plausible falsehoods." To counteract this, the system enforces a strict, mathematical "Customer Problem Fit" (CPF) to "Problem Solution Fit" (PSF) pipeline. This pipeline is not merely a sequence of prompts; it is a rigid state machine. Every node within the LangGraph orchestrator must output data that conforms exactly to tightly constrained Pydantic `BaseModel` schemas equipped with the `extra="forbid"` configuration. This configuration acts as an impenetrable barrier, guaranteeing that the LLM cannot invent unsupported features, hallucinate data fields, or introduce any concept that was not explicitly requested. By rigorously validating every intermediate artefact—from the foundational Empathy Map to the intricate Value Proposition Canvas and the chronological Customer Journey—the system ensures a logically sound, unbreakable progression of ideas. If an LLM attempts a logical leap, the Pydantic schema validation will violently reject the output, forcing the agent to retry or halting the execution entirely.

Secondly, the system must remain completely agnostic to the final code generation tool, avoiding any form of vendor lock-in. The previous iteration of the JTC 2.0 architecture was tightly coupled to the v0.dev API. While this provided immediate visual gratification, it severely limited the system's flexibility and longevity, tying the platform's success to the continued existence and API stability of a single third-party provider. The Remastered Edition pivots dramatically to a strategy of generating a universal standard specification. The system must aggregate all validated business logic, mental models, and user journeys into a comprehensive, beautifully formatted Markdown document (`MVP_PROMPT_SPEC.md`). This document acts as the ultimate "source of truth." It must be structured precisely to provide maximum context to *any* external, third-party AI coding assistant—be it Cursor, Windsurf, or a future, yet-to-be-invented tool. This agnostic approach significantly increases the longevity, utility, and inherent value of the JTC 2.0 platform.

Thirdly, the system must meticulously safeguard the user's emotional wellbeing through an advanced strategy of "De-identification." Innovation within traditional corporate structures (JTCs) often involves harsh, personal, and sometimes vindictive criticism. The JTC 2.0 platform is designed to simulate this exact environment (the "Gekizume" or intense grilling), but it must ensure the human user does not internalize the AI's rejections. To achieve this psychological distancing, the architecture deliberately retains the 16-colour, low-resolution Pyxel graphical user interface. This retro aesthetic abstracts the brutal feedback from the "Virtual Customer" and "JTC Board" agents, framing the painful experience as a harmless role-playing game. Furthermore, the system introduces a new, highly engaging Human-in-the-Loop (HITL) approval mechanism. When a complex schema is successfully generated and validated, the system must render an animated "Approval Stamp" (Hanko) in the Pyxel interface, accompanied by satisfying retro sound effects, whilst simultaneously exporting a high-resolution PDF for the user to review. This gamification of the bureaucratic approval process creates a powerful sense of accomplishment, transforming a traditionally demoralizing process into an engaging, forward-moving journey.

Finally, the system must ensure rigorous enterprise-grade observability and cost control. Given the sheer complexity of the multi-agent debates (specifically the 3H Review and the JTC Board Simulation, where LLMs converse with other LLMs), the risk of infinite loops, deadlocks, or excessive token consumption is unacceptably high. The architecture must mandate the use of LangSmith for complete, hierarchical trace integration. Every LangGraph transition, every tool call, and every LLM inference must be immutably logged. Additionally, robust, configurable circuit breakers must be implemented directly into the graph's transition logic to actively monitor the dialogue state. These breakers must detect repetitive phrase patterns or excessive turn counts, violently forcing termination if agents reach a deadlock. This is absolutely critical for controlling operational costs, preventing API rate limit exhaustion, and maintaining overall system stability in a production environment.

## 3. System Architecture

The overarching system architecture relies on LangGraph to orchestrate a complex, multi-stage workflow, enforcing strict data transformation rules. The architecture is divided into clear, impenetrable boundary layers to ensure the absolute Separation of Concerns (SoC) and maintain a highly cohesive, loosely coupled codebase.

At the very core is the **Orchestration Layer** (LangGraph). This layer acts as the immutable brain of the operation, dictating the sequential execution of the six primary phases. It manages the central `GlobalState`, which acts as the single source of truth for the entire simulation. Crucially, the Orchestration Layer passes strictly validated Pydantic models between the various agent nodes. The state is strictly immutable during agent execution; it is only updated via clearly defined, thoroughly tested state reducer functions that occur *between* node executions. This guarantees that no rogue agent can corrupt the global context.

Beneath the Orchestration Layer is the **Agent Execution Layer**. This layer contains the specific, highly specialized AI personas: the Ideator, the Virtual Customer, the Finance Manager, the Sales Manager, the Hacker, the Hipster, the Hustler, and the final Builder. A critical architectural constraint is placed upon these agents: they do not possess direct access to the `GlobalState`. Instead, they receive specific, narrowly scoped contexts injected directly into their prompts. Crucially, they are explicitly instructed to never generate ideas from scratch. They must strictly inherit and reason upon the output of previous nodes. For instance, the Virtual Customer agent is incapable of critiquing the product based on its own biases; its critique is mathematically constrained by the precise `MentalModelDiagram` and `AlternativeAnalysis` generated in the prior phase.

The **Integration Layer** manages all external API communications. This includes the OpenAI client for LLM inference, the Tavily client for deep market research, and the local Vector Store (LlamaIndex) for retrieving customer interview transcripts. All external calls must be wrapped in generic, decoupled interfaces (e.g., `LLMFactory`, `SearchClient`). This ensures that the core business logic remains entirely oblivious to the specific implementation details of the external services, allowing for seamless swapping of providers (e.g., switching from OpenAI to Anthropic) without altering the LangGraph nodes.

The **Presentation Layer** consists of the Pyxel-based User Interface and the highly optimized PDF Document Generator. The Pyxel UI operates asynchronously, rendering the simulation state and providing the crucial Human-in-the-Loop feedback mechanism. The Document Generator acts as a translation layer, converting the complex, machine-readable Pydantic models into beautiful, human-readable Markdown and PDF formats for user review during the HITL pauses.

**Boundary Management Rules:**
1. **Strict Dependency Injection**: Agents must not instantiate external clients (e.g., LLM APIs, Search APIs) directly within their class definitions or methods. All dependencies must be passed via explicit interfaces during the node creation factory functions (e.g., `make_ideator_node(llm_client)`).
2. **State Isolation**: The Pyxel UI must never directly modify the `GlobalState`. It strictly reads from the state to render visuals. When user input is required, it sends specific, validated command objects back to the Orchestration Layer to trigger controlled state transitions (e.g., proceeding through a HITL gate).
3. **No Direct I/O in Nodes**: Graph nodes must absolutely not write directly to the file system. All file operations (e.g., generating PDFs or the `AgentPromptSpec.md`) must be handled by a dedicated, heavily tested `FileService`. This service must utilize strict atomic operations (`tempfile.mkstemp`, `os.replace`, and `fcntl.flock`) to prevent partial writes, race conditions, and file corruption during parallel execution.

```mermaid
graph TD
    subgraph "External World"
        User(User)
        Transcripts[Interview Audio/Text]
    end

    subgraph "Presentation Layer"
        PyxelUI[Pyxel Retro UI]
        PDFGen[PDF Document Generator]
        HITLGate[Human-in-the-Loop Gate]
    end

    subgraph "Integration Layer"
        RAG[LlamaIndex Vector Store]
        LLM[OpenAI API / LLM Client]
        Search[Tavily Search API]
    end

    subgraph "Orchestration Layer (LangGraph)"
        GlobalState[(Global State)]
        Phase1[Phase 1: Idea Verification]
        Phase2[Phase 2: CPF Validation]
        Phase3[Phase 3: PSF Mapping]
        Phase4[Phase 4: Validation & Review]
        Phase5[Phase 5: Output Spec Generation]
        Phase6[Phase 6: Governance Check]
    end

    subgraph "Agent Execution Layer"
        IdeatorAgent[Ideator Agent]
        CPOAgent[CPO Fact Checker]
        VirtualCustomer[Virtual Customer Agent]
        JTCBoard[JTC Board: Finance & Sales]
        Review3H[3H Review: Hacker, Hipster, Hustler]
        BuilderAgent[Builder Spec Agent]
    end

    User <--> PyxelUI
    PyxelUI <--> HITLGate
    HITLGate --> GlobalState
    Transcripts --> RAG

    GlobalState --> Phase1
    Phase1 --> IdeatorAgent
    IdeatorAgent --> Search
    IdeatorAgent --> LLM

    Phase1 --> Phase2
    Phase2 --> CPOAgent
    CPOAgent --> RAG
    CPOAgent --> LLM

    Phase2 --> Phase3
    Phase3 --> LLM

    Phase3 --> Phase4
    Phase4 --> VirtualCustomer
    Phase4 --> JTCBoard
    Phase4 --> Review3H
    VirtualCustomer --> LLM
    JTCBoard --> LLM
    Review3H --> LLM

    Phase4 --> Phase5
    Phase5 --> BuilderAgent
    BuilderAgent --> LLM

    Phase5 --> Phase6
    Phase6 --> PDFGen
    Phase6 --> LLM

    Phase2 -.-> PDFGen
    Phase3 -.-> PDFGen

```

## 4. Design Architecture

The project structure is meticulously designed around strict Domain-Driven Design (DDD) principles. This ensures that the core domain logic (the Pydantic schemas representing the business concepts) is entirely isolated from infrastructure concerns (like API calls) and presentation logic (like Pyxel rendering). This separation is paramount for maintainability and testability.

```ascii
.
├── src/
│   ├── agents/
│   │   ├── base.py              # Base Agent classes and common logic
│   │   ├── personas.py          # Definitions for specific agent roles
│   │   ├── ideator.py           # Phase 1 Ideation logic
│   │   ├── cpo.py               # Phase 2 RAG Fact-checking
│   │   ├── virtual_customer.py  # New Phase 4 validation agent
│   │   ├── review_3h.py         # New Phase 4 3H review logic
│   │   └── builder.py           # Refactored for Markdown spec generation
│   ├── core/
│   │   ├── config.py            # Centralized settings and validation
│   │   ├── constants.py         # Immutable system constants
│   │   ├── exceptions.py        # Custom domain exceptions
│   │   ├── factory.py           # Dependency Injection orchestrator
│   │   ├── graph.py             # Main LangGraph definition and compilation
│   │   ├── nodes.py             # Individual node execution wrappers
│   │   ├── simulation.py        # Sub-graph for multi-agent debates
│   │   └── services/
│   │       ├── file_service.py  # Atomic filesystem operations
│   │       └── pdf_service.py   # New generator for HITL visual artifacts
│   ├── data/
│   │   └── rag.py               # LlamaIndex ingestion and querying
│   ├── domain_models/
│   │   ├── common.py            # Shared schema utilities
│   │   ├── canvas_models.py     # New models (VPC, Journey, etc.)
│   │   ├── enums.py             # System enumerations
│   │   ├── lean_canvas.py       # Legacy Lean Canvas models
│   │   ├── state.py             # Extended GlobalState definition
│   │   └── validators.py        # Reusable Pydantic validators
│   ├── ui/
│   │   ├── renderer.py          # Pyxel game loop and drawing
│   │   └── components/          # Reusable Pyxel UI elements
│   └── main.py                  # CLI entry point
```

### Domain Models Extension Strategy

The absolute core integration requirement of this Remastered Edition is the seamless addition of the massive new schema models without compromising the integrity of the existing `GlobalState` or breaking the legacy Ideation flow. The existing `src/domain_models/state.py` defines the fundamental `GlobalState`. We will employ a strictly additive extension strategy, appending the newly required fields while meticulously preserving the existing ones to ensure absolute backwards compatibility.

The new schemas will be housed in a dedicated, isolated module named `src/domain_models/canvas_models.py`. These heavily constrained models include:

1.  **ValuePropositionCanvas**: Encompasses a detailed `CustomerProfile` (Jobs, Pains, Gains) and a `ValueMap` (Products, Pain Relievers, Gain Creators), ensuring perfect logical alignment.
2.  **MentalModelDiagram**: Comprises multiple `MentalTower` instances, mapping deep-seated user beliefs to specific cognitive tasks.
3.  **AlternativeAnalysis**: Tracks multiple `AlternativeTool` objects, strictly calculating the financial and UX friction to prove the requisite switching costs.
4.  **CustomerJourney**: Defines a chronological list of `JourneyPhase` objects, explicitly forcing the identification of the single "worst_pain_phase."
5.  **SitemapAndStory**: Maps application routing via strongly typed `Route` objects and specifies the singular, core `UserStory` that the MVP must solve.
6.  **ExperimentPlan**: Outlines rigorous `MetricTarget` objects for the AARRR funnel, forcing a definition of PMF (Product-Market Fit) prior to any development.
7.  **AgentPromptSpec**: The ultimate output model, defining the `StateMachine` (Success, Loading, Error, Empty) and strict UI validation rules.

All new models will inherit directly from `pydantic.BaseModel` and mandate `model_config = ConfigDict(extra="forbid")`. This is non-negotiable; it is the primary defense mechanism against LLM hallucination.

Within `src/domain_models/state.py`, the `GlobalState` will be updated to include Optional fields for these new models. This ensures that the state can be instantiated early in the pipeline without requiring all data immediately.

```python
class GlobalState(BaseModel):
    # ... existing fields (phase, topic, target_persona, etc.) ...

    # Remastered Edition Fields
    value_proposition: ValuePropositionCanvas | None = None
    mental_model: MentalModelDiagram | None = None
    alternative_analysis: AlternativeAnalysis | None = None
    customer_journey: CustomerJourney | None = None
    sitemap_and_story: SitemapAndStory | None = None
    experiment_plan: ExperimentPlan | None = None
    agent_prompt_spec: AgentPromptSpec | None = None
```

This strictly additive approach ensures that previous test suites relying on the instantiation of `GlobalState` will not fail, as the new fields default to `None` until explicitly populated by the subsequent Remastered pipeline phases.

## 5. Implementation Plan

The project development is rigorously divided into exactly six sequential implementation cycles. Each cycle represents a massive, complete, and independently testable increment of functionality. Developers must adhere strictly to these boundaries.

### Cycle 1: Domain Models and Configuration Baseline

**Objective:** The singular goal of this phase is to establish the absolute, unyielding foundational schema and environment necessary for the Remastered pipeline. We must guarantee absolute type safety before a single API call is made. This cycle sets the concrete rules that the AI must follow.

**Tasks:**
1.  **Schema Implementation:** We will implement all the new Pydantic models (`ValuePropositionCanvas`, `MentalModelDiagram`, `AlternativeAnalysis`, `CustomerJourney`, `SitemapAndStory`, `ExperimentPlan`, `AgentPromptSpec`) precisely as defined in the domain specifications into `src/domain_models/canvas_models.py`.
2.  **Constraint Enforcement:** Every single model must be configured with `extra="forbid"`. We will implement incredibly strict field validators using `@field_validator`. For example, we must ensure that the `emotion_score` within a `JourneyPhase` is strictly bounded between an integer value of -5 and 5. We must ensure that the `CustomerJourney` contains no less than 3 phases and no more than 7. These constraints are critical for preventing LLM runaway.
3.  **State Integration:** We will meticulously update the `GlobalState` in `src/domain_models/state.py` to seamlessly incorporate these new models as Optional fields, ensuring backwards compatibility with the existing Ideator flow.
4.  **Observability Mandate:** We will radically enhance `src/core/config.py` to mandate LangSmith configuration. The environment variables `LANGCHAIN_TRACING_V2` and `LANGCHAIN_API_KEY` must be validated upon startup. If these are missing in a production environment, the system must refuse to boot.
5.  **Atomic File Operations:** We will create a robust, entirely standalone `FileService`. This service must be capable of cross-platform atomic writes. It will utilize `tempfile.mkstemp`, `os.replace`, and `fcntl.flock` to guarantee that the final generation of massive Markdown files is never corrupted by parallel executions or sudden system crashes.

### Cycle 2: Phase 1 & 2 - Ideation to Customer Problem Fit (CPF)

**Objective:** This cycle constructs the initial, highly critical pipeline phases that forcibly move an abstract idea from conception to a rigorously validated problem space. It enforces the strict "Chain of Thought" methodology, ensuring the AI cannot guess solutions without proving the problem exists.

**Tasks:**
1.  **Ideator Refactoring:** We will refactor the existing Ideator agent's system prompt to output ideas that perfectly align with the new, required context format, ensuring it feeds cleanly into the subsequent Persona generation.
2.  **Persona & Empathy Execution:** We will implement the `persona_node`. This node will consume the selected idea and force the LLM to generate a high-resolution Persona and Empathy Map. We will extract complex string parsing logic into dedicated validators to handle edge cases where the LLM might inject Markdown code blocks around the JSON output.
3.  **Alternative Friction Analysis:** We will develop the `alternative_analysis_node`. This node is designed to forcefully evaluate existing workarounds. The LLM must explicitly identify the current tools used by the persona and calculate the "10x Value" threshold required to overcome the switching cost.
4.  **Value Proposition Alignment:** We will construct the highly complex `vpc_node`. This node takes the Pain/Gain profile and maps it against the proposed solutions. The LLM must explicitly generate a `fit_evaluation` string that proves the logical connection between the Pain Relievers and the actual Pains.
5.  **RAG Integration:** We will seamlessly integrate the existing `transcript_ingestion_node` (RAG pipeline) and connect it to a refactored CPO Agent. This agent will query the LlamaIndex vector store to relentlessly fact-check the generated VPC against actual customer interview data, acting as an automated "Mom Test."
6.  **The First HITL Gate:** We will implement the foundational Human-in-the-Loop (HITL) pause mechanism within the LangGraph orchestrator. This logic will halt graph execution entirely, persisting the state to disk, and await explicit user feedback on the generated CPF artifacts before allowing progression to Phase 3.

### Cycle 3: Phase 3 - Problem Solution Fit (PSF) Mapping

**Objective:** The objective of Cycle 3 is to translate the deeply validated problem space into a precise, behavioral model and functional specification. Crucially, this must be achieved *without* jumping straight to visual user interfaces. We are building logic, not pixels.

**Tasks:**
1.  **Mental Model Construction:** We will develop the `mental_model_journey_node`. This node consumes the validated persona and generates the internal "Mental Towers." It forces the LLM to hypothesize the deep-seated beliefs driving user behavior, ensuring features are aligned with psychology, not just utility.
2.  **Chronological Journey Mapping:** We will implement the complex logic required to map these abstract Mental Towers into a strictly chronological `CustomerJourney`. The node must explicitly identify and label the single phase with the highest "Pain," as this becomes the focal point for the MVP.
3.  **Structural Wireframing (No Design):** We will construct the `sitemap_wireframe_node`. This node must extract a single, core `UserStory` directly from the identified highest-pain journey phase. It will then translate this story into a pure textual, structural wireframe. We will implement strict sanitization logic (`bleach.clean`) here to ensure the LLM does not attempt to inject HTML or CSS styles into the structural definition.
4.  **The Second HITL Gate:** We will implement the second major HITL gate. This gate allows the user to meticulously review the journey and textual wireframes. The primary function of this gate is to provide explicit instructions to cut unnecessary features (enforcing "subtraction thinking") before any multi-agent debate occurs.

### Cycle 4: Phase 4 - Validation and 3H Review Simulation

**Objective:** This cycle represents the crucible of the JTC 2.0 system. We will subject the strictly defined structural specifications to an aggressive, multi-agent critique to relentlessly validate both the business viability and the technical feasibility before any final specification is generated.

**Tasks:**
1.  **The Virtual Customer Agent:** We will architect the `Virtual Customer` agent. This agent is unique; it must be dynamically instantiated using the previously generated `Persona` and `MentalModelDiagram` as its absolute core system prompt. It will aggressively critique the wireframes from the exact perspective of the defined user, focusing specifically on UX friction.
2.  **JTC Board Re-integration:** We will successfully integrate the existing `JTC Board Simulation` (comprising the skeptical Finance and aggressive Sales managers). They will be tasked with reviewing the `AlternativeAnalysis` to validate the Return on Investment (ROI) and highlight potential market cannibalization risks within the enterprise context.
3.  **The 3H Review Architecture:** We will develop the complex `3H Review Agents` (Hacker, Hipster, Hustler). This requires careful prompt engineering to ensure they maintain their specific personas without collapsing into a generic AI voice.
4.  **Orchestrating the Debate:** We will orchestrate the massive `3h_review_node`. The graph logic must manage the turn-based conversation, ensuring the Hacker focuses purely on technical debt, the Hipster on UX friction against the mental model, and the Hustler entirely on unit economics (LTV/CAC).
5.  **Circuit Breaker Implementation:** We will implement essential circuit-breaker logic utilizing `Settings` parameters. We will monitor the conversation state to detect infinite debate loops (e.g., agents repeatedly agreeing to disagree) or excessive token usage, forcefully terminating the node execution and proceeding with the best-known state to prevent massive API bills.

### Cycle 5: Phase 5 & 6 - Output Generation and UI Integration

**Objective:** The objective of the penultimate cycle is to finalize the physical artifact generation and integrate the deeply satisfying Pyxel-based visual approval rendering. This is where the machine-readable data becomes human-valuable output.

**Tasks:**
1.  **Builder Agent Transformation:** We will radically transform the `Builder Agent`. Instead of making direct API calls to v0.dev to generate React code, it must now consume the entirety of the massive context window (VPC, Journey, wireframes, 3H Feedback) and meticulously populate the final, highly complex `AgentPromptSpec` Pydantic model.
2.  **Experiment Planning:** We will develop the highly specialized `experiment_planning_node` to generate the `ExperimentPlan`. This forces the AI to detail the specific AARRR metrics and explicitly define the pivot conditions (what failure looks like) before the MVP is even built.
3.  **Markdown Formatting Service:** We will construct a dedicated Markdown formatting service (`FileService` extension). This service will translate the raw `AgentPromptSpec` and `ExperimentPlan` Pydantic objects into beautifully formatted, perfectly structured Markdown documents (`MVP_PROMPT_SPEC.md`, `EXPERIMENT_PLAN.md`) ready for ingestion by tools like Cursor.
4.  **Pyxel UI Gamification:** We will deeply integrate the Pyxel UI modifications. We will implement the visual "Approval Stamp" (Hanko) animation and the corresponding retro sound effects. This animation logic must be triggered asynchronously via specific callbacks when each LangGraph HITL gate is successfully passed.
5.  **PDF Pipeline:** We will implement the PDF generation pipeline (`pdf_service.py`). This service will convert the intermediate Pydantic canvases into highly visual, structured, human-readable PDFs for the user to comfortably review during the paused HITL states.

### Cycle 6: Final Refinement, Observability, and UAT

**Objective:** The final cycle is dedicated entirely to polishing the system, ensuring absolute compliance with all architectural constraints, proving the system's stability, and validating the end-to-end user experience through automated tutorials.

**Tasks:**
1.  **Node Executor Audit:** We will conduct a comprehensive, line-by-line review of all LangGraph nodes in `nodes.py`. We must explicitly ensure that all core logic is safely wrapped using the `NodeExecutor.execute()` pattern. This guarantees consistent error boundaries and logging when returning node implementations dynamically via factories.
2.  **Closure Bug Prevention:** We will systematically verify that all dynamically created functions (especially those within the simulation loop) utilize `functools.partial` to bind variables. This is critical to prevent dangerous late-binding closure bugs that plague complex Python iterators.
3.  **Security and File Audit:** We will strictly audit the `FileService` usage to confirm all Markdown and PDF outputs utilize secure, atomic filesystem writes. We will verify that no un-sanitized data flows from the LLM directly to the filesystem.
4.  **UAT Marimo Execution:** We will execute the comprehensive User Acceptance Test (UAT) suite utilizing the interactive Marimo notebook (`tutorials/UAT_AND_TUTORIAL.py`). We will ensure both "Mock Mode" and "Real Mode" operate flawlessly without throwing a single unhandled exception.
5.  **Proof of Work Generation:** Finally, we will generate the definitive test execution log (`dev_documents/test_execution_log.txt`) as undeniable Proof of Work. We will execute `pytest` (with coverage mapping), `ruff check .`, and `mypy .`, demanding a 100% success rate across all linters and type checkers before final submission.

## 6. Test Strategy

The testing strategy is paramount to the success of the JTC 2.0 Remastered Edition. It prioritizes absolute strictness, complete isolation, and totally side-effect-free execution. We must ensure the massive LangGraph structure can be validated thoroughly without incurring hundreds of dollars in API costs or corrupting local filesystems.

### Cycle 1: Domain Models Testing

**Strategy:** The strategy for Cycle 1 is pure unit testing focused entirely and relentlessly on Pydantic schema validation. We will not test functionality; we will test structural integrity.
**Execution:** Tests will instantiate all new canvas models using both valid and intentionally, maliciously invalid data sets. We will explicitly test every single boundary condition (e.g., lists exceeding maximum lengths, string regex constraints). Critically, we will assert that passing extraneous fields raises a severe `pydantic.ValidationError` due to the `extra="forbid"` configuration. We will specifically utilize the pattern `<ModelClass>.model_validate({"field": valid_value, "extra_field": "bad"})` instead of passing `**{"extra_field": "bad"}` to explicitly prevent strict MyPy `[call-arg]` errors during the test suite execution. Absolutely no external APIs or file I/O operations are permitted in this cycle's tests.

### Cycle 2: CPF Pipeline Integration

**Strategy:** The strategy involves highly isolated node testing utilizing deeply mocked dependencies. We must prove the mathematical flow of data without relying on the stochastic nature of the LLM.
**Execution:** We will heavily rely on `unittest.mock.patch`. Crucially, we will explicitly patch the specific module factory import path (`src.core.llm.LLMFactory.get_llm`) rather than modifying a global instance. We will inject pre-written, perfectly formed JSON strings that exactly match the expected Pydantic schemas. The test suite will execute the `ideator_node`, `persona_node`, and `vpc_node` sequentially in total isolation. We will verify that the output of one node is correctly parsed, appended to the `GlobalState`, and correctly ingested as context by the subsequent node. We will also inject malformed JSON to ensure the validation logic correctly catches and handles the errors.

### Cycle 3: PSF Mapping and Graph Flow

**Strategy:** This cycle focuses on state reducer logic and complex LangGraph transition testing. We must ensure the graph routes data correctly based on variable inputs.
**Execution:** We will test the LangGraph state transitions directly. By mocking the LLM responses to simulate entirely different HITL feedback inputs (e.g., an approval versus a rejection with correction instructions), we will verify that the graph routes to the correct subsequent nodes. We will strictly utilize temporary directories (`tempfile.TemporaryDirectory`) to safely test the intermediate output of the textual wireframes. This ensures absolutely no permanent files or artifacts are written to the developer's local machine during the execution of the test suite.

### Cycle 4: Multi-Agent Simulation Validation

**Strategy:** The testing strategy for the simulation revolves entirely around testing the circuit breakers, token limits, and verifying the accuracy of dynamic agent prompt injection.
**Execution:** We will intentionally mock the LLM to return highly specific phrase patterns (e.g., "I vehemently disagree") repeatedly. This is designed to deliberately trigger the infinite loop detection circuit breakers. We will assert that the simulation safely aborts, logs the event correctly, and raises the appropriate custom `SimulationDeadlockException`. Furthermore, we will deeply inspect the `call_args` of the mocked LLM calls to mathematically guarantee that the Virtual Customer agent correctly received the entirety of the previously generated `MentalModelDiagram` embedded deep within its system prompt.

### Cycle 5: Output Generation and File I/O

**Strategy:** This cycle mandates rigorous, concurrent testing of the `FileService` and all Markdown formatting and rendering logic. We must prove the file writes are bulletproof.
**Execution:** We will utilize temporary files and `unittest.mock` combined with `ThreadPoolExecutor` to intentionally simulate highly concurrent write attempts to the same `MVP_PROMPT_SPEC.md` file. We will assert that the `FileService` successfully utilizes cross-platform file locking (e.g., `fcntl.flock` with `OSError` fallbacks for Windows environments) to prevent partial writes. The Markdown formatting logic will be unit-tested to ensure it correctly and mercilessly sanitizes any potentially malicious HTML characters generated by the LLM using `bleach.clean` to prevent Markdown injection attacks on the final document viewers.

### Cycle 6: End-to-End System UAT

**Strategy:** The final strategy encompasses executable tutorials and full pipeline simulation to prove the system works as a cohesive whole from the user's perspective.
**Execution:** The primary testing artifact will be the execution of the Marimo notebook (`tutorials/UAT_AND_TUTORIAL.py`). This notebook will be executed in a dedicated "Mock Mode" where a specialized, highly robust mock LLM class returns pre-defined, successful schema responses for the entirety of the 14-step workflow. The test will verify that the massive graph runs from start to finish without a single human intervention, that all strictly required Pydantic models are completely populated in the final `GlobalState`, and that the final `MVP_PROMPT_SPEC.md` and `EXPERIMENT_PLAN.md` specification files exist perfectly formed in the designated output directory. This confirms the system operates seamlessly and beautifully as a single, cohesive unit.
