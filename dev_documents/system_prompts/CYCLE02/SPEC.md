# Cycle 02 Specification: The Hell Meeting & Proxy Model

## 1. Summary

Cycle 02 implements the psychological core of "The JTC 2.0": the **Proxy Model** and the **Adversarial Simulation** (affectionately known as the "Hell Meeting"). Having selected a business idea in Cycle 01, the user must now subject it to the harsh reality of corporate scrutiny. However, to preserve the user's psychological safety, this critique is directed at a digital avatar, the `New Employee Agent`, rather than the user themselves.

In this cycle, we introduce the `Department Head Agents`—Finance, Sales, and Compliance. These agents are designed not to be helpful, but to be *realistic blockers*. They will use `Tavily` to find reasons why the idea will fail (competitors, regulations, costs). The `New Employee Agent` must defend the idea.

We also introduce the **Silent CPO Agent**. This agent observes the "battle" in silence (adding to the graph state without emitting messages) and only interacts with the user *after* the meeting in a separate "Informal" subgraph (the "Roof Phase"). This separates the "Performance" from the "Mentoring".

Technically, this involves expanding the `LangGraph` workflow to include multiple nodes, conditional branching (looping until a decision is reached), and integrating a more complex `Pyxel` UI to visualise this RPG-style battle.

## 2. System Architecture

We are expanding the Agent Swarm and the Presentation Layer.

### File Structure
**Bold files** are to be created or modified in this cycle.

```ascii
.
├── src/
│   ├── agents/
│   │   ├── **cpo.py**            # Silent CPO Agent Logic
│   │   └── **opponents.py**      # Dept Head Agents (Finance, Sales, etc.)
│   ├── core/
│   │   ├── **state.py**          # Modified to include 'critiques' and 'feedback'
│   │   └── **graph.py**          # Updated with meeting loops
│   ├── data/
│   │   └── **models.py**         # Added Critique and Dialogue models
│   └── ui/
│       ├── **assets/**           # Images/Sounds for Pyxel
│       ├── **pyxel_app.py**      # The Main Game Loop
│       └── **renderers.py**      # Helper to draw text/agents
└── tests/
    └── **test_opponents.py**
```

### Core Components Blueprints

#### `src/core/state.py` (Extended)
```python
class DialogueLine(BaseModel):
    speaker: str # "Finance", "Sales", "Employee"
    content: str
    emotion: str # "angry", "sad", "neutral" for UI

class AgentState(TypedDict):
    # ... existing fields ...
    # The transcript of the Hell Meeting
    meeting_transcript: List[DialogueLine]
    # The advice given by the CPO
    cpo_advice: str
    # Has the meeting ended?
    meeting_finished: bool
```

#### `src/agents/opponents.py`
```python
def call_finance_agent(state: AgentState):
    """
    Critiques the idea from a ROI/Cost perspective.
    Uses Tavily to find competitor pricing or cost benchmarks.
    """
    idea = state['selected_idea']
    # 1. Search for financial risks
    # 2. Generate biting critique
    return {"meeting_transcript": [DialogueLine(speaker="Finance", content="...", emotion="angry")]}
```

#### `src/agents/cpo.py`
```python
def call_cpo_agent(state: AgentState):
    """
    Analyzes the meeting transcript and provides constructive advice.
    """
    # Analyze the 'meeting_transcript'
    # Identify valid points made by opponents
    # Suggest a Pivot or Defense strategy
    return {"cpo_advice": "..."}
```

#### `src/core/graph.py` (Updated)
```python
workflow = StateGraph(AgentState)
# ... employee node ...
workflow.add_node("finance", call_finance_agent)
workflow.add_node("sales", call_sales_agent)
workflow.add_node("cpo", call_cpo_agent)

# Define the Battle Loop
workflow.add_edge("employee", "finance")
workflow.add_edge("finance", "sales")
workflow.add_edge("sales", "cpo") # In reality, complex logic decides when to stop

app = workflow.compile(interrupt_after=["cpo"])
```

## 3. Design Architecture

### Domain Models (`src/data/models.py`)

1.  **`PersonaProfile`**:
    *   Defines the personality of the opponents.
    *   Fields: `role` (e.g., "Finance Director"), `obsession` (e.g., "ROI"), `voice_style` (e.g., "Sarcastic, Short sentences").
    *   **Why**: To ensure consistent role-playing across different LLM calls.

