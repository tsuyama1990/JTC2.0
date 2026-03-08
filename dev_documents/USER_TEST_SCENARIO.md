# User Test Scenario & Tutorial Plan

## 1. Aha! Moment
The "Magic Moment" occurs when the user, after navigating a challenging series of retro 16-colour RPG-style "boss fights" (internal JTC approval meetings and harsh customer feedback), finally receives the "Approval" stamp animation accompanied by a satisfying sound effect. Simultaneously, a perfect, production-ready `AgentPromptSpec.md` and a meticulously crafted `EXPERIMENT_PLAN.md` are instantly generated in their local directory. The user realises that days of tedious requirements gathering, political maneuvering, and blank-page anxiety have been condensed into a 15-minute engaging simulation, resulting in a specification document that can be immediately copy-pasted into Cursor to build a working prototype.

## 2. Prerequisites
Before running the tutorial or the main application, the user requires the following:
*   **Python 3.12+** installed on their machine.
*   **uv** package manager installed (for rapid dependency resolution).
*   **API Keys**: A valid `OPENAI_API_KEY` (and optionally a `TAVILY_API_KEY` for advanced web search features) set in their `.env` file.
*   (For the Tutorial/Mock Mode): No API keys are required, as the system will utilize `unittest.mock` to simulate LLM and search responses.

## 3. Success Criteria
A successful user experience is defined by the following metrics:
*   The interactive tutorial (`tutorials/UAT_AND_TUTORIAL.py`) runs from start to finish in "Mock Mode" without raising any exceptions.
*   The user understands the workflow from Ideation to the final generation of the `AgentPromptSpec.md`.
*   The system successfully suspends execution at designated Human-in-the-Loop (HITL) gates, allows user input, and resumes flawlessly.
*   The final output files (`AgentPromptSpec.md`, `EXPERIMENT_PLAN.md`, and PDF canvases) are generated in the correct local directory format.

---

## 4. Test Scenarios (User Acceptance Tests)

### Scenario ID: UAT-01
*   **Priority:** High
*   **Title:** End-to-End Core Workflow Execution (The Fitness Journey)
*   **Description:** This scenario verifies that a user can successfully navigate the entire JTC 2.0 pipeline, from initial idea generation to the final output of the MVP specifications. It ensures that the strict Chain of Thought is maintained without hallucinations. The user will start with a basic idea for a new internal tool. The system must guide them through generating a Persona, Alternative Analysis, Value Proposition Canvas, Mental Model Diagram, and Customer Journey. Crucially, at the HITL gates (after the VPC and Sitemap generation), the system must pause and present the generated PDF canvases. The user will then provide a minor adjustment (e.g., "Make the target persona slightly older"). The system must accept this feedback, update the internal state, and proceed. Finally, the user must survive the simulated JTC Board meeting and the 3H Review, resulting in the successful generation of the `AgentPromptSpec.md` and `EXPERIMENT_PLAN.md`.

### Scenario ID: UAT-02
*   **Priority:** Medium
*   **Title:** Resilience Against Infinite Debate Loops
*   **Description:** This scenario tests the system's circuit breakers and token limiters during the multi-agent debate phases. The user will input a highly controversial or intentionally flawed business idea that is guaranteed to provoke strong disagreement between the Hacker, Hipster, and Hustler agents during the 3H Review. The test observes the agents' interaction. Instead of entering an infinite loop of rebuttals, the system's moderator logic must detect the stalemate (e.g., by tracking the number of turns or specific phrases) and force a resolution or termination of the debate within the configured `max_turns` limit. The system must then gracefully proceed to the next node or return an error state, preventing excessive API usage.

