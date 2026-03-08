# User Test Scenario & Tutorial Plan

## 1. Test Scenarios

These scenarios represent the core workflows that must be rigorously verified for the new Remastered system to be considered successful. They are derived from the "Fitness Journey" defined in the main specification document and prioritize the validation of the new schema-driven architecture.

### Scenario ID: UAT-001 - The Complete End-to-End "Fitness Journey" (Priority: Critical)

**Description:**
This is the primary happy-path scenario representing a complete, flawless execution of the Remastered system. The user initiates the session via the CLI, inputting a raw business idea (e.g., "AI for Agriculture"). The system must successfully guide them through all six phases of the new architecture without raising any validation errors or infinite loops.

Crucially, the user will experience the new Human-in-the-Loop (HITL) gates. At Gate 1.5, the system must pause and display the generated Pydantic models (the `ValuePropositionCanvas` and `AlternativeAnalysis`) via terminal output and trigger the generation of a PDF document to the local `/outputs/` directory. Simultaneously, the gamified Pyxel "Approval Stamp" animation must trigger to signal the successful validation of the Customer/Problem Fit. The user will provide a simple "Proceed" command.

At Gate 1.8, the system will present the `MentalModelDiagram` and `CustomerJourney`. The user will again provide steering feedback, verifying that the `worst_pain_phase` was correctly identified. The scenario concludes successfully when the system navigates through the JTC Board and 3H Reviews, ultimately outputting the final `AgentPromptSpec.md` and `ExperimentPlan.md` files to the local disk.

**Why it matters (Aha! Moment):**
The user realises the magic when, instead of just receiving a generic URL for a basic UI, they see a highly structured, mathematically linked chain of logic—from a deep psychological "Mental Model Diagram" all the way to a precise "Sitemap & User Story." The moment the final `AgentPromptSpec.md` is generated and saved, the user understands they now hold a perfect blueprint that can be pasted into Cursor or Windsurf to build exactly what the customer needs without any AI hallucinations.

### Scenario ID: UAT-002 - The Harsh Pivot at the Virtual Market (Priority: High)

**Description:**
This scenario tests the system's ability to ruthlessly kill bad ideas before engineering resources are wasted, demonstrating the value of the rigorous multi-agent validation step. The user will input a fundamentally flawed business idea with high friction (e.g., "A complex Web3 social network for dogs").

The system will proceed normally through the initial ideation and canvas generation phases, constructing the necessary `CustomerProfile` and `ValueMap`. However, when it reaches Phase 4 (Virtual Solution Interview), the Virtual Customer Agent—strictly adhering to their generated `MentalModelDiagram` and `AlternativeAnalysis` schemas—must heavily criticize the proposed Sitemap and User Story. The agent's output must explicitly point out that the `switching_cost` from existing alternatives is too high and the perceived `10x_value` is non-existent.

The user will then be prompted at HITL Gate 2 to make a "Pivot or Persevere" decision based on this harsh feedback. The user will choose to "Pivot". The system must then successfully halt the current trajectory, discard the flawed `SitemapAndStory`, and either terminate the run gracefully or prompt the user for a new foundational idea, demonstrating the system's value in preventing wasted effort.

**Why it matters (Aha! Moment):**
The user feels the true value of the platform when an AI persona, perfectly acting out the defined customer pains and cognitive tasks, completely destroys their wireframe logic before a single line of code is written. It simulates the harsh reality of the market in a safe, de-identified environment, saving them months of development time.

### Scenario ID: UAT-003 - Transcript Ingestion and Fact-Checking (Priority: Medium)

**Description:**
This scenario rigorously validates the Retrieval-Augmented Generation (RAG) capabilities and ensures that the structured schemas are grounded in reality, not AI guesses. The user will start the session by providing a `--ingest` flag pointing to a mock interview transcript file (e.g., a PLAUD audio transcription of a farmer complaining extensively about supply chain logistics and rotting produce).

During the workflow execution, specifically at the `transcript_ingestion_node` and the subsequent CPO mentoring phase, the system must utilize LlamaIndex to retrieve relevant chunks of the ingested transcript. The CPO Agent must intervene using "The Mom Test" principles. Critically, the CPO's output must explicitly reference quotes or specific data points from the ingested transcript to either validate or invalidate the assumptions made in the `ValuePropositionCanvas`. If the VPC claims the pain is "cost of seeds," but the transcript emphasizes "supply chain," the CPO must forcefully correct the state.

**Why it matters (Aha! Moment):**
The user sees the AI directly quoting real people ("As John said in the transcript on Tuesday..."). The abstract business frameworks suddenly become grounded in undeniable, real-world evidence. The user realizes the AI is no longer hallucinating features but is actively connecting raw customer data to concrete product specifications.

---

## 2. Behavior Definitions (Gherkin-style)

