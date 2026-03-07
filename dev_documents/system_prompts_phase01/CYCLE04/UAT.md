# Cycle 4 User Acceptance Testing (UAT)

## 1. Test Scenarios

### Scenario 1: Identify Key Influencer
-   **ID**: UAT-C04-01
-   **Priority**: Medium
-   **Description**: Verify that the system correctly identifies the most influential node in the network.
-   **Pre-conditions**: A standard JTC network is loaded.
-   **Steps**:
    1.  Run the Nemawashi analysis.
-   **Expected Result**:
    -   System identifies "Finance Manager" or "CEO" as the Key Influencer.
    -   System advises: "Convince the Finance Manager first to sway the CEO."

### Scenario 2: The "Nomikai" Effect
-   **ID**: UAT-C04-02
-   **Priority**: High
-   **Description**: Verify that simulating a social event changes the outcome of the consensus.
-   **Pre-conditions**: Initial consensus is "Rejected" (< 0.5).
-   **Steps**:
    1.  Execute `run_nomikai_simulation(target="Finance Manager")`.
    2.  Re-run the DeGroot consensus check.
-   **Expected Result**:
    -   The Finance Manager's support score increases (e.g., 0.1 -> 0.4).
    -   The final group consensus score crosses the threshold (e.g., > 0.6).
    -   System Output: "Nomikai successful. Finance Manager is now open to the idea."

## 2. Behavior Definitions (Gherkin)

```gherkin
Feature: Organizational Politics (Nemawashi)

  Scenario: Opinions converge over time
    GIVEN a network of 3 agents with opinions [0.1, 0.5, 0.9]
    AND a connected influence matrix
    WHEN the simulation runs for 5 steps
    THEN the variance of opinions should decrease
    AND the values should approach a weighted average

  Scenario: Stubborn agents resist change
    GIVEN the Finance Manager has stubbornness 0.9 (Self-weight)
    AND the Sales Manager tries to influence them
    WHEN the simulation runs
    THEN the Finance Manager's opinion should change very slowly (< 0.1 change per step)
```
