# Cycle 5 User Acceptance Testing (UAT)

## 1. Test Scenarios

### Scenario 1: Feature Pruning
-   **ID**: UAT-C05-01
-   **Priority**: High
-   **Description**: Verify that the system forces the user to select a single feature for the MVP.
-   **Pre-conditions**: Cycle 4 passed. The Plan has 3 proposed features.
-   **Steps**:
    1.  Enter the MVP Construction phase.
    2.  System presents the 3 features.
    3.  User attempts to select 2.
-   **Expected Result**:
    -   System rejects the selection: "Please select only ONE core feature for the MVP."
    -   User selects 1.
    -   System accepts and proceeds.

### Scenario 2: MVP Generation (v0.dev)
-   **ID**: UAT-C05-02
-   **Priority**: Critical
-   **Description**: Verify that the system successfully calls the v0.dev API and returns a URL.
-   **Pre-conditions**: Feature selected. Valid API Key.
-   **Steps**:
    1.  Trigger generation.
    2.  Wait (approx 10-20 seconds).
-   **Expected Result**:
    -   System displays: "MVP Generated Successfully: https://v0.dev/..."
    -   The URL is valid (returns 200 OK when checked).

## 2. Behavior Definitions (Gherkin)

```gherkin
Feature: Automated MVP Construction

  Scenario: Generating a UI from a spec
    GIVEN the MVP Spec is "A login page for a pet sitting app"
    WHEN the Builder Agent calls v0.dev
    THEN the API request should contain "React", "Tailwind CSS", and the specific feature description
    AND the response should contain a valid URL string
```
