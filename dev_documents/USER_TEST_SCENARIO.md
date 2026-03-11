# User Test Scenario & Tutorial Plan

## 1. Test Scenarios

### Scenario ID: TS-001 - The Core Pathfinder
**Priority:** High
**Description:** This scenario aims to validate the absolute "happy path" of the system, verifying that a user can input a simple idea and successfully traverse the 14-step workflow, resulting in the generation of the `AgentPromptSpec.md` and `EXPERIMENT_PLAN.md`.
**Aha! Moment:** The user inputs a simple seed topic (e.g., "AI for remote team building") and after a few simulated AI debates, sees a perfectly formatted, 5-page PDF of a Value Proposition Canvas and a complete MarkDown specification ready for a coding agent, experiencing the transition from a vague idea to a structured requirement in minutes.
**Details:** The test begins with the Ideation Phase, where 10 Lean Canvases are generated. The user selects 'Plan A'. The system must then seamlessly transition into generating the Persona and Empathy Map. At the HITL Gate 1.5, the user will interact with the system by providing minor feedback (e.g., "Focus more on introverts"). The system must acknowledge this, generate the updated Value Proposition Canvas, and proceed to the Problem/Solution Fit phase. The simulation of the Virtual Customer and the 3H Review must execute without deadlocks. The final outputs must accurately reflect the user's initial input and subsequent feedback. The Pyxel UI must display the expected "Approval" stamps at the designated milestones. The entire process should complete in under 10 minutes, demonstrating the speed and rigour of the methodology. This process is vital to ensuring that the user experience is smooth, efficient, and ultimately successful in guiding them toward a robust business model definition. By thoroughly validating these interactions, we guarantee that the software operates without glitches or delays, providing an optimal environment for enterprise intrapreneurs to test their ideas. We must also verify that the transition between phases is completely seamless. Additionally, the system must properly log all state changes during this happy path to ensure complete traceability. We expect the AI to respond promptly without excessive latency. It is critical that the frontend updates consistently and without lag. The approval stamp should appear with the correct animation and sound effect every time. All PDF generation must happen in the background without blocking the main UI thread. Any feedback provided by the user must be correctly parsed and immediately integrated into the next phase of the process. This meticulous attention to detail during the happy path is what will ultimately drive user adoption and trust in the system.

### Scenario ID: TS-002 - The RAG Reality Check
**Priority:** High
**Description:** This scenario specifically tests the Retrieval-Augmented Generation (RAG) capabilities, ensuring the CPO agent effectively utilizes ingested transcripts to challenge the user's assumptions.
**Aha! Moment:** The user attempts to push a feature that contradicts real customer feedback. The CPO agent intervenes, citing specific sentences from the ingested interview transcript, and forces the user to pivot the Value Proposition Canvas. The user realizes the system is acting as a true, data-driven mentor, not just a "Yes-Man" AI.
**Details:** The user will first use the `--ingest` command to load a provided sample transcript (`sample_interview.txt`). The system must vectorize this without memory leaks or path traversal vulnerabilities. Next, the user initiates a simulation with a topic directly related to the transcript. During Phase 2, the user intentionally provides a solution that is unsupported by the transcript data. The CPO agent must flag this during the Problem Interview RAG step (Step 5), quoting the specific text that contradicts the user. The test verifies that the system can properly parse, embed, and retrieve the context to perform a rigorous "Mom Test" validation. This specific verification is absolutely critical because it guarantees that our RAG implementation is robust and actually influences the decision-making process within the simulation. Without this, the system would simply be a generic brainstorming tool, lacking the empirical grounding required for true Startup Science methodology. We must rigorously test edge cases, such as when the transcript contains ambiguous language or conflicting statements, to ensure the CPO agent handles them gracefully. The vectorization process must be highly efficient, taking minimal time even for large transcripts. The retrieval mechanism must be highly accurate, pulling only the most relevant snippets to challenge the user. The agent's response must clearly articulate why the user's assumption is flawed based on the data. The UI must cleanly display the retrieved quote alongside the agent's feedback. This interaction is the core differentiator of our platform, providing unparalleled value to the user by preventing them from building products nobody wants. The system must also gracefully handle cases where the user tries to argue with the CPO agent, maintaining its data-driven stance. By validating this entire flow, we ensure the system delivers on its promise of rigorous, evidence-based innovation.

