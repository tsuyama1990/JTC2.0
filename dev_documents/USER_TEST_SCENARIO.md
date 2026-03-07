# User Test Scenario & Tutorial Plan

## 1. Test Scenarios

These User Acceptance Tests (UAT) are designed to ensure the system delivers a truly magical experience. The UAT scenarios effectively serve as interactive tutorials for new users.

### Scenario 1: The "Aha!" Moment (Quick Start)
**ID:** UAT-01
**Priority:** High
**Description:** The user runs a single command to initiate the ideation phase and experiences the magic of seeing 10 fully fleshed-out business ideas generated instantly from a simple prompt. The user then selects one idea, and the system immediately generates a Persona and Value Proposition Canvas, culminating in a satisfying visual "Approval" stamp on the retro UI. This initial flow establishes the baseline of the simulation. Once the canvas is constructed, the user will see a prompt generated from a highly advanced AI system that strictly adheres to structural models, eliminating all forms of hallucination. The user will review the generated Persona, mapping out how the specific pain points and gains align with the product features. The retro UI provides an engaging, low-stress environment where even critical feedback is de-identified. Finally, the user experiences the satisfaction of a virtual "Hanko" stamp, progressing them seamlessly to the next phase without any manual intervention.
**Amaze Factor:** The sheer speed and depth of the generated business models, contrasted with the charming, nostalgic pixel-art approval animation.
**Time to Complete:** Under 3 minutes.

### Scenario 2: The Harsh Reality of the JTC (Advanced Simulation)
**ID:** UAT-02
**Priority:** Medium
**Description:** Building on UAT-01, the user progresses to the JTC Board Simulation. The user watches as their selected idea is mercilessly critiqued by the virtual Finance and Sales Managers based on the Alternative Analysis and Customer Journey mapped out earlier. The simulation accurately represents a typical Traditional Japanese Company (JTC) environment where new ideas face extreme scrutiny and skepticism. The user will observe the interactions and adversarial questioning from the virtual agents. This phase will test the boundaries of the value proposition against corporate financial and sales expectations. The rigorous debate will force the user to reflect on potential market cannibalization and the true cost of acquiring users, ultimately leading to a more robust and resilient business model before moving forward.
**Amaze Factor:** The uncanny realism of the AI agents' corporate jargon and the depth of their critique, which is directly tied to the previously generated psychological mental models and unit economics.
**Time to Complete:** Under 5 minutes.

### Scenario 3: The Ultimate Output (End-to-End Execution)
**ID:** UAT-03
**Priority:** High
**Description:** The user navigates the entire 14-step workflow, successfully passing all Human-in-the-Loop (HITL) feedback gates. The scenario concludes with the system outputting the final, perfectly formatted `AgentPromptSpec.md` and `EXPERIMENT_PLAN.md` files into the local directory. The user will follow the complete journey, experiencing the dynamic shifts from ideation to severe criticism, and finally to solution refinement. The output provides a highly structured Markdown file that can be immediately used by AI-assisted coding tools like Cursor to generate the Minimum Viable Product. This scenario proves that the system functions as a true architectural engine, replacing fragmented ideation processes with a continuous, unified pipeline that yields tangible software requirements.
**Amaze Factor:** The user realises they now possess a robust, ready-to-code technical specification document that completely bridges the gap between a vague idea and a deployable product, completely free from AI hallucinations.
**Time to Complete:** Under 10 minutes.

## 2. Behavior Definitions (Gherkin-Style)

### Feature: Idea Generation and Selection
**Scenario:** Generating initial Lean Canvases
**GIVEN** the user has a valid API key for Tavily and OpenAI
**WHEN** the user runs the CLI application with the argument "AI for Agriculture"
**THEN** the system should perform a PEST analysis
**AND** output exactly 10 distinct Lean Canvas drafts
**AND** present a prompt for the user to select "Plan A"

### Feature: Schema-Driven Concept Validation
**Scenario:** Generating the Value Proposition Canvas and receiving the first stamp
**GIVEN** the user has selected "Plan A"
**WHEN** the system completes the Alternative Analysis and Value Proposition Design phases
**THEN** the system must strictly adhere to the Pydantic schemas
**AND** output a formatted PDF document containing the VPC
**AND** trigger a pixel-art "Approval" stamp animation on the Pyxel UI
**AND** pause execution to await Human-in-the-Loop feedback

### Feature: Multi-Agent Corporate Simulation
**Scenario:** Surviving the 3H Review
**GIVEN** the system has generated the Sitemap and User Story
**WHEN** the workflow enters the 3H Review node
**THEN** the Hacker agent should critique technical feasibility
**AND** the Hipster agent should critique UX friction
**AND** the Hustler agent should critique unit economics
**AND** the system must invoke a circuit breaker if the agents enter an infinite loop of agreement or disagreement

### Feature: Final Specification Generation
**Scenario:** Producing the `AgentPromptSpec.md`
**GIVEN** the system has successfully passed all review gates
**WHEN** the system enters the Output Generation phase
**THEN** the Builder Agent must compile all context into a single Markdown file
**AND** the file must include a valid Mermaid state machine diagram
**AND** the final `EXPERIMENT_PLAN.md` must be saved to the local directory

## 3. Tutorial Strategy

To ensure seamless onboarding and rapid verification of system capabilities, we will adopt a unified, interactive tutorial strategy using Marimo.

### 3.1 Strategy: "Mock Mode" vs. "Real Mode"
*   **Mock Mode:** For Continuous Integration (CI) and users without API keys, the tutorial will employ `unittest.mock` to simulate external LLM and Tavily responses. It will output pre-defined, perfect Pydantic JSON strings. This guarantees the tutorial executes flawlessly offline, demonstrating the state transitions and UI effects without incurring costs.
*   **Real Mode:** If valid environment variables (`OPENAI_API_KEY`, `TAVILY_API_KEY`) are detected, the tutorial will execute the actual LangGraph orchestration, proving the real-world efficacy of the prompt engineering.

### 3.2 Tutorial Plan
A **SINGLE** Marimo file named `tutorials/UAT_AND_TUTORIAL.py` will be created.
This file will encapsulate all test scenarios (Quick Start and Advanced) in an interactive, reproducible format. Consolidating the UATs into a single Marimo notebook reduces cognitive load and provides a cohesive narrative arc for the user, taking them from idea generation to the final `AgentPromptSpec` output in one smooth flow.

### 3.3 Tutorial Validation
The success of the tutorial strategy is validated by executing `marimo run tutorials/UAT_AND_TUTORIAL.py`. A successful run must execute from top to bottom without any Python exceptions or Pydantic validation errors, demonstrating the robustness of the underlying architecture.