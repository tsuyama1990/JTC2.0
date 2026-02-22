# Cycle 03 UAT: Primary Info Injection (RAG) & Customer-Problem Fit

## 1. Test Scenarios

These scenarios are designed to validate the system's ability to distinguish between "Assumption" and "Fact". We focus on the *injection of primary data* (interview transcripts) and how the system uses this data to update its world model (Empathy Map).

### Scenario ID: UAT-C03-01 - "The Mom Test" Verification (Riskiest Assumption)
**Priority**: High
**Description**:
This scenario validates the "Gate 2" logic. The user has a hypothesis (e.g., "People want a subscription for socks"). The system identifies the Riskiest Assumption (e.g., "People care enough about socks to subscribe").
The user then conducts a "Mom Test" interview (simulated by uploading a text file). The interview content either *validates* or *invalidates* the assumption. The system must correctly interpret the text and update the `EmpathyMap`.

**Marimo Implementation Plan**:
1.  **Setup Cell**: Initialize state with `riskiest_assumption` = "Customers hate buying socks."
2.  **Upload Cell**: Simulate uploading a file `interview_01.txt` containing: "I love buying socks! It's fun. I don't want a subscription."
3.  **RAG Cell**: Run the `ingest_transcript` function.
4.  **Analysis Cell**: Run the `Analyst Agent`.
5.  **Validation Cell**: Check `state['empathy_map'].pain` and `state['riskiest_assumption_status']`. It should be `INVALIDATED`.

**Evaluation Criteria**:
1.  **Fact Extraction**: Did the system extract "loves buying socks" as a "Gain" or "Positive Sentiment"?
2.  **Logic Reversal**: Did the system correctly flip the assumption from True to False based on the text?
3.  **Citation**: Ideally, the system should quote the exact line ("I love buying socks!") as evidence.

### Scenario ID: UAT-C03-02 - Transcript-Driven Pivot (Opponent Reaction)
**Priority**: Medium
**Description**:
In Cycle 02, the opponents (Finance/Sales) used general market data. In Cycle 03, they must use the specific interview data.
If the user uploads an interview where the customer says "I would pay $100 for this," the Finance Agent—who previously complained about low margins—should change its tune. This tests the RAG integration into the opponent agents.

**Marimo Implementation Plan**:
1.  **Context Cell**: Load a state where Finance Agent says "Pricing is too low at $10."
2.  **Upload Cell**: Upload `interview_02.txt`: "I'd pay $50 easily for this solution."
3.  **Re-Run Cell**: Run the Finance Agent again with the new context.
4.  **Validation Cell**: Check the new critique. It should mention "Customer willingness to pay is higher than expected ($50)."

**Evaluation Criteria**:
1.  **Context Awareness**: The agent must reference the specific dollar amount mentioned in the text.
2.  **Tone Shift**: The agent's tone should shift from "Critical" to "Cautiously Optimistic" (or at least acknowledge the data).
3.  **Persistence**: The knowledge must persist across agent calls (via Vector Store).

## 2. Behavior Definitions

We use Gherkin syntax to define the expected behavior of the system features.

### Feature: RAG Ingestion
**As a** User
**I want** to upload my interview notes/transcripts
**So that** the system builds its strategy on real customer feedback, not hallucinations.

**Scenario: User uploads a valid text file**
  **Given** the system is at "Gate 2" (Customer Discovery)
  **And** the user has a text file `mom_test.txt` with > 100 words of conversation
  **When** the user uploads the file via the UI
  **Then** the system should chunk the text and store it in the local Vector DB
  **And** the system should respond with "Ingestion Complete: 1 Interview Added"
  **And** the `AgentState` should update `has_interviews` to True.

**Scenario: User uploads an irrelevant file**
  **Given** the system is ready
  **When** the user uploads a file containing "Lorem Ipsum" or random code
  **Then** the system should still ingest it (technically)
  **But** the `Analyst Agent` should flag it as "Low Information Density" or "No clear insights found"
  **And** the `EmpathyMap` should remain largely empty.

### Feature: Empathy Map Generation
**As a** Product Manager (User)
**I want** an automatically generated Empathy Map
**So that** I can visualize the customer's pains and gains.

**Scenario: Generating map from negative feedback**
  **Given** the Vector DB contains an interview where the customer complains about "Slow service" and "Rude staff"
  **When** the `Analyst Agent` runs
  **Then** the `EmpathyMap.pain` list should contain "Slow service" and "Rude staff"
  **And** the `EmpathyMap.feels` list should contain "Frustrated" or "Angry".

**Scenario: Generating map from positive feedback**
  **Given** the Vector DB contains an interview where the customer praises "Easy to use interface"
  **When** the `Analyst Agent` runs
  **Then** the `EmpathyMap.gain` list should contain "Easy Interface"
  **And** the `EmpathyMap.thinks` list should contain "This solves my problem."

### Feature: Gate 2 Validation (The Pivot)
**As a** Startup Founder
**I want** the system to tell me if my idea is dead
**So that** I don't waste time building a product nobody wants.

**Scenario: Assumption Invalidated (Pivot Required)**
  **Given** the `riskiest_assumption` is "Customers have a budget for this"
  **And** the ingested interviews consistently show "We have no budget"
  **When** the Gate 2 Logic runs
  **Then** the system should set `validation_status` to "FAILED"
  **And** the UI should display a "PIVOT REQUIRED" alert
  **And** the workflow should offer to return to Cycle 01 (Idea Gen) or modify the Business Model (e.g., Freemium).

**Scenario: Assumption Validated (Proceed)**
  **Given** the `riskiest_assumption` is "Customers struggle with X"
  **And** the interviews confirm "X is a huge pain"
  **When** the Gate 2 Logic runs
  **Then** the system should set `validation_status` to "PASSED"
  **And** the UI should unlock the "Solution Design" phase (Cycle 04).