2.  **`Critique` Schema**:
    *   Structured output for opponents.
    *   Fields: `argument` (text), `evidence` (URL from Tavily), `severity` (1-10), `category` (Financial, Legal, Market).
    *   **Why**: To allow the CPO agent to weigh the arguments mathematically later (DeGroot model).

### The "De-identification" Pattern
The design explicitly separates the **User** from the **Idea**.
*   The User inputs the idea, but the **Employee Agent** defends it.
*   The UI displays the Employee Agent as a pixel-art character (e.g., a sweating salaryman).
*   The User is an observer (The Camera).
*   **Invariant**: The Opponent Agents *never* address the User directly ("You"). They always address the Employee Agent ("He", "She", or "Your plan").

### The "Informal/Formal" Split
The architecture models the JTC culture by splitting the graph into two subgraphs (conceptually):
1.  **Formal Graph (Meeting Room)**: High tension, public critique, state updates are appended to `meeting_transcript`.
2.  **Informal Graph (Roof/Smoking Area)**: Low tension, private mentoring, state updates `cpo_advice`.
This transition is managed by the `LangGraph` conditional edges.

## 4. Implementation Approach

### Step 1: Agent Personas
1.  Create `src/agents/opponents.py`.
2.  Define the system prompts for "Finance Director" (The Penny Pincher) and "Sales Manager" (The Cannibalism Fear-monger).
3.  Implement tool use: They must search before speaking.
4.  **Verification**: Write a script that feeds a `LeanCanvas` to the Finance Agent and prints the critique. Ensure it references real-world competitors (via Tavily).

### Step 2: The Battle Loop (Graph)
1.  Update `src/core/graph.py`.
2.  Define the sequence: `Employee Presentation` -> `Finance Critique` -> `Employee Defense` -> `Sales Critique` -> `Employee Defense`.
3.  (For Cycle 02, we can keep it linear to avoid infinite loops, or use a `loop_count` in state).
4.  **Verification**: Run the graph via CLI. Check if the `meeting_transcript` grows with each step.

### Step 3: The Silent CPO
1.  Create `src/agents/cpo.py`.
2.  The prompt should be: "You are a wise mentor. Read the transcript. Do not solve the problem, but point out the *valid* risks raised by Finance/Sales and suggest a direction."
3.  **Verification**: Check if the advice is actually relevant to the transcript.

### Step 4: Pyxel UI Integration
1.  Install `pyxel`.
2.  Create `src/ui/pyxel_app.py`.
3.  Implement a basic loop:
    *   `update()`: Polls the `app.stream()` generator.
    *   `draw()`: Draws the background (Meeting Room) and text bubbles.
4.  Load basic assets (placeholder rectangles are fine for now, or generated pixel art).
5.  **Verification**: Run `python src/ui/pyxel_app.py`. Ensure the window opens and text appears sequentially.

## 5. Test Strategy

### Unit Testing Approach (Min 300 words)
*   **Persona Consistency**: We will test if the `Finance Agent` consistently outputs "Financial" category critiques.
    *   *Test*: Feed a generic plan. Assert `critique.category == "Financial"`.
*   **State Immutability**: We will ensure that agents do not overwrite previous history.
    *   *Test*: Create a state with 3 messages. Run an agent. Assert state now has 4 messages, and the first 3 are identical.
*   **UI Render Logic**: Although testing graphics is hard, we can test the `TextWrapper` logic.
    *   *Test*: Pass a long string to the text wrapper. Assert it splits into lines of max 40 chars. This is crucial for the limited resolution of Pyxel (Retro UI).

### Integration Testing Approach (Min 300 words)
*   **The "Hell Meeting" Simulation**: We will script a full run of the meeting.
    *   *Input*: A `LeanCanvas` for "Uber for Cats".
    *   *Expectation*:
        *   Finance Agent finds pet transport regulations or costs.
        *   Sales Agent complains about niche market size.
        *   Employee Agent tries to pivot.
        *   CPO Agent summarizes the chaos.
    *   *Verification*: We will use an LLM-based evaluator (Judge) to read the final transcript and rate it for "Realism" and "Conflict Level". If the agents are too nice, the test fails.
*   **Graph State Transitions**:
    *   We will verify that the graph transitions from `meeting` node to `cpo` node only after the loop completes.
    *   We will verify that the `interrupt` happens exactly after the CPO speaks, waiting for the user's next move (which will be Cycle 03).