These definitions form the basis for automated and manual testing of the new architectural components. They define the precise expected state transitions within the `GlobalState` Pydantic model. Because this architecture mandates strict validation across a complex, multi-stage LangGraph workflow, these definitions comprehensively cover every major operational boundary, data transformation, and user interaction point. The implementation of these specifications ensures that no hallucinations propagate through the pipeline.

**Feature: Phase 1 Ideation and Initialization**
```gherkin
GIVEN the user launches the application with a specific raw topic (e.g., "Automated Drone Delivery")
WHEN the system triggers the `ideator_node` to search for market trends
THEN the AI must return exactly 10 distinct `LeanCanvas` models
AND the system must populate the `GlobalState.generated_ideas` with a `LazyIdeaIterator` containing these ideas
AND the execution must interrupt at HITL Gate 1 to await the user's explicit selection of "Plan A"
```

**Feature: Phase 2 Persona and Empathy Map Generation**
```gherkin
GIVEN the user has successfully selected a `LeanCanvas` idea at Gate 1
WHEN the LangGraph transitions into the `persona_node`
THEN the agent must consume the `LeanCanvas` data from `GlobalState`
AND it must output a structured JSON conforming perfectly to the `Persona` Pydantic schema
AND the system must save this newly generated object directly into `GlobalState.target_persona` without raising any validation errors
```

**Feature: Phase 2 Alternative Analysis Calculation**
```gherkin
GIVEN the system holds a valid `target_persona` within its state
WHEN the system subsequently executes the `alternative_analysis_node`
THEN the agent must identify at least one pre-existing competitor or legacy methodology
AND it must return a valid `AlternativeAnalysis` object that explicitly quantifies the `switching_cost` and asserts a `ten_x_value` proposition
AND the `GlobalState.alternative_analysis` field must be updated accordingly
```

**Feature: Phase 2 Schema-Driven Value Proposition Validation**
```gherkin
GIVEN the system has successfully generated both the `target_persona` and the `AlternativeAnalysis`
WHEN the system executes the critical `vpc_node` (Value Proposition Canvas)
THEN the AI must synthesize previous findings and return a response strictly conforming to the `ValuePropositionCanvas` Pydantic schema
AND the response must not contain any undocumented fields outside of the explicit schema definition (enforced by `extra="forbid"`)
AND the resulting `ValueMap.pain_relievers` array must logically align with the `CustomerProfile.pains` array, as confirmed by the `fit_evaluation` string
AND the system must save this final object successfully to the `GlobalState.value_proposition` property
AND the LangGraph execution must pause immediately at HITL Gate 1.5
```

**Feature: Phase 2 Human-in-the-Loop (HITL) Review and Pyxel Gamification**
```gherkin
GIVEN the system has paused execution at HITL Gate 1.5 (Customer/Problem Fit Review)
AND the complete `ValuePropositionCanvas` resides safely within the current state checkpoint
WHEN the user provides a "Proceed" or affirmative approval input via the provided terminal prompt or UI widget
THEN the external Pyxel rendering engine must instantly trigger the specific "Approval Stamp" (赤いハンコ) visual animation
AND the backend system must concurrently invoke the `pdf_generator` service
AND the system must successfully format and write a visual PDF representation of the canvas into the local `/outputs/canvas/` directory
AND the system must automatically resume the LangGraph execution and transition to the subsequent `transcript_ingestion_node`
```

**Feature: Phase 3 Contextual Inheritance and Mental Model Mapping**
```gherkin
GIVEN the system is currently executing the `mental_model_journey_node`
AND the `GlobalState` contains valid, fully populated `target_persona`, `alternative_analysis`, and `value_proposition` models
WHEN the agent attempts to generate the `MentalModelDiagram` and the `CustomerJourney` objects
THEN the internal LangChain prompt template must explicitly embed stringified representations of the prerequisite data
AND the resulting `CustomerJourney` list of `JourneyPhase` objects must be strictly chronologically ordered without logic gaps
AND the `CustomerJourney` model must algorithmically identify exactly one valid `worst_pain_phase` that matches an existing, defined phase name within the journey list
```

**Feature: Phase 3 Sitemap and Story Constraint Enforcement**
```gherkin
GIVEN the `CustomerJourney` has successfully isolated the `worst_pain_phase`
WHEN the system transitions to the `sitemap_wireframe_node`
THEN the AI must formulate a `SitemapAndStory` object that is narrowly focused
AND the `core_story.target_route` must logically resolve the specific frustrations outlined in the `worst_pain_phase`
AND any generated routes that do not directly address the validated core problem must be discarded by the AI's internal subtractive reasoning
AND the graph must pause at HITL Gate 1.8 to await final Problem/Solution Fit confirmation
```

