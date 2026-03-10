# User Test Scenario & Tutorial Plan

## 1. Test Scenarios

### Scenario ID: UAT-001 - The "Aha! Moment" (Full Pipeline Execution)
**Priority**: High
**Description**:
This critical scenario represents the primary "Magic Moment" for the user. The primary objective is to demonstrate the sheer power, accuracy, and absolute lack of hallucination of the "JTC 2.0 Remastered" methodology by executing the entire, highly complex 14-step pipeline from a single, rudimentary prompt. The user provides a basic idea, such as "An AI tool for corporate brainstorming". The system must then autonomously execute the Ideation phase, pulling down real-time market data via Tavily, and pause precisely at the first Human-in-the-Loop (HITL) gate. It must flawlessly display the newly generated Pydantic models (the strictly typed Persona and Empathy Map) along with the deeply satisfying Pyxel "Approval Stamp" (Hanko) animation, triggering a retro sound effect. The user experiences the thrill of seeing their vague idea transformed into rigorous, structured business logic without a single hallucinated leap or unprompted feature injection. The scenario then seamlessly continues through the "Problem Solution Fit" phase. Here, the user witnesses the dynamically instantiated Virtual Customer agent brutally and logically critiquing the generated Mental Model and pure textual wireframes based *only* on the previously generated context. The ultimate, non-negotiable success criterion for this scenario is the automatic, entirely error-free generation of the final `MVP_PROMPT_SPEC.md` and `EXPERIMENT_PLAN.md` files in the designated output directory. This single command execution must definitively prove to the user that the system is not merely an interactive chatbot, but a comprehensive, completely autonomous requirements engineering and Go-To-Market pipeline capable of producing enterprise-grade documentation. We will use a dedicated Marimo notebook (`tutorials/UAT_AND_TUTORIAL.py`) to allow users to execute this scenario seamlessly in a highly controlled, visual environment.

### Scenario ID: UAT-002 - Human-in-the-Loop (HITL) Intervention
**Priority**: High
**Description**:
This scenario validates the crucial "De-identification" and strict control mechanisms built deeply into the Remastered architecture. The core tenet is that the AI must *never* run away with an idea unchecked by human intuition. The user starts a fresh session with the prompt "A new accounting SaaS for small businesses." When the LangGraph execution inevitably reaches the first HITL gate (immediately after successfully generating the massive Value Proposition Canvas), the user must actively intervene to alter the trajectory. The user will review the dynamically outputted, highly structured PDF document and provide specific, corrective feedback via the Pyxel prompt interface. For example, the user might input, "The target audience is far too broad, you must narrow it down exclusively to freelance graphic designers operating in Tokyo." The system must successfully and accurately ingest this specific feedback, rollback the necessary internal state, and force the LLM to regenerate both the Persona and the VPC to strictly align with the new, narrowed constraint without throwing a Pydantic `ValidationError`. The success criterion is the system's ability to demonstrate total obedience to human constraints whilst simultaneously maintaining the absolute structural integrity of the complex Pydantic models. The Pyxel UI must clearly and unambiguously show the system pausing, awaiting the human input, and then re-running the satisfying Hanko animation upon successful re-validation of the new, constrained models. This scenario conclusively proves that the JTC 2.0 platform is a highly obedient co-pilot, absolutely not an uncontrollable auto-pilot.

### Scenario ID: UAT-003 - Circuit Breaker and Token Limit Enforcement
**Priority**: Medium
**Description**:
This scenario is specifically designed to rigorously test the system's robustness against the inherent unpredictability, cost, and chaos of multi-agent LLM debates. The user will deliberately initiate a scenario specifically engineered to cause maximum political friction. For example, the user prompts, "A direct-to-consumer business model that completely cannibalises our existing, highly profitable B2B enterprise sales division." During the highly volatile "JTC Board Simulation" phase, the simulated Finance and Sales agents will inevitably clash over the Alternative Analysis, highlighting the extreme ROI risk and the guaranteed market cannibalization. To thoroughly test the internal circuit breakers, we will simulate a scenario (via mock inputs or highly specific, adversarial prompt injection) where the agents enter a deeply repetitive, unresolvable loop of disagreement (e.g., repeating "I cannot approve this without further data"). The LangGraph system must successfully and immediately detect this loop based on the strict `max_turns` configuration or by recognizing specific phrase detection patterns defined within the `SimulationConfig` Pydantic settings. The absolute success criterion is that the system gracefully and safely aborts the simulation loop, immediately preventing any further (and expensive) API token consumption. It must then present a clear fallback UI or a summarized "Deadlock" message to the user, rather than crashing with an unhandled exception or, worse, running indefinitely and racking up API charges. This scenario conclusively demonstrates the vital enterprise-grade observability and strict cost-control measures integrated deeply into the core architecture.

## 2. Behavior Definitions (Gherkin)

