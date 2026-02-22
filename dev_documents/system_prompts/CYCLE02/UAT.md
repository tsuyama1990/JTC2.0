# Cycle 2 User Acceptance Testing (UAT)

## 1. Test Scenarios

### Scenario 1: The "Gekizume" Meeting
-   **ID**: UAT-C02-01
-   **Priority**: Critical
-   **Description**: Verify that the selected idea triggers a realistic debate between the Finance and Sales agents.
-   **Pre-conditions**: An idea has been selected in Cycle 1.
-   **Steps**:
    1.  Proceed to the "Simulation" phase.
    2.  Observe the Pyxel window or console logs.
-   **Expected Result**:
    -   The "New Employee" agent introduces the idea.
    -   The "Finance Manager" immediately critiques it, citing a specific risk (e.g., "The market CAGR is too low" or "Initial CAPEX is too high").
    -   The "Sales Manager" critiques the go-to-market strategy.
    -   The debate lasts for at least 3 turns.

### Scenario 2: Proxy Defense
-   **ID**: UAT-C02-02
-   **Priority**: High
-   **Description**: Verify that the "New Employee" agent attempts to defend the idea but acknowledges weaknesses.
-   **Pre-conditions**: Cycle 1 complete.
-   **Steps**:
    1.  Observe the dialogue after the Finance Manager's critique.
-   **Expected Result**:
    -   The New Employee agent replies with a defense (e.g., "But the market is growing...").
    -   The tone is apologetic or nervous (simulating a junior position).

## 2. Behavior Definitions (Gherkin)

```gherkin
Feature: JTC Simulation

  Scenario: Finance Manager critiques a high-cost idea
    GIVEN the selected idea is "VR Headsets for Elderly"
    AND the cost structure is "Hardware intensive"
    WHEN the Finance Manager Agent analyzes the plan
    THEN it should search for "VR hardware market risks"
    AND it should generate a critique mentioning "Inventory risk" or "Unit economics"

  Scenario: Sales Manager critiques a B2B idea
    GIVEN the selected idea is "SaaS for Competitors"
    WHEN the Sales Manager Agent analyzes the plan
    THEN it should generate a critique mentioning "Channel conflict" or "Existing customer trust"
```
