# Cycle 5 User Acceptance Testing (UAT)

## 1. Test Scenarios

### Scenario 1: Feature Pruning & Spec Generation
-   **ID**: UAT-C05-01
-   **Priority**: High
-   **Description**: Verify that the system generates a detailed AgentPromptSpec instead of calling an external UI generation API.
-   **Pre-conditions**: Cycle 4 passed. The Plan has a finalized set of validated assumptions and customer journey.
-   **Steps**:
    1.  Enter the MVP Construction phase.
    2.  System presents the consolidated context (VPC, Mental Model, Journey, Sitemap).
    3.  Trigger generation.
-   **Expected Result**:
    -   System displays: "Successfully generated AgentPromptSpec and ExperimentPlan."
    -   The generated spec contains proper Next.js/React routing constraints and a structured Mermaid flowchart.

### Scenario 2: Experiment Plan Generation
-   **ID**: UAT-C05-02
-   **Priority**: Critical
-   **Description**: Verify that the system outputs a valid Experiment Plan with AARRR metrics targets.
-   **Pre-conditions**: Validated assumptions exist.
-   **Steps**:
    1.  Trigger generation in Builder Agent.
-   **Expected Result**:
    -   System outputs an `ExperimentPlan`.
    -   Plan includes `riskiest_assumption`, `experiment_type`, and at least one `aarrr_metrics` target.

## 2. Behavior Definitions (Gherkin)

```gherkin
Feature: Automated Spec Construction

  Scenario: Generating AI Coder Prompts from a spec
    GIVEN the MVP context contains a Sitemap and User Story
    WHEN the Builder Agent executes spec generation
    THEN the system should output an AgentPromptSpec
    AND the system should output an ExperimentPlan with defined metrics
```
