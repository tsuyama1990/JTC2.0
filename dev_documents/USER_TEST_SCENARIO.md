# User Test Scenario & Tutorial Plan

## 1. Test Scenarios

### Scenario ID: UAT-001 - The "Aha! Moment" (Full Pipeline Execution)
**Priority**: High
**Description**:
This scenario represents the primary "Magic Moment" for the user. The objective is to demonstrate the sheer power of the "JTC 2.0 Remastered" methodology by executing the entire 14-step pipeline from a single, rudimentary prompt. The user provides a basic idea, such as "An AI tool for corporate brainstorming". The system must then autonomously execute the Ideation phase, pause for the first Human-in-the-Loop (HITL) gate, and display the generated Pydantic models (Persona and Empathy Map) along with the Pyxel "Approval Stamp" animation. The user experiences the thrill of seeing their vague idea transformed into rigorous, structured business logic without any hallucinated leaps. The scenario continues through the "Problem Solution Fit" phase, where the user witnesses the Virtual Customer agent brutally critiquing the generated Mental Model and textual wireframes. The ultimate success criterion is the automatic, error-free generation of the final `MVP_PROMPT_SPEC.md` and `EXPERIMENT_PLAN.md` files in the output directory. This single command execution must demonstrate that the system is not merely a chatbot, but a comprehensive, autonomous requirements engineering pipeline. We will use a dedicated Marimo notebook to allow users to execute this scenario seamlessly in a controlled environment.

### Scenario ID: UAT-002 - Human-in-the-Loop (HITL) Intervention
**Priority**: High
**Description**:
This scenario validates the "De-identification" and control mechanisms built into the Remastered architecture. The AI must not run away with an idea unchecked. The user starts a session with the prompt "A new accounting SaaS". When the system reaches the first HITL gate (after generating the Value Proposition Canvas), the user must actively intervene. The user will review the outputted PDF and provide corrective feedback via the Pyxel prompt, such as "The target audience is too broad, narrow it down to freelance graphic designers". The system must successfully ingest this feedback, rollback the necessary state, and regenerate the Persona and VPC to strictly align with the new constraint. The success criterion is the system's ability to demonstrate obedience to human constraints whilst maintaining the structural integrity of the Pydantic models. The Pyxel UI must clearly show the system pausing, awaiting input, and then re-running the animation upon successful validation. This scenario proves that the JTC 2.0 platform is a co-pilot, not an uncontrollable auto-pilot.

### Scenario ID: UAT-003 - Circuit Breaker and Token Limit Enforcement
**Priority**: Medium
**Description**:
This scenario ensures the system's robustness against the inherent unpredictability of multi-agent debates. The user will initiate a scenario specifically designed to cause friction, for example, "A business model that completely cannibalises our existing enterprise sales". During the "JTC Board Simulation" phase, the Finance and Sales agents will inevitably clash over the Alternative Analysis and ROI projections. To test the circuit breakers, we will simulate a scenario (via mock inputs or specific prompt injection) where the agents enter a repetitive loop of disagreement. The system must successfully detect this loop based on the `max_turns` configuration or specific phrase detection defined in the Settings. The success criterion is that the system gracefully aborts the simulation loop, prevents further API token consumption, and presents a fallback UI or summary message to the user, rather than crashing or running indefinitely. This demonstrates the enterprise-grade observability and cost-control measures integrated into the architecture.

## 2. Behavior Definitions (Gherkin)

