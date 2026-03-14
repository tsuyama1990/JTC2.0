# User Test Scenario & Tutorial Plan

## Aha! Moment
The "Magic Moment" occurs when the user, after navigating the grueling gauntlet of the JTC 2.0 simulation, receives their final output. Instead of a fragile, hardcoded UI snippet, they witness the system instantly generate a flawless, universally compatible `AgentPromptSpec.md` and a rigorously reasoned `ExperimentPlan.md`. They realize that their nebulous idea has been systematically validated, stripped of hallucinated features, and perfectly structured. When they copy this spec into Cursor or Windsurf and see an immaculate React application build itself in seconds—exactly aligned with a validated customer pain point—they understand the true power of the "Fitness Journey Workflow".

## Prerequisites
Before executing these test scenarios and tutorials, the user must ensure their environment is properly configured:
- **Python 3.12+** installed on the host machine.
- **uv** package manager installed (`pip install uv`).
- **Dependencies** installed via `uv sync`.
- **API Keys** correctly configured in the `.env` file:
    - `OPENAI_API_KEY` (Required for full simulation)
    - `TAVILY_API_KEY` (Required for Phase 1 Ideation)
- **marimo** notebook environment installed (included in dev dependencies).

## Success Criteria
The tutorial is deemed successful if:
1. The user can execute both the Mock Mode and Real Mode scenarios from start to finish within the `marimo` interface.
2. The Pyxel UI renders correctly and displays the "Approval" stamp animations at the designated Human-in-the-Loop (HITL) gates.
3. The final `AgentPromptSpec.md` and `ExperimentPlan.md` files are successfully generated in the local directory without errors.
4. The user understands the "Chain of Thought" progression and how each phase builds upon the previous one.

---

## 1. Tutorial Strategy

To transform these user test scenarios into an engaging, educational experience, we will eschew traditional, static CLI scripts. Instead, we will leverage **Marimo**, a reactive Python notebook environment. This strategy provides several critical advantages for User Acceptance Testing (UAT) and tutorials:

1. **Interactive Execution:** Users can run the LangGraph phases step-by-step, observing the state changes in real-time within the notebook cells, rather than watching a monolithic terminal log scroll by.
2. **Visual Data Inspection:** The complex Pydantic models (like `ValuePropositionCanvas` and `MentalModelDiagram`) can be elegantly rendered and inspected directly within the notebook interface, making the "Chain of Thought" visually apparent.
3. **Dual Execution Modes:** The tutorial will explicitly support two modes:
    - **Mock Mode (CI/Safe Mode):** By setting `os.environ["MOCK_MODE"] = "true"`, the tutorial will execute using pre-defined, deterministic local fixtures. This allows users (and automated CI pipelines) to verify the workflow logic, state transitions, and UI animations instantly, without requiring active API keys or incurring token costs.
    - **Real Mode (Live API):** For users ready to simulate a genuine idea, the tutorial will connect to the live OpenAI and Tavily APIs, demonstrating the system's full generative capabilities.
4. **Unified Entry Point:** To ensure simplicity and reproducibility, we will avoid fragmenting the tutorial across multiple files. The entire UAT and tutorial experience will be consolidated into a **SINGLE** executable Marimo file: `tutorials/UAT_AND_TUTORIAL.py`.

---

## 2. Test Scenarios

These scenarios are designed to validate the core use-cases defined in the `ALL_SPEC.md` while simultaneously serving as the primary tutorial path for new users.

### Scenario ID: UAT-001 - The Mock Mode "Happy Path" (Priority: High)
**Objective:** Verify that the entire 14-step LangGraph workflow can execute flawlessly from start to finish in Mock Mode, correctly updating the `GlobalState` and triggering UI elements, without relying on external APIs.

**Detailed Description:**
This scenario serves as the baseline health check for the JTC 2.0 system and the gentle "Quick Start" for new users. The user will launch the Marimo notebook and select "Mock Mode". The system will immediately bypass the initial `ideator_node` network call and load a pre-configured `LeanCanvas` representing a mock idea (e.g., "AI for Agriculture").

The user will then step through the subsequent phases using the notebook controls. The critical verification points occur at the Human-in-the-Loop (HITL) gates. At Gate 1.5 (CPF Feedback), the user must observe that the system has successfully generated the `Persona`, `ValuePropositionCanvas`, and `AlternativeAnalysis` mock objects, and that the Pyxel UI (running asynchronously) correctly flashes the "Approval" stamp animation. The user will provide a mock feedback string to resume execution.

This process repeats through Phase 3 (Gate 1.8), where the `MentalModelDiagram` and `SitemapAndStory` are validated. In Phase 4, the user will observe the simulated, deterministic debate between the 3H Reviewers and the JTC Board. Finally, the user must verify that Phase 5 successfully generates the `AgentPromptSpec.md` and `ExperimentPlan.md` files in the local `outputs/` directory, confirming the end-to-end integrity of the mocked workflow. This scenario proves the system is fundamentally sound and ready for live usage.

### Scenario ID: UAT-002 - Real Idea Validation with RAG Ingestion (Priority: High)
**Objective:** Verify the system's ability to ingest real-world transcript data, execute live API calls, and utilize the RAG pipeline to influence the CPO and Virtual Customer agents.