**Feature**: Autonomous Idea Validation and Spec Generation

  **Scenario**: The user successfully executes the full pipeline to generate an MVP specification
    **Given** the user has correctly configured the environment with valid, funded OpenAI and Tavily API keys
    **And** the system is currently running the primary LangGraph orchestration loop
    **When** the user inputs the topic "AI for Agriculture"
    **Then** the system must utilize Tavily to research and generate exactly 10 distinct Lean Canvas ideas
    **And** it must pause execution at the very first HITL gate to request a human user selection
    **When** the human user deliberately selects "Plan A"
    **Then** the system must strictly and accurately generate a `Persona`, an `EmpathyMap`, and a complex `ValuePropositionCanvas` using the predefined Pydantic models
    **And** it must flawlessly render the "Approval" (Hanko) stamp animation and trigger the sound effect on the Pyxel UI
    **And** it must simultaneously export these highly structured models as a beautiful, human-readable PDF document
    **When** the user officially approves the generated CPF models via the Pyxel prompt
    **Then** the system must automatically proceed to generate the deep `MentalModelDiagram` and the chronological `CustomerJourney`
    **And** the dynamically instantiated Virtual Customer agent must aggressively critique the resulting pure textual wireframes
    **When** the multi-agent simulation eventually completes successfully without hitting a circuit breaker
    **Then** the system must successfully output a perfectly formatted Markdown `MVP_PROMPT_SPEC.md` file
    **And** it must simultaneously output a perfectly formatted Markdown `EXPERIMENT_PLAN.md` file detailing the AARRR metrics
    **And** both of these critical files must exist in the designated local output directory absolutely without any schema or Markdown formatting errors.

  **Scenario**: The user decisively corrects the system trajectory during a HITL gate
    **Given** the LangGraph system has correctly paused execution at the "Problem Solution Fit" HITL gate
    **And** the system has already generated a detailed textual wireframe for a complex analytics dashboard
    **When** the human user inputs the specific, subtractive feedback "Remove the entire analytics feature, focus only on the manual data entry flow"
    **Then** the system must immediately invoke the final Builder agent, injecting this strict subtraction constraint into its context
    **And** the subsequent generated `AgentPromptSpec` must absolutely not contain any routing paths, UI components, or logic related to the removed analytics feature
    **And** the Pyxel UI must clearly register and display the newly updated, constrained state to the user.

  **Scenario**: The strict circuit breaker prevents infinite, costly debate loops
    **Given** the highly volatile "3H Review" (Hacker, Hipster, Hustler) simulation is currently active
    **And** the Hacker and Hustler agents fundamentally fail to reach a consensus within the strictly configured `max_turns` limit defined in `Settings`
    **When** the internal turn counter exceeds this predefined, hardcoded limit
    **Then** the LangGraph system must immediately and forcefully terminate the current debate node execution
    **And** it must log a specific, highly visible circuit breaker `SimulationDeadlockException` to the console and LangSmith trace
    **And** it must gracefully proceed to the next logical phase using the last known valid state, absolutely ensuring that external API limits and budgets are not breached by a runaway loop.


## 3. Tutorial Strategy

The overarching tutorial strategy aims to completely eliminate the massive friction typically associated with onboarding users to highly complex AI orchestration platforms. Instead of forcing busy users to read extensive, dry README files and manually execute archaic command-line scripts, we will leverage **Marimo**, a highly reactive, modern Python notebook environment.

This approach allows users to verify complex requirements and ensure total reproducibility in a highly visual, extremely satisfying, step-by-step manner. The tutorial will be split into two distinct, highly valuable modes:
1.  **Mock Mode (CI/No-API-Key)**: This mode is designed explicitly for users evaluating the architecture, or for running automated tests in headless CI pipelines. This mode injects pre-defined, mathematically perfect Pydantic JSON responses directly into the LLM client wrapper. This allows the user to flawlessly witness the entire LangGraph pipeline flow, the satisfying Pyxel animations, and the final document generation instantly, absolutely without consuming any paid OpenAI API credits or requiring network access.
2.  **Real Mode**: This is for actual, real-world usage. The interactive notebook will gently guide the user through setting their specific API keys securely and running the entire pipeline against their own real-world, highly specific business prompts.

The entire, comprehensive experience must be encapsulated within a single, cohesive Marimo file to completely prevent cognitive overload and configuration hell.

## 4. Tutorial Plan

To perfectly implement this strategy, exactly one single Marimo notebook file will be created and maintained:

*   **File Path**: `tutorials/UAT_AND_TUTORIAL.py`

This single, master file will contain the following distinct, highly interactive sections:
*   **Introduction & Secure Setup**: Clear, concise instructions on obtaining the required API keys (OpenAI, Tavily, LangSmith) and installing the specific Python dependencies via `uv`.
*   **Quick Start (The Magic Moment)**: A fully automated, instant run of scenario UAT-001 operating entirely in "Mock Mode". The user simply clicks "Run" on the cell and watches the entire system generate the `MVP_PROMPT_SPEC.md` from start to finish in seconds, proving the pipeline works locally.
*   **Deep Dive (HITL Intervention)**: A highly interactive section demonstrating scenario UAT-002. Here, the Marimo notebook intentionally pauses execution and provides a native input field, allowing the user to type custom, subtractive feedback directly into the LangGraph state and watch the AI instantly pivot its strategy based on the text.
*   **Architecture Exploration**: This final section provides beautiful, dynamically generated visualizations of the complex Pydantic schemas and the internal LangGraph node structure. This exists to explicitly educate the user on *exactly how* the hallucination-free generation is achieved under the hood, building extreme trust in the system.

## 5. Tutorial Validation

To ensure the tutorial is truly robust and entirely bulletproof:
1.  The `UAT_AND_TUTORIAL.py` file must be executed entirely from top to bottom (Run All) without throwing a single, unhandled exception or `NameError`.
2.  While operating in "Mock Mode", the tutorial must successfully and deterministically generate the `MVP_PROMPT_SPEC.md` and `EXPERIMENT_PLAN.md` files in the exact designated output directory.
3.  The Pyxel UI dependencies must be properly and carefully managed so that running the notebook does not violently crash headless environments (e.g., GitHub Actions CI pipelines). It must gracefully catch display errors and fall back to clean text logs if a physical display is unavailable.
4.  Every single line of Python code contained within the Marimo cells must adhere strictly to the project's ruthless Ruff (`max-complexity=10`) and MyPy (`strict=True`) configurations, completely preventing AI-generated spaghetti code from entering the tutorial.