**Feature**: Autonomous Idea Validation and Spec Generation

  **Scenario**: The user executes the full pipeline to generate an MVP specification
    **Given** the user has configured the environment with valid OpenAI and Tavily API keys
    **And** the system is running the LangGraph orchestration
    **When** the user inputs the topic "AI for Agriculture"
    **Then** the system should generate 10 Lean Canvas ideas
    **And** pause at the first HITL gate to request user selection
    **When** the user selects "Plan A"
    **Then** the system must strictly generate a `Persona`, `EmpathyMap`, and `ValuePropositionCanvas` using Pydantic models
    **And** render the "Approval" stamp animation on the Pyxel UI
    **And** export the models as a PDF document
    **When** the user approves the CPF models
    **Then** the system must proceed to generate the `MentalModelDiagram` and `CustomerJourney`
    **And** the Virtual Customer agent must critique the resulting textual wireframes
    **When** the simulation completes successfully
    **Then** the system must output a formatted `MVP_PROMPT_SPEC.md` file
    **And** a formatted `EXPERIMENT_PLAN.md` file
    **And** both files must exist in the designated output directory without schema errors.

  **Scenario**: The user corrects the system during a HITL gate
    **Given** the system has paused at the "Problem Solution Fit" HITL gate
    **And** the system has generated a textual wireframe for a dashboard
    **When** the user inputs the feedback "Remove the analytics feature, focus only on data entry"
    **Then** the system must invoke the Builder agent with the subtraction constraint
    **And** the subsequent `AgentPromptSpec` must not contain any routing or components related to analytics
    **And** the Pyxel UI must register the updated state.

  **Scenario**: The circuit breaker prevents infinite debate loops
    **Given** the "3H Review" simulation is active
    **And** the Hacker and Hustler agents fail to reach a consensus within the configured `max_turns` limit
    **When** the turn counter exceeds the limit
    **Then** the system must immediately terminate the debate node
    **And** log a circuit breaker exception
    **And** proceed to the next phase using the last known valid state, ensuring API limits are not breached.


## 3. Tutorial Strategy

The tutorial strategy aims to eliminate the friction typically associated with complex AI orchestration platforms. Instead of forcing users to read extensive README files and manually execute command-line scripts, we will leverage **Marimo**, a reactive Python notebook environment.

This approach allows users to verify requirements and ensure reproducibility in a highly visual, step-by-step manner. The tutorial will be split into two modes:
1.  **Mock Mode (CI/No-API-Key)**: For users evaluating the architecture or running automated tests. This mode injects pre-defined, perfect Pydantic responses into the LLM client, allowing the user to witness the pipeline flow, the Pyxel animations, and the final document generation without consuming any API credits.
2.  **Real Mode**: For actual usage. The notebook will guide the user through setting their API keys securely and running the pipeline against real-world prompts.

The entire experience must be encapsulated within a single, cohesive file to prevent cognitive overload.

## 4. Tutorial Plan

To implement the strategy, a single Marimo notebook file will be created:

*   **File Path**: `tutorials/UAT_AND_TUTORIAL.py`

This single file will contain:
*   **Introduction & Setup**: Clear instructions on required keys and dependencies.
*   **Quick Start (The Magic Moment)**: A fully automated run of UAT-001 in Mock Mode. The user simply clicks "Run" and watches the system generate the `MVP_PROMPT_SPEC.md` from start to finish.
*   **Deep Dive (HITL)**: An interactive section demonstrating UAT-002, where the notebook pauses and provides an input field for the user to inject custom feedback into the LangGraph state.
*   **Architecture Exploration**: Visualizations of the Pydantic schemas and the LangGraph structure to educate the user on *how* the hallucination-free generation is achieved.

## 5. Tutorial Validation

To ensure the tutorial is robust:
1.  The `UAT_AND_TUTORIAL.py` file must be executable entirely from top to bottom without throwing any unhandled exceptions.
2.  In "Mock Mode", the tutorial must successfully generate the `MVP_PROMPT_SPEC.md` and `EXPERIMENT_PLAN.md` files in the output directory.
3.  The Pyxel UI dependencies must be properly managed so that running the notebook does not crash headless environments (e.g., CI pipelines), gracefully falling back to text logs if a display is unavailable.
4.  All Python code within the Marimo cells must adhere strictly to the project's Ruff and MyPy configurations.