**Detailed Description:**
This advanced scenario tests the system's true generative capabilities. The user will ensure valid API keys are configured and launch the notebook in "Real Mode". The first action is crucial: the user will execute a cell that invokes the `main.py --ingest ./sample_data/interview.txt` command programmatically. The user must verify that the LlamaIndex vector store is successfully created and populated without raising path traversal or memory errors.

Next, the user initiates the LangGraph execution with a custom topic (e.g., "SaaS for independent plumbers"). The system must successfully query the Tavily API and generate 10 unique `LeanCanvas` drafts. The user interacts with HITL Gate 1 to select "Plan A".

As the execution proceeds into Phase 2, the critical test occurs. The CPO agent must demonstrably reference the ingested `interview.txt` data when providing feedback on the generated `ValuePropositionCanvas`. The user must inspect the `GlobalState` to confirm the LLM correctly parsed the Pydantic schemas over the live network connection. The user will navigate the remaining HITL gates, providing genuine feedback to pivot or refine the idea based on the live AI responses. The scenario concludes when the final Markdown artifacts are generated, proving the system can handle dynamic, real-world execution.

### Scenario ID: UAT-003 - Circuit Breaker and Error Recovery (Priority: Medium)
**Objective:** Verify that the system handles multi-agent debate deadlocks and LLM schema validation failures gracefully, without crashing.

**Detailed Description:**
This scenario stresses the system's resilience. Operating in Mock Mode, the user will load a specific fixture designed to simulate a catastrophic failure. First, a fixture will inject an invalid JSON payload (missing a required field in the `MentalModelDiagram`) to simulate an LLM hallucination during Phase 3. The user must observe the notebook logs to verify that the `tenacity` retry logic engages, catches the `ValidationError`, and successfully attempts to recover the state.

Next, the user triggers the Phase 4 Validation. The system will be fed a specialized mock script that forces the Hacker and Hustler agents into an infinite loop of contradictory feedback. The user must monitor the execution and verify that the system's semantic moderator logic correctly identifies the deadlock and triggers the circuit breaker. The test passes if the system forces a termination of the debate and gracefully advances the graph to the next node (or raises a caught, handled exception), preventing an infinite loop and proving the system is safe for autonomous, unattended execution.

---

## 3. Behavior Definitions (Gherkin)

These definitions form the basis for automated integration tests and clarify the exact expected behavior of the UAT scenarios.

### Behavior: Seamless Execution in Mock Mode
**GIVEN** the environment variable `MOCK_MODE` is set to "true"
**AND** valid mock fixtures exist in the `tests/fixtures/` directory
**WHEN** the user initiates the LangGraph execution via the Marimo notebook
**THEN** the system must bypass all external network requests to OpenAI and Tavily
**AND** the `GlobalState` must be populated sequentially with the deterministic mock data
**AND** the system must pause exactly three times at the defined HITL Gates (1.5, 1.8, and 3)
**AND** the final Markdown artifacts must be successfully generated in the output directory.

### Behavior: Contextual RAG Integration
**GIVEN** a valid customer interview transcript `interview.txt` exists
**AND** the system is running in Real Mode
**WHEN** the user executes the ingestion command
**AND** the system reaches the `transcript_ingestion_node` in Phase 2
**THEN** the CPO agent must query the vector store
**AND** the CPO agent's output must demonstrably include factual references found within the `interview.txt` file
**AND** the CPO agent must flag any assumptions in the `ValuePropositionCanvas` that contradict the ingested data.

### Behavior: Circuit Breaker Activation
**GIVEN** the system is executing the `3h_review_node` in Phase 4
**AND** the simulated Hacker and Hustler agents fail to reach a consensus
**WHEN** the number of conversational turns exceeds the `max_turns` limit defined in `SimulationConfig`
**THEN** the semantic moderator must intervene
**AND** the debate loop must be forcibly terminated
**AND** the system must log a circuit breaker warning
**AND** the LangGraph execution must safely proceed to the next node without crashing the host application.

---

## 4. Tutorial Plan

The entire tutorial experience will be centralized.

1. **File Creation:** We will create exactly one file: `tutorials/UAT_AND_TUTORIAL.py`.
2. **Framework:** This file will be a valid Marimo notebook script.
3. **Structure:** The notebook will be divided into the following sections:
    - **Introduction:** Explaining the JTC 2.0 concept and the "Chain of Thought".
    - **Configuration:** Interactive cells to set API keys or toggle `MOCK_MODE`.
    - **Data Ingestion (Optional):** A cell to test the RAG pipeline.
    - **The Fitness Journey:** Step-by-step cells that execute the LangGraph phases, pausing at HITL gates, and rendering the current `GlobalState` Pydantic models visually.
    - **Artifact Generation:** The final step, displaying the generated Markdown specs directly in the notebook interface.

## 5. Tutorial Validation

To ensure the tutorial is always functional:
- A CI pipeline job will be configured to execute `uv run pytest`.
- A specific E2E test will be written to programmatically run the UAT scenarios defined in the UAT document via a headless script ensuring that the core logic works without manual intervention.