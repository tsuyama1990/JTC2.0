# Cycle 05 UAT: MVP Generation (v0.dev) & Product-Market Fit

## 1. Test Scenarios

These scenarios are designed to validate the "Build-Measure-Learn" loop. The core value here is **Speed**. The user should feel that they have gone from a "Rough Idea" to a "Functional Prototype" in minutes, not months.

### Scenario ID: UAT-C05-01 - Automated MVP Generation (Build Phase)
**Priority**: High
**Description**:
The user has passed the "Nemawashi" (Consensus) phase with a specific "One Feature" solution (e.g., "AI-powered Gardening Assistant - Plant Identifier").
The system must now construct a prompt for v0.dev that accurately reflects this feature, its target audience ("Elderly Gardeners"), and the style ("Simple, High Contrast").
Ideally, the generated UI should have:
*   A clear Header.
*   A functional-looking "Upload Photo" button.
*   A placeholder result area ("This is a Rose").

**Marimo Implementation Plan**:
1.  **Setup Cell**: Initialize state with `solution_scope` = "Plant Identifier App".
2.  **Builder Cell**: Run the `Builder Agent` to generate the v0 prompt.
3.  **API Cell**: Call `v0_client.generate_ui(prompt)`. (Use Mock mode if no API key).
4.  **Display Cell**: Render the returned URL in an iframe (or link).
5.  **Validation Cell**: User manually inspects the UI (or we check for key HTML elements if we parse the response).

**Evaluation Criteria**:
1.  **Relevance**: Does the generated UI actually look like a Plant Identifier? Or is it a generic landing page?
2.  **Completeness**: Does it include the specific requirements from the Empathy Map (e.g., "Large Buttons for elderly")?
3.  **Speed**: Does the generation happen within a reasonable timeout (e.g., < 60s)?
4.  **Stability**: Does the system handle API errors gracefully (e.g., retry logic)?

### Scenario ID: UAT-C05-02 - The Pivot Decision (Learn Phase)
**Priority**: Medium
**Description**:
This scenario tests the system's ability to guide the user through failure.
We simulate a "Bad Launch". The Metrics Engine generates a Retention Curve that drops to 0% after Day 1.
The Dashboard displays this grim reality.
The user is presented with 4 choices:
1.  **Zoom-in Pivot**: Focus on a single feature of the MVP.
2.  **Zoom-out Pivot**: Expand the scope.
3.  **Customer Segment Pivot**: Target a different audience.
4.  **Persevere**: Keep optimizing (burns more budget).

The user selects "Customer Segment Pivot" (e.g., from "Elderly" to "Professional Landscapers"). The system must **Reset the State** correctly:
*   Keep the Solution (Plant ID).
*   Clear the Empathy Map (since the customer changed).
*   Clear the Consensus (need to lobby again for the new target).
*   Return the workflow to **Cycle 03 (Customer Discovery)**.

**Marimo Implementation Plan**:
1.  **Setup Cell**: Initialize state with `metrics` showing 0% retention.
2.  **Dashboard Cell**: Render the chart.
3.  **Input Cell**: User selects "Customer Segment Pivot".
4.  **Transition Cell**: Run the graph transition logic.
5.  **Validation Cell**: Assert `state['current_stage'] == 'GATE_2'` and `state['empathy_map']` is Empty.

**Evaluation Criteria**:
1.  **Logic Correctness**: Did the state reset to the correct phase?
2.  **Data Hygiene**: Did we clear the invalid data (old customer interviews) while keeping valid data (the tech stack)?
3.  **Guidance**: Did the system explain *why* a pivot was necessary based on the data?

## 2. Behavior Definitions

We use Gherkin syntax to define the expected behavior of the system features.

### Feature: MVP Construction
**As a** Non-Technical Founder
**I want** to see my idea as a real web page
**So that** I can show it to customers and get feedback.

**Scenario: Generating a UI from Requirements**
  **Given** the "Builder Agent" has a list of requirements: ["Login", "Dashboard", "Settings"]
  **And** the style guide is "Modern, Dark Mode"
  **When** the agent calls the v0 API
  **Then** the prompt sent to v0 should contain "Create a Modern, Dark Mode React app with Login, Dashboard, Settings"
  **And** the API should return a valid URL (e.g., `https://v0.dev/r/xyz123`)
  **And** the system should store this URL in `state['mvp_url']`.

**Scenario: Handling API Failures**
  **Given** the v0 API is down (returns 500)
  **When** the agent attempts generation
  **Then** the system should retry up to 3 times with exponential backoff
  **And** if it still fails, it should fallback to a "Wireframe Mode" (ASCII art or placeholder image)
  **And** notify the user "Could not generate live UI, showing wireframe instead."

### Feature: Metrics Simulation (AARRR)
**As a** Data Analyst
**I want** realistic usage data
**So that** I can make informed decisions.

**Scenario: Strong Product-Market Fit**
  **Given** the Idea Score is 0.9 (High Validation)
  **And** the Execution Score is 0.8 (High Consensus)
  **When** the Metrics Engine runs for "Day 7"
  **Then** the Retention Rate should be $> 40\%$
  **And** the Revenue should be positive.

**Scenario: Weak Product-Market Fit**
  **Given** the Idea Score is 0.3 (Low Validation)
  **When** the Metrics Engine runs
  **Then** the Retention Rate should drop to $< 10\%$ by Day 3
  **And** the Churn Rate should be high.

### Feature: Pivot Logic (State Transition)
**As a** System Architect
**I want** the Pivot action to reliably transform the graph state
**So that** the simulation remains consistent.

**Scenario: Executing a Zoom-In Pivot**
  **Given** the current feature is "Complex ERP System"
  **And** the user selects "Zoom-In Pivot" to focus on "Just the Invoicing Module"
  **When** the transition occurs
  **Then** the `solution_scope` should update to "Invoicing Module"
  **And** the workflow should jump back to **Cycle 04 (Solution Fit)**
  **But** it should NOT jump back to Cycle 01 (Idea Gen), as the core idea is preserved.