### Scenario ID: UAT-03
*   **Priority:** High
*   **Title:** Pyxel UI and State Synchronisation
*   **Description:** This scenario focuses on the decoupled frontend experience. The user runs the application, and the Pyxel UI launches in a separate window. As the LangGraph backend processes data (e.g., transitioning from the Ideation phase to the CPF phase), the Pyxel UI must accurately reflect the current state without freezing or crashing. When a major canvas is successfully generated and the backend pauses at a HITL gate, the Pyxel UI must immediately trigger the visual "Approval" stamp animation and play the corresponding sound effect. This test ensures the polling mechanism between the frontend and the `GlobalState` is robust and responsive.

---

## 5. Behavior Definitions (Gherkin)

**Feature: Schema-Driven Concept Generation**

**Scenario: Generating a Value Proposition Canvas without hallucinations**
*   **GIVEN** the system has successfully generated a Persona and an Alternative Analysis
*   **AND** the current workflow phase is `Phase.CPF`
*   **WHEN** the `vpc_node` is executed by the LangGraph engine
*   **THEN** the AI agent must output a valid JSON string that strictly conforms to the `ValuePropositionCanvas` Pydantic model
*   **AND** the `GlobalState` must be updated with this canvas
*   **AND** the system must transition to the first HITL gate

**Feature: Human-in-the-Loop Feedback**

**Scenario: User provides course correction during a HITL gate**
*   **GIVEN** the workflow is paused at the CPF feedback gate
*   **AND** the Pyxel UI is displaying the "Approval" stamp
*   **WHEN** the user inputs "Focus the pain points more on time-saving rather than cost" into the prompt interface
*   **THEN** the system must resume the graph execution
*   **AND** the subsequent `mental_model_journey_node` must incorporate this feedback into its generation process
*   **AND** the updated context must be reflected in the final output documents

**Feature: Infinite Loop Prevention**

**Scenario: The 3H Review reaches a stalemate**
*   **GIVEN** the Hacker and Hustler agents are debating the technical feasibility versus unit economics
*   **AND** the debate has reached the `max_turns` limit defined in `src/core/config.py`
*   **WHEN** the next agent attempts to respond
*   **THEN** the moderator circuit breaker must intercept the request
*   **AND** force a "Concession" or "Agreed to disagree" state
*   **AND** transition the workflow to the `spec_generation_node`

---

## 6. Tutorial Strategy and Plan

### 6.1 Tutorial Strategy
The tutorial strategy is designed to provide an immediate "Aha!" moment without requiring the user to spend money on API tokens or configure complex environments. This is achieved through a dual-mode approach:
*   **Mock Mode (Default for CI/Tutorials):** If `OPENAI_API_KEY` is not present, the system automatically defaults to using mocked LLM responses that return pre-validated JSON strings conforming to our Pydantic schemas. This allows users to experience the flow and the Pyxel UI instantly.
*   **Real Mode:** Once the user is comfortable, they can add their API keys to experience the actual generative power of the system.

### 6.2 Tutorial Plan
To ensure simplicity and ease of verification, a **SINGLE** Marimo notebook file will be created: `tutorials/UAT_AND_TUTORIAL.py`.

This single file will contain:
1.  **Introduction & Setup:** Explanation of the JTC 2.0 concept and instructions on how to toggle between Mock and Real modes.
2.  **Quick Start (UAT-01):** An automated walkthrough of the entire "Fitness Journey" using Mock Mode. Users can run the cells sequentially to watch the `GlobalState` evolve from an idea to a final `AgentPromptSpec.md`.
3.  **Advanced Scenarios:** Cells demonstrating the circuit breaker logic (UAT-02) and how to manually inspect the generated Pydantic models (VPC, Journey, etc.).
4.  **UI Demonstration:** Instructions on how to launch the separate Pyxel UI script alongside the notebook to observe the synchronisation (UAT-03).

### 6.3 Tutorial Validation
The `tutorials/UAT_AND_TUTORIAL.py` file must be executable via the `marimo run` or `marimo edit` commands. Continuous Integration (CI) pipelines will execute this notebook in Mock Mode to guarantee that changes to the core engine do not break the tutorial experience, ensuring the requirements and user acceptance criteria are continuously verified.