### Scenario ID: TS-003 - Mock Mode Execution
**Priority:** Medium
**Description:** This scenario validates the system's ability to run completely offline without actual API calls, essential for CI/CD pipelines and automated testing.
**Aha! Moment:** The developer sets `MOCK_MODE=true` and runs the entire suite instantly. The system gracefully returns mock objects and generated data, proving the architecture is perfectly decoupled from its external dependencies.
**Details:** The test sets the environment variable `MOCK_MODE=true`. It runs the full simulation workflow. The LLM and Tavily API calls must be completely bypassed. The system should return static, predefined Pydantic models for the Ideation, Persona, and Journey phases. The final PDF generation and Markdown generation must still execute, utilizing the mock data to generate the files. This ensures the structural integrity of the application can be verified continuously without incurring API costs. The ability to execute the entire simulation pipeline entirely offline is a fundamental requirement for maintaining a high-velocity development workflow and ensuring robust Continuous Integration. By extensively validating this Mock Mode, we guarantee that our development teams can rapidly iterate on the core business logic, LangGraph state transitions, and UI rendering without being bottlenecked by external API rate limits, network latency, or unpredictable API costs. We must verify that absolutely every single external call is intercepted and correctly mocked. The mock data provided must perfectly adhere to the strict Pydantic schemas, ensuring that the downstream nodes process the information exactly as they would in a live environment. The final generation of the PDF and Markdown artifacts must be indistinguishable from a live run, aside from the static content. This allows us to run comprehensive End-to-End tests on every single commit, catching regressions immediately. Furthermore, this mode is invaluable for onboarding new developers or demonstrating the system's capabilities in environments without internet access. The seamless toggle between real and mock execution is a testament to the system's cleanly decoupled architecture. By rigorously testing this scenario, we fortify the platform's reliability and developer experience, laying a solid foundation for long-term maintainability. The ability to execute the entire simulation pipeline entirely offline is a fundamental requirement for maintaining a high-velocity development workflow and ensuring robust Continuous Integration. By extensively validating this Mock Mode, we guarantee that our development teams can rapidly iterate on the core business logic, LangGraph state transitions, and UI rendering without being bottlenecked by external API rate limits, network latency, or unpredictable API costs. We must verify that absolutely every single external call is intercepted and correctly mocked. The mock data provided must perfectly adhere to the strict Pydantic schemas, ensuring that the downstream nodes process the information exactly as they would in a live environment. The final generation of the PDF and Markdown artifacts must be indistinguishable from a live run, aside from the static content. This allows us to run comprehensive End-to-End tests on every single commit, catching regressions immediately. Furthermore, this mode is invaluable for onboarding new developers or demonstrating the system's capabilities in environments without internet access. The seamless toggle between real and mock execution is a testament to the system's cleanly decoupled architecture. By rigorously testing this scenario, we fortify the platform's reliability and developer experience, laying a solid foundation for long-term maintainability.

## 2. Behavior Definitions

The following Gherkin-style definitions formalize the expected system behaviors for the test scenarios outlined above.

### Feature: Additive Workflow Execution
**GIVEN** the user has launched the application with a valid API key and no previous state
**WHEN** the user inputs the topic "Automated gardening for urban apartments"
**THEN** the system should generate 10 unique Lean Canvas ideas
**AND** the Pyxel UI should prompt the user to select "Plan A"
**WHEN** the user selects an idea
**THEN** the system must consecutively generate a Persona, an Empathy Map, and an Alternative Analysis
**AND** a `ValuePropositionCanvas` PDF must be generated in the `/outputs` directory
**AND** the Pyxel UI must display the "Approval" stamp animation
**AND** the system must wait for Human-in-the-Loop (HITL) feedback before proceeding.

