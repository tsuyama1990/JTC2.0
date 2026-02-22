# Cycle 04 Specification: Nemawashi & Consensus Dynamics (French-DeGroot Model)

## 1. Summary

Cycle 04 introduces the most unique feature of The JTC 2.0: the **Mathematical Simulation of Corporate Politics**. In a startup, a CEO can just say "Do it." In a JTC, nothing happens without "Nemawashi" (groundwork/lobbying).

We model this using the **French-DeGroot Model** of Opinion Dynamics. This model treats the organization as a graph of agents where each agent has an opinion ($x_i$, range 0-1) and a trust matrix ($W$, where $w_{ij}$ is how much agent $i$ trusts agent $j$).

In this cycle, we implement **Gate 3 (Problem-Solution Fit)**. The user must refine their solution to a "One Feature MVP". However, the "Department Heads" (Finance, Sales, Compliance) start with low opinions of the new plan. The user cannot force them; they must use the "Silent CPO" to lobby them.

The simulation runs in rounds. In each round (simulating a meeting or "Nomikai"), agents update their opinions based on the weighted average of their neighbours. The user wins if the consensus opinion crosses a threshold (e.g., 0.7) before time (budget) runs out.

## 2. System Architecture

We are adding the Simulation Layer (NumPy/NetworkX) to the stack.

### File Structure
**Bold files** are to be created or modified in this cycle.

```ascii
.
├── src/
│   ├── agents/
│   │   ├── **lobbyist.py**       # Logic for CPO lobbying actions
│   │   └── opponents.py          # Added 'opinion_score' field
│   ├── core/
│   │   ├── **state.py**          # Added 'consensus_matrix', 'current_opinions'
│   │   └── graph.py              # New subgraph: 'nemawashi_loop'
│   ├── simulation/
│   │   ├── **__init__.py**
│   │   └── **degroot.py**        # The Math Engine
│   └── ui/
│       └── **network_viz.py**    # Pyxel/Matplotlib visualization of the graph
└── tests/
    └── **test_degroot.py**
```

### Core Components Blueprints

#### `src/simulation/degroot.py`
```python
import numpy as np

def run_degroot_step(opinions: np.ndarray, trust_matrix: np.ndarray) -> np.ndarray:
    """
    Update opinions: x(t+1) = W * x(t)
    """
    return np.dot(trust_matrix, opinions)

def calculate_consensus(opinions: np.ndarray) -> float:
    return np.mean(opinions)
```

#### `src/core/state.py` (Extended)
```python
class AgentOpinion(TypedDict):
    agent_name: str
    score: float # 0.0 to 1.0
    self_confidence: float # w_ii

class AgentState(TypedDict):
    # ...
    # The current scalar opinion of each agent
    opinions: Dict[str, float]
    # The Trust Matrix (adjacency list representation)
    trust_network: Dict[str, Dict[str, float]]
    # Has the "One Feature" been locked?
    feature_locked: bool
```

## 3. Design Architecture

### Domain Models

1.  **`TrustMatrix`**:
    *   A square matrix where rows/cols are agents (Employee, Finance, Sales, Compliance, CPO).
    *   **Invariant**: Rows must sum to 1.0 (Stochastic Matrix).
    *   **Dynamics**:
        *   **High Self-Confidence ($w_{ii}$)**: Stubborn agent (Department Head).
        *   **High Trust in Others ($w_{ij}$)**: Impressionable agent.

2.  **`LobbyingAction`**:
    *   The User/CPO chooses an action to perturb the matrix or opinions.
    *   *Examples*:
        *   "Show Data to Finance" -> Increases Finance's opinion ($x_{finance}$).
        *   "Drink with Sales" -> Increases Sales' trust in Employee ($w_{sales, employee}$).

### The "Nemawashi" Game Loop
1.  **State Init**: Agents start with low opinions ($0.2$) based on the "Hell Meeting" history.
2.  **User Turn**: User selects an action via CPO (costing "Political Capital").
3.  **Matrix Update**: The action modifies $W$ or $x$.
4.  **Simulation Step**: Run $x(t+1) = Wx(t)$.
5.  **Check Condition**: If Mean($x$) > $0.7$, Gate Passed.

## 4. Implementation Approach

### Step 1: The Math Engine
1.  Implement `src/simulation/degroot.py`.
2.  Use `numpy` for efficient matrix multiplication.
3.  Implement validation logic to ensure the matrix remains stochastic (rows sum to 1).
4.  **Verification**: Unit test with a $2 \times 2$ matrix. Hand-calculate the result and compare.

### Step 2: Integrating Opinions into Agents
1.  Update `AgentState` to track opinions.
2.  Update `opponents.py`: The text output should reflect the score.
    *   Score < 0.3: "This is garbage."
    *   Score > 0.7: "I'm on board."
3.  **Verification**: Manually set Finance opinion to 0.9 and run the agent. Check text output.

### Step 3: The Lobbying Actions
1.  Create `src/agents/lobbyist.py`.
2.  Define a set of tools/actions available to the CPO.
    *   `provide_evidence(target, evidence_strength)`
    *   `socialize(target, intensity)`
3.  Implement the logic: These actions output a "Matrix Update Delta" or "Opinion Delta".
4.  **Verification**: Call `socialize("Finance")` and check if $w_{finance, employee}$ increases.

### Step 4: Gate 3 (One Feature)
1.  Before the simulation starts, force the user to select "One Feature" from the solution list.
2.  This selection resets the opinions (new idea = new skepticism).
3.  The simulation runs until consensus or "Game Over" (ran out of turns).

## 5. Test Strategy

### Unit Testing Approach (Min 300 words)
*   **Mathematical Correctness**:
    *   *Test*: Identity Matrix. If $W = I$, opinions should never change.
    *   *Test*: Consensus Convergence. If the graph is strongly connected and aperiodic, opinions should converge to a stable value. We will assert `np.allclose`.
*   **Matrix Constraints**:
    *   *Test*: Verify that after every update (e.g., "socialize"), the row normalization function is called so $\sum w_{ij} = 1$. Failure to do this causes exploding/vanishing opinions.
*   **Action Logic**:
    *   *Test*: `provide_evidence` should increase opinion score but *decrease* self-confidence ($w_{ii}$), making the agent more open to influence.

### Integration Testing Approach (Min 300 words)
*   **The "Nemawashi" Simulation**:
    *   *Scenario*:
        *   Finance Hates the project ($0.1$). Sales Loves it ($0.9$).
        *   Finance trusts Sales ($0.5$).
        *   After 1 step, Finance's opinion should rise significantly because they listen to Sales.
    *   *Verification*: Run the `run_degroot_step` function and check values.
*   **End-to-End Gate 3**:
    *   *Scenario*: User enters Gate 3. Selects "Feature A". CPO advises "Talk to Finance". User clicks "Talk to Finance".
    *   *Expectation*:
        1.  Finance Opinion $\uparrow$.
        2.  Next Round: Finance spreads positive opinion to Compliance.
        3.  Consensus Reached.
    *   *Verification*: Trace the `AgentState` history to ensure the causal chain holds.
*   **Game Balance**:
    *   *Manual Playtest*: Is it impossible to win? Is it too easy? We need to tune the "Cost" of actions vs the "Impact" on the matrix. (This is soft verification).
