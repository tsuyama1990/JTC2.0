# Cycle 1 User Acceptance Testing (UAT)

## 1. Test Scenarios

### Scenario 1: Initial Idea Generation
-   **ID**: UAT-C01-01
-   **Priority**: High
-   **Description**: Verify that the system can generate 10 distinct, relevant business ideas based on a broad topic.
-   **Pre-conditions**: Valid API keys for OpenAI and Tavily are set in `.env`.
-   **Steps**:
    1.  Run the application.
    2.  Enter the topic: "AI for Agriculture".
    3.  Wait for the process to complete (approx 30-60 seconds).
    4.  Inspect the output list.
-   **Expected Result**:
    -   10 distinct `LeanCanvas` objects are displayed.
    -   Each has a title, problem, and solution.
    -   The ideas are relevant to "Agriculture".

### Scenario 2: Idea Selection (Gate 1)
-   **ID**: UAT-C01-02
-   **Priority**: High
-   **Description**: Verify the user can select a single idea to proceed (mocking the start of the next phase).
-   **Pre-conditions**: UAT-C01-01 has passed.
-   **Steps**:
    1.  From the list of 10 ideas, input the ID of the 3rd idea (e.g., "2").
    2.  System acknowledges the selection.
-   **Expected Result**:
    -   System prints: "Selected Plan: [Title of Idea 3]".
    -   The internal state reflects this selection (verified via debug log or marimo variable).

## 2. Behavior Definitions (Gherkin)

```gherkin
Feature: Idea Generation and Selection

  Scenario: User requests ideas for a new domain
    GIVEN the system is initialized
    AND the user provides the topic "Sustainable Fashion"
    WHEN the Ideator Agent runs
    THEN it should call the Tavily Search Tool to research "Sustainable Fashion trends"
    AND it should generate a list of exactly 10 Lean Canvas drafts
    AND each draft should have a unique Value Proposition

  Scenario: User selects a plan
    GIVEN 10 ideas have been generated
    WHEN the user inputs the ID "5"
    THEN the system should lock "Idea #5" as the "Selected Idea"
    AND the system state should transition to "Verification" readiness
```