**Feature: Phase 4 Multi-Agent Adversarial Review (3H Node)**
```gherkin
GIVEN the user has authorized the system to proceed past Gate 2 (Virtual Customer Interview)
WHEN the system executes the parallel or sequential `3h_review_node`
THEN the Hacker agent must review the `SitemapAndStory` specifically for technical feasibility
AND the Hipster agent must review the exact same object strictly for UX friction against the `MentalModelDiagram`
AND the Hustler agent must review the unit economics against the `AlternativeAnalysis`
AND all three independent critiques must be successfully appended as `DialogueMessage` objects to the `GlobalState.debate_history` array
AND the system's internal circuit breakers must ensure that this debate does not exceed the predefined `max_turns` limit
```

**Feature: Phase 5 Final Specification Serialization and Output**
```gherkin
GIVEN the system has completed the exhaustive 3H Review and the JTC Board simulation
AND the `GlobalState` holds a massive context containing all validated canvases, journeys, and debate histories
WHEN the ultimate `spec_generation_node` is executed
THEN the system must aggregate all previous schemas into a unified, coherent context window
AND the system must utilize this context to instantiate the final `AgentPromptSpec` and `ExperimentPlan` Pydantic models
AND the system must serialize these models and write an `AgentPromptSpec.md` file to the local disk without any file permission errors
AND the generated markdown file must contain a syntactically valid Mermaid `stateDiagram-v2` definition block
AND the final document must absolutely not contain any hallucinated frontend UI components or backend features that do not directly and measurably address the previously established `worst_pain_phase`
```

---

## 3. Tutorial Strategy

To ensure reproducibility, maintainability, and ease of verification for the Auditor agent and end-users, the User Acceptance Testing and onboarding tutorials will be completely consolidated into a single, interactive environment.

### Strategy: "Mock Mode" vs "Real Mode"
- **Mock Mode (CI/No-API-Key Execution):** For automated CI runs and rapid architectural validation by developers, the tutorial will implement a rigorous `Mock Mode`. This mode will utilize Python's `unittest.mock` library to completely patch all external network calls (OpenAI chat completions, Tavily search, LlamaIndex embeddings). It will inject predefined, valid JSON strings that perfectly match the new Pydantic schemas (like `ValuePropositionCanvas` and `MentalModelDiagram`). This allows the LangGraph state machine to execute from start to finish in a matter of seconds, validating the graph edges, schema validation logic, and file I/O operations without requiring API keys or incurring LLM API costs.
- **Real Mode:** When valid environment variables (`OPENAI_API_KEY`, etc.) are detected on the host machine, the tutorial will bypass the mocks and execute actual LLM calls. This provides the genuine, unpredictable, and highly valuable simulation experience for actual business validation.

---

## 4. Tutorial Plan

We will create a **SINGLE** Marimo notebook file to serve as the unified testing, demonstration, and tutorial environment. Consolidating the tests into one file drastically reduces maintenance overhead and provides a linear, cohesive learning experience.

**Target File:** `tutorials/UAT_AND_TUTORIAL.py`

This Marimo notebook will contain the following specific cell structure:
1.  **Environment Check & Setup Cell:** Automatically detects if API keys are present in the environment or `.env` file to dynamically toggle between Mock Mode and Real Mode. It initializes the LangGraph application.
2.  **Introduction Cell:** Explains the "Fitness Journey" concept, the importance of schema-driven generation, and what the user is about to experience in the simulation.
3.  **Scenario Execution Cells:**
    -   A dedicated execution cell to run **UAT-001** (The Happy Path). This cell will programmatically simulate user inputs at the HITL gates and display the generated Pydantic models (like the VPC) directly in the notebook UI using `mo.md()`.
    -   A dedicated execution cell to run **UAT-002** (The Harsh Pivot). This cell will demonstrate the Virtual Customer's rejection logic and verify that the graph handles the pivot state correctly.
    -   A dedicated execution cell to run **UAT-003** (Transcript Ingestion). This cell will load a dummy text file, execute the RAG ingestion node, and display the CPO's fact-checked output.
4.  **Output Verification Cell:** A final, automated cell that inspects the local file system to confirm that `AgentPromptSpec.md`, `ExperimentPlan.md`, and the Canvas PDFs were successfully generated, structurally valid, and written to disk without permission errors.

## 5. Tutorial Validation

To validate that the tutorial executes correctly and the architecture is sound, the following strict criteria must be met:
1.  Executing `uv run marimo edit tutorials/UAT_AND_TUTORIAL.py` (or running it headlessly via `python`) in an environment absolutely devoid of `.env` API keys must automatically default to Mock Mode. It must complete the entire graph execution successfully without raising any `ValidationError`, exceptions, or network timeout errors.
2.  The final Output Verification cell must assert "PASS" by successfully finding the expected output files (`AgentPromptSpec.md`, etc.) in the designated local output directories, and it must verify that the content of these files is not empty.
3.  The Pyxel simulation loop (if invoked in the test environment) must utilize a headless renderer or appropriate thread management to ensure it does not block the main LangGraph execution thread indefinitely, allowing the automated test to finish gracefully.