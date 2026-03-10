# User Test Scenario & Tutorial Plan

## 1. Test Scenarios

### Scenario UAT-01: Quick Start & Ideation (Priority: High)
- **Description:** A new user runs the system for the first time with a simple topic (e.g., "AI for Agriculture").
- **Aha! Moment:** The user instantly sees 10 highly detailed, researched Lean Canvases generated within seconds, followed by an immediate transition into a Pyxel-based retro simulation where corporate agents debate the idea.
- **Expected Outcome:** The system should successfully query Tavily, generate 10 unique `LeanCanvas` objects without schema validation errors, and display the first "Hanko" (Approval) stamp in the Pyxel UI once the user selects an idea.

### Scenario UAT-02: Human-in-the-Loop (HITL) Feedback on CPF (Priority: High)
- **Description:** During Phase 2, the system generates the Value Proposition Canvas (VPC). The user provides negative or constructive feedback (e.g., "The target is too broad, focus on small farmers").
- **Aha! Moment:** The system stops, generates a beautiful PDF of the current VPC, and waits. The user sees their direct text input dynamically alter the AI's next iteration of the `CustomerProfile` and `ValueMap`.
- **Expected Outcome:** The system pauses at HITL Gate 1.5, accepts user input via the Pyxel prompt or console, successfully re-runs the `vpc_node` with the new constraints, and updates the PDF.

### Scenario UAT-03: Virtual Customer Rejection (Priority: Medium)
- **Description:** The user pushes an overly complex or expensive solution through to Phase 4.
- **Aha! Moment:** The Virtual Customer agent brutally rejects the idea based on the predefined `MentalModelDiagram` and `AlternativeAnalysis`, proving the system simulates real-world market friction rather than just agreeing with the user.
- **Expected Outcome:** The Virtual Customer agent outputs a low willingness-to-pay score and high friction feedback, triggering HITL Gate 2 where the user is forced to pivot or abandon the idea.

### Scenario UAT-04: Final Output Generation (Priority: High)
- **Description:** The user successfully navigates all 6 phases.
- **Aha! Moment:** The user receives a perfect, ready-to-use `AgentPromptSpec.md` and `ExperimentPlan` in their local directory, enabling them to instantly paste the prompt into Cursor and get a working Next.js app.
- **Expected Outcome:** The system completes Phase 6, plays the final "Approval" animation, and successfully writes `MVP_PROMPT_SPEC.md`, `EXPERIMENT_PLAN.md`, and the `RINGI_SHO.md` to disk.

## 2. Behavior Definitions (Gherkin-style)

```gherkin
Feature: Core Ideation and Schema Validation
  As an intrapreneur
  I want the system to generate structured business canvases
  So that I do not suffer from AI hallucination or logical leaps

  Scenario: Generating a Value Proposition Canvas
    Given the user has selected a Lean Canvas "Plan A"
    When the system executes the "vpc_node"
    Then the output MUST strictly conform to the `ValuePropositionCanvas` Pydantic schema
    And the output MUST NOT contain any extra fields
    And the Pyxel UI MUST display the "Approval" Hanko animation

Feature: Human In The Loop (HITL) Governance
  As a project manager
  I want to review intermediate models before proceeding
  So that I can correct the AI's direction

  Scenario: Intervening at a HITL Gate
    Given the system has reached "HITL Gate 1.5"
    When the system generates the PDF for the Value Proposition Canvas
    Then the system MUST pause execution
    And the system MUST prompt the user for feedback
    When the user inputs "Focus more on cost reduction"
    Then the system MUST regenerate the canvas incorporating the feedback
```

## 3. Tutorial Strategy

To ensure a smooth onboarding experience, the UAT scenarios will be transformed into executable, interactive tutorials using `marimo`.
- **Mock Mode (CI/No-API-Key):** For automated testing and users without API keys, the tutorial will use injected mocked LLM responses that return pre-validated JSON strings matching the Pydantic schemas.
- **Real Mode:** For users with API keys, the tutorial will execute the actual LangGraph workflow against live OpenAI/Tavily endpoints.

## 4. Tutorial Plan

A **SINGLE** Marimo notebook file will be created to house all tutorials:
- **File Path:** `tutorials/UAT_AND_TUTORIAL.py`
- **Content:** The notebook will contain:
  1. Setup and Environment Check (API Key validation).
  2. Scenario 1: Quick Start (Automated run through Phase 1).
  3. Scenario 2: Interactive HITL Demonstration (Pausing at a gate and accepting mock user input).
  4. Scenario 3: Final Output Verification (Displaying the generated Markdown files within the notebook).

## 5. Tutorial Validation

- The `tutorials/UAT_AND_TUTORIAL.py` must execute from start to finish without raising `pydantic.ValidationError` or `KeyError`.
- In Mock Mode, the execution must complete in under 10 seconds.
- In Real Mode, the execution should complete within 5 minutes, demonstrating the full capability of the LangGraph orchestrator and the strict schema enforcement.