### Feature: Strict Schema Enforcement
**GIVEN** the LangGraph orchestrator is currently executing Phase 3 (Mental Model & Journey Mapping)
**WHEN** the LLM generates a response that attempts to add an unmapped field to the `CustomerJourney` Pydantic model
**THEN** the Pydantic validator must raise a `ValidationError` due to `extra="forbid"`
**AND** the LangGraph node must catch the error, log it via LangSmith, and attempt a retry (up to the configured limit)
**AND** if the retry fails, the system must gracefully halt the execution and notify the user via the Pyxel UI without crashing the main application loop.

### Feature: RAG-Driven Validation
**GIVEN** the user has successfully ingested `interview_01.txt` containing the phrase "I hate subscription models"
**AND** the system is currently executing the `transcript_ingestion_node`
**WHEN** the user proposes a solution heavily reliant on a monthly subscription
**THEN** the CPO agent must query the LlamaIndex vectorized data
**AND** the CPO agent must output feedback explicitly citing the "I hate subscription models" constraint
**AND** the system must demand a revision of the `ValueMap` before proceeding to Phase 3.

### Feature: Mock Mode for CI/CD
**GIVEN** the environment variable `MOCK_MODE` is set to `true`
**WHEN** the user runs the `main.py` entry point
**THEN** the application must bypass all OpenAI client initialization routines
**AND** the system must utilize pre-configured mock Pydantic models for all agent responses
**AND** the system must complete the 14-step workflow, generating mock `AgentPromptSpec.md` and `EXPERIMENT_PLAN.md` files
**AND** the final execution log must state that the system ran successfully in Mock Mode. These specific Gherkin behaviors are absolutely crucial because they provide an unambiguous, executable contract between the requirements and the actual system implementation. By defining these scenarios using the Given-When-Then format, we ensure that both technical and non-technical stakeholders have a perfectly clear and shared understanding of exactly how the system must react under various precise conditions. This rigorous approach to behavioral specification eliminates any potential ambiguity or misinterpretation of the core requirements. Furthermore, these definitions serve as the exact blueprint for our automated End-to-End test suites. Every single step defined here must translate directly into a corresponding automated test assertion, guaranteeing that the software consistently meets its defined quality standards. This is particularly vital for validating complex, multi-stage processes like the LangGraph orchestrations and the intricate interactions with the LLM. It allows us to systematically verify the robust handling of edge cases, such as schema validation failures or unexpected inputs, ensuring the system remains stable and predictable. By strictly adhering to these meticulously crafted behavioral definitions, we build a platform that is not only highly functional but also deeply reliable, maintainable, and continuously verifiable throughout its entire lifecycle. This formalized specification acts as our ultimate source of truth, guiding every phase of development and testing to ensure absolute alignment with the overall project objectives. Furthermore, these behaviors must be continuously monitored and validated as the system evolves. They act as a regression suite, instantly highlighting any unintended side effects introduced by new features. This constant vigilance is necessary to maintain the high standard of quality required for enterprise software. The clarity provided by the Gherkin syntax empowers our QA teams to write precise, comprehensive test cases. It also allows product managers to quickly verify that their specific requirements have been implemented exactly as intended. By embedding these behavioral definitions deep within our development process, we create a culture of quality and accountability. Every engineer understands exactly what is expected of the code they write. The resulting system is robust, resilient, and perfectly tailored to the needs of the users. This dedication to behavioral specification is a cornerstone of our development philosophy, ensuring that we consistently deliver software that exceeds expectations and provides tangible business value.

## 3. Tutorial Strategy

