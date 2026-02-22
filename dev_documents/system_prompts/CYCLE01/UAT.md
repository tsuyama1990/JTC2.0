# Cycle 01 UAT: Idea Verification

## 1. Test Scenarios

These scenarios are designed to ensure that the "Idea Verification" phase functions as intended, providing value to the user while adhering to the rigorous constraints of the "Science of Entrepreneurship". We focus on the user experience of generating and selecting business ideas.

### Scenario ID: UAT-C01-01 - 10 Lean Canvas Generation & Selection
**Priority**: High
**Description**:
This scenario validates the core value proposition of Cycle 01: The ability of the system to act as a competent brainstorming partner. The user inputs a broad, perhaps vague, interest (e.g., "Silver Tech" or "EdTech for Kids"), and the system must return 10 distinct, structured, and plausible business ideas formatted as Lean Canvases.

The critical success factor here is "Distinctness" and "Structure".
*   **Distinctness**: The 10 ideas should not be 10 variations of the same app. They should explore different angles (B2B vs B2C, different pain points).
*   **Structure**: Each idea must have a clear `Problem`, `Solution`, `Customer Segment`, and `Unique Value Proposition`.

**Marimo Implementation Plan**:
We will create a Marimo notebook `tutorials/UAT_AND_TUTORIAL.py` (which will evolve).
1.  **Input Cell**: A text area for `topic`.
2.  **Execution Cell**: Calls the `graph.invoke()` method.
3.  **Output Cell**: Renders the 10 ideas in a nice Markdown table or card layout.
4.  **Selection Cell**: A dropdown or radio button list to select one idea.
5.  **Validation Cell**: Asserts that the selected idea is stored in `AgentState`.

**Evaluation Criteria**:
1.  **Relevance**: Are the ideas actually about the input topic? (AI-graded).
2.  **Completeness**: Do all 10 ideas have all required fields filled? (Code-graded).
3.  **Speed**: Does the generation happen within a reasonable time (e.g., < 30 seconds)?
4.  **Error Handling**: If Tavily returns no results, does the agent hallucinate or gracefully degrade (e.g., use internal knowledge)?

### Scenario ID: UAT-C01-02 - State Persistence & Interrupt Logic
**Priority**: Medium
**Description**:
This scenario tests the robustness of the LangGraph state machine. In a real-world usage of "The JTC 2.0", a user might generate ideas on Friday, close the application, and come back on Monday to select one. The system must support this asynchronous workflow.

Although Cycle 01 is a CLI/Script, we must verify that the `compiled_graph` correctly pauses execution after the `employee` node. We need to verify that the state (the 10 ideas) is preserved in the `checkpointer` (in-memory for now, but architecturally ready for persistence).

**Marimo Implementation Plan**:
1.  **Step 1**: Run the graph up to the interrupt.
2.  **Step 2**: Inspect the `graph.get_state(thread_id)` object. Print the `next` node. It should be empty or waiting for user input.
3.  **Step 3**: Simulate a user selection by updating the state with `graph.update_state(thread_id, {"selected_idea": ...})`.
4.  **Step 4**: Resume the graph (if applicable in future cycles).

**Evaluation Criteria**:
1.  **Interrupt Success**: The graph must strictly stop after generating ideas. It should not proceed to any "Critique" or "Interview" phase (which don't exist yet, but the logic must hold).
2.  **Data Integrity**: The `ideas` list must be identical before and after the pause. No data loss.
3.  **Thread Isolation**: If we run two different threads (Topic A and Topic B), their states must not mix.

## 2. Behavior Definitions

We use Gherkin syntax to define the expected behavior of the system features. This serves as a contract between the Architect and the Developer (me).

### Feature: Idea Generation
**As a** aspiring entrepreneur (User)
**I want** to generate multiple Lean Canvas drafts based on a market area
**So that** I can explore different business models without spending weeks on research.

**Scenario: User requests ideas for a valid topic**
  **Given** the "New Employee Agent" is initialized with access to Tavily and OpenAI
  **And** the user provides the topic "Remote Work Tools for introverts"
  **When** the workflow is executed
  **Then** the agent should perform a Tavily search for "remote work trends 2024" or similar
  **And** the agent should generate exactly 10 `LeanCanvas` objects
  **And** each object should have a non-empty `problem` field
  **And** each object should have a non-empty `customer_segments` field
  **And** the system should pause execution to await user selection.

**Scenario: User provides an empty or gibberish topic**
  **Given** the agent is active
  **When** the user provides the topic "asdfghjkl"
  **Then** the agent should either:
    *   Ask for clarification (if interactive).
    *   Or generate ideas based on a default "General Tech" topic with a warning.
    *   (Ideally, it should gracefully handle the lack of search results).
  **And** the system should not crash.

### Feature: Idea Selection
**As a** user
**I want** to select one "Plan A" from the generated list
**So that** I can focus my validation efforts on the most promising concept.

**Scenario: User selects a valid idea ID**
  **Given** the state contains a list of 10 generated ideas with IDs 0-9
  **When** the user inputs "Select ID 3"
  **Then** the `selected_idea` field in the `AgentState` should be updated with the content of Idea #3
  **And** the other 9 ideas should be retained in `ideas` (for reference) but not active.
  **And** the workflow should be marked as "Gate 1 Passed".

**Scenario: User selects an invalid ID**
  **Given** the list has 10 items
  **When** the user inputs "Select ID 99"
  **Then** the UI should display an error message "Invalid Selection"
  **And** the state should remain unchanged (no `selected_idea` set)
  **And** the system should prompt for selection again.

### Feature: Data Privacy (Internal)
**As a** Corporate Security Officer (simulated)
**I want** to ensure that no proprietary data is leaked
**So that** the system is safe for enterprise use.

**Scenario: Config Validation**
  **Given** the application starts up
  **When** the `config.py` is loaded
  **Then** it should check for the presence of `OPENAI_API_KEY`
  **And** if missing, it should raise a `ValidationError` and stop immediately.
