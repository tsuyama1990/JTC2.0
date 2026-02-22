# Cycle 3 User Acceptance Testing (UAT)

## 1. Test Scenarios

### Scenario 1: Transcript Injection and "Mom Test" Failure
-   **ID**: UAT-C03-01
-   **Priority**: High
-   **Description**: Verify that injecting negative customer feedback causes the CPO to suggest a pivot.
-   **Pre-conditions**: Cycle 1 & 2 complete. A file `interview_negative.txt` exists with content: "I would never pay for this service. It's too complicated."
-   **Steps**:
    1.  Ingest the file into the system.
    2.  Run the "CPO Consultation" phase.
-   **Expected Result**:
    -   The CPO Agent outputs a message quoting "I would never pay for this".
    -   The CPO suggests a specific pivot (e.g., "Simplify the product" or "Change the revenue model").

### Scenario 2: Validation Success
-   **ID**: UAT-C03-02
-   **Priority**: Medium
-   **Description**: Verify that positive feedback reinforces the plan.
-   **Pre-conditions**: A file `interview_positive.txt` exists with content: "This solves my biggest headache. I'll pay $100 right now."
-   **Steps**:
    1.  Ingest the file.
    2.  Run the CPO Agent.
-   **Expected Result**:
    -   The CPO Agent confirms: "Customer validation is strong."
    -   The system state moves to "Solution Design" readiness.

## 2. Behavior Definitions (Gherkin)

```gherkin
Feature: Reality Injection (RAG)

  Scenario: CPO Agent detects a pricing mismatch
    GIVEN the Plan A is a "$50/month subscription"
    AND the Vector Store contains a transcript saying "My budget is max $10"
    WHEN the CPO Agent reviews the plan against the data
    THEN it should retrieve the "max $10" chunk
    AND it should advise "Your pricing model is invalidated by customer data."

  Scenario: Ingesting new data updates the index
    GIVEN an empty Vector Store
    WHEN the user uploads "new_interview.txt"
    THEN the document count in the index should increase by 1
    AND the content should be searchable immediately
```