The tutorial strategy aims to transform the rigorous test scenarios into an engaging, interactive learning experience for new users. Instead of providing disjointed CLI commands or separate test scripts, we will unify the entire User Acceptance Testing (UAT) and tutorial process into a single, executable Marimo notebook.

*   **Interactive Learning:** Marimo allows users to run Python code block by block while reading rich Markdown explanations. This provides immediate visual feedback.
*   **"Mock Mode" First:** The tutorial will begin by introducing "Mock Mode". This allows users to experience the entire workflow and see the final PDF/Markdown outputs instantly without needing API keys or incurring costs. This guarantees an initial "Aha! Moment" for every user, regardless of their setup.
*   **Gradual Complexity:** After the "Mock Mode" demonstration, the tutorial will guide the user on how to configure their `.env` file for "Real Mode" execution, slowly introducing the RAG ingestion capabilities and the Pyxel UI.
*   **Artifact Focus:** The tutorial will heavily emphasize the generated artifacts (`AgentPromptSpec.md`, `EXPERIMENT_PLAN.md`, and the PDF canvases), explaining *why* they are structured the way they are and how they prevent AI hallucinations when used with external coding agents.

## 4. Tutorial Plan

To execute the tutorial strategy, we will create a **SINGLE** Marimo Text/Python file named `tutorials/UAT_AND_TUTORIAL.py`.

This file will contain the following structured sections:

1.  **Welcome to JTC 2.0 (Remastered):** A brief introduction to the Startup Science methodology and the goals of the platform.
2.  **Environment Setup:** Instructions and code blocks for verifying the Python version (`3.12+`) and the presence of necessary dependencies (`uv`).
3.  **Scenario 1: The Fast-Track (Mock Mode Execution):**
    *   Explanation of Mock Mode.
    *   Code block: Setting `os.environ['MOCK_MODE'] = 'true'`.
    *   Code block: Initializing the `SimulationGraph` and running a complete end-to-end mock simulation for the topic "AI for remote team building".
    *   Code block: Displaying the generated `AgentPromptSpec.md` and `EXPERIMENT_PLAN.md` files directly within the Marimo notebook output for the user to read.
4.  **Scenario 2: The Real Deal (Connecting to the APIs):**
    *   Instructions for setting up the `.env` file with `OPENAI_API_KEY` and `TAVILY_API_KEY`.
    *   Code block: Disabling Mock Mode.
    *   Code block: Running Phase 1 (Ideation) and stopping at HITL Gate 1.
    *   Interactive element: Allowing the user to modify the state (select a plan) before continuing.
5.  **Scenario 3: Grounding in Reality (RAG Demonstration):**
    *   Explanation of the CPO agent and the Mom Test.
    *   Code block: Creating a dummy text file (`sample_interview.txt`).
    *   Code block: Running the `transcript_service.py` to ingest the file.
    *   Code block: Executing the Phase 2 RAG verification node to show how the CPO agent utilizes the ingested text.
6.  **Reviewing the Outputs:** A final section detailing where the high-resolution PDFs are saved (`/outputs/canvas/`) and how to use the generated `AgentPromptSpec.md` with tools like Cursor or Windsurf.

## 5. Tutorial Validation

The `tutorials/UAT_AND_TUTORIAL.py` Marimo notebook must be strictly validated to ensure reproducibility.

1.  **Headless Execution:** During the CI/CD pipeline, a script will run the Marimo notebook headlessly (`marimo export html tutorials/UAT_AND_TUTORIAL.py` or a dedicated test script).
2.  **Zero Error Tolerance:** The headless execution must complete without raising any Python exceptions.
3.  **Output Verification:** The test runner must assert that after the notebook execution, the expected mock files (`AgentPromptSpec.md` and `EXPERIMENT_PLAN.md`) have been successfully created in the designated temporary output directories.
4.  **Proof of Work:** As part of the final implementation cycle (Cycle 06), a test execution log capturing the successful headless execution of the Marimo UAT notebook will be generated and saved to `dev_documents/test_execution_log.txt`.
