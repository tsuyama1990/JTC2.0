# Cycle 6 User Acceptance Testing (UAT)

## 1. Test Scenarios

### Scenario 1: Financial Viability Check
-   **ID**: UAT-C06-01
-   **Priority**: High
-   **Description**: Verify that the system flags unviable business models.
-   **Pre-conditions**: Cycle 5 complete.
-   **Steps**:
    1.  Input parameters: High CAC ($500), Low LTV ($100).
    2.  Run Governance check.
-   **Expected Result**:
    -   System warns: "LTV/CAC ratio is 0.2 (Target > 3.0). Business is not viable."
    -   Approval Status: "Rejected".

### Scenario 2: Ringi-sho Generation
-   **ID**: UAT-C06-02
-   **Priority**: Critical
-   **Description**: Verify the generation of the final approval document.
-   **Pre-conditions**: Viable metrics.
-   **Steps**:
    1.  Run Finalization.
-   **Expected Result**:
    -   File `RINGI_SHO.md` is created.
    -   Content includes: "Proposal for [Idea Name]", "Financial Projections", "Nemawashi Result: Approved".

## 2. Behavior Definitions (Gherkin)

```gherkin
Feature: Business Governance

  Scenario: Generating a formal proposal
    GIVEN a validated idea with LTV/CAC > 3
    AND consensus from Key Influencers
    WHEN the Governance Agent runs
    THEN it should produce a document formatted as a standard Japanese Ringi-sho
    AND the document should cite the MVP URL and Interview Evidence
```
