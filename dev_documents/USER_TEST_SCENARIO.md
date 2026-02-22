# User Test Scenarios & Tutorial Plan

## 1. Tutorial Strategy

The "The JTC 2.0" is a complex system involving multiple AI agents, mathematical models, and external API calls. To ensure that new users (and potential investors) can understand and verify the system's capabilities without incurring massive API costs or setting up complex environments, we will implement a **Unified Tutorial & UAT Strategy** using **Marimo**.

### 1.1. Marimo as the Interface
We will use `marimo` (a reactive Python notebook) as the primary interface for both:
1.  **User Acceptance Testing (UAT)**: Developers use it to verify features during the cycle.
2.  **Interactive Tutorials**: Users use it to learn the system step-by-step.

### 1.2. Mock Mode vs. Real Mode
To make the tutorial accessible:
-   **Real Mode**: Connects to actual OpenAI, Tavily, and v0.dev APIs. Requires `.env` keys.
-   **Mock Mode**: Uses pre-recorded responses for all agents. This allows the tutorial to run in CI/CD environments and for users without API keys to see the "Happy Path."

## 2. Tutorial Plan

We will create a **SINGLE** master file: `tutorials/UAT_AND_TUTORIAL.py`.
This file will contain sections corresponding to the 4 Critical User Journeys defined below.

### Section 1: Ideation (The Spark)
-   **Goal**: Demonstrate how the system generates Lean Canvases.
-   **Interaction**: User inputs a topic -> System shows 3 ideas -> User selects 1.

### Section 2: The Meeting (The Grill)
-   **Goal**: Demonstrate the "Gekizume" simulation.
-   **Interaction**: User watches a turn-based debate between "New Employee" and "Finance Manager".

### Section 3: Reality Check (The Pivot)
-   **Goal**: Demonstrate RAG and CPO intervention.
-   **Interaction**: User "uploads" a mock transcript -> CPO points out a contradiction.

### Section 4: Execution (The Build)
-   **Goal**: Demonstrate MVP Generation.
-   **Interaction**: System generates a v0.dev URL (mocked or real).

## 3. Critical Test Scenarios (UAT)

These scenarios define the acceptance criteria for the project.

### Scenario 1: Idea Verification (Cycle 1)
-   **User Story**: As an entrepreneur, I want to generate multiple business models from a vague idea so that I can choose the best starting point.
-   **Acceptance Criteria**:
    -   System generates 10 distinct Lean Canvases.
    -   Each canvas has a unique "Unique Value Proposition".
    -   User selection is correctly stored in the state.

### Scenario 2: Simulation & De-identification (Cycle 2)
-   **User Story**: As a timid employee, I want to see my idea criticized by AI agents so that I can find flaws without feeling personally attacked.
-   **Acceptance Criteria**:
    -   Finance Manager Agent asks at least 1 quantitative question (ROI, Cost).
    -   Sales Manager Agent asks at least 1 market-fit question.
    -   The "New Employee" proxy agent attempts to defend the idea.

### Scenario 3: The "Mom Test" (Cycle 3)
-   **User Story**: As a product manager, I want to validate my plan against real customer interviews so that I don't build something nobody wants.
-   **Acceptance Criteria**:
    -   System ingests a text file containing "Negative Feedback" (e.g., "Too expensive").
    -   CPO Agent detects the conflict between "Plan Price" and "Customer Budget".
    -   CPO Agent explicitly recommends a Pivot.

### Scenario 4: MVP Construction (Cycle 5)
-   **User Story**: As a non-coder, I want to see a working prototype of my solution immediately so that I can show it to stakeholders.
-   **Acceptance Criteria**:
    -   System accepts a finalized feature list.
    -   Builder Agent constructs a valid prompt for v0.dev.
    -   System returns a valid URL (or a mocked success message with a placeholder URL).

## 4. Tutorial Validation

To validate the tutorial itself:
1.  Run `marimo edit tutorials/UAT_AND_TUTORIAL.py --headless` in the CI pipeline.
2.  Ensure it executes from top to bottom without error in "Mock Mode".
