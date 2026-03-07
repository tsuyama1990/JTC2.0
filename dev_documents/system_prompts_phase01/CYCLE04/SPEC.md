# Cycle 4 Specification: Consensus Building (Nemawashi)

## 1. Summary

The primary objective of **Cycle 4** is to simulate the invisible layer of organizational politics using the **French-DeGroot Model** of opinion dynamics. This cycle introduces the **"Nemawashi" (Root-binding)** process, which is critical for success in JTCs.

The system will model the influence network between agents (Finance, Sales, CPO, CEO). By calculating how opinions propagate through this weighted network, the system can generate a strategic "Nemawashi Map" for the user, advising them on who to approach first to build consensus before the final decision. We also simulate "Nomikai" (Drinking Parties) where social barriers lower and influence weights shift.

## 2. System Architecture

### 2.1. File Structure

This cycle adds the Math/Logic Layer. **Bold** files are new or modified.

```ascii
.
├── dev_documents/
├── src/
│   ├── core/
│   │   ├── ...
│   │   └── **nemawashi.py**    # French-DeGroot Logic
│   ├── domain/
│   │   ├── **__init__.py**
│   │   └── **politics.py**     # Influence Matrix Models
│   └── ui/
│       └── **nemawashi_view.py** # Visualization of the network
```

### 2.2. Component Interaction

1.  **GlobalState** maintains an `OpinionVector` (Initial buy-in of each stakeholder).
2.  **GlobalState** maintains an `InfluenceMatrix` (Who listens to whom).
3.  **Nemawashi Engine** runs the DeGroot update rule: $x(t+1) = W \cdot x(t)$ until convergence or $t=10$.
4.  **Nomikai Simulation** temporarily alters $W$ (increasing specific $w_{ij}$) and re-runs the simulation to see if consensus improves.
5.  **Output**: A list of "Key Influencers" to target.

## 3. Design Architecture

### 3.1. Mathematical Model (`src/core/nemawashi.py`)

-   **Opinion Vector ($x$)**: An array where $x_i \in [0, 1]$ represents agent $i$'s support for the project.
-   **Influence Matrix ($W$)**: A row-stochastic matrix where $w_{ij}$ is the weight agent $i$ places on agent $j$'s opinion.
-   **Self-Confidence ($w_{ii}$)**: How stubborn an agent is. High for Finance, low for New Employee.

### 3.2. Data Models (`src/domain/politics.py`)

```python
import numpy as np
from pydantic import BaseModel, ConfigDict

class Stakeholder(BaseModel):
    name: str
    initial_support: float  # 0.0 to 1.0
    stubbornness: float    # Self-weight

class InfluenceNetwork(BaseModel):
    stakeholders: List[Stakeholder]
    matrix: List[List[float]]  # W

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def update_opinions(self, steps: int = 5) -> List[float]:
        # Implementation of x(t+1) = Wx(t)
        pass
```

## 4. Implementation Approach

1.  **Math Implementation**: Implement the DeGroot model using `numpy` in `src/core/nemawashi.py`.
2.  **Agent Integration**: Assign initial $x_i$ values based on the sentiment analysis from Cycle 2 (e.g., if Finance was angry, $x_{Finance} = 0.1$).
3.  **Network Definition**: Define a standard "JTC Topology" (CEO listens to Finance, Sales listens to CEO, everyone ignores New Employee).
4.  **Nomikai Logic**: Implement a function `hold_nomikai(target: Agent)` that increases $w_{target, user}$ and decreases $w_{target, target}$ (lowered inhibitions).
5.  **Visualization**: Simple text-based heatmap or graph output.

## 5. Test Strategy

### 5.1. Unit Testing
-   **File**: `tests/test_nemawashi.py`
-   **Scope**:
    -   Verify matrix multiplication logic.
    -   Verify that opinions converge to a consensus value (or loop).
    -   Verify that "Stubborn Agents" (high diagonal values) slow down convergence.

### 5.2. Integration Testing
-   **Scope**:
    -   Run a simulation where Finance hates the idea (0.1) but the CEO loves it (0.9).
    -   If Finance listens to CEO (high weight), Finance's opinion should improve over time.
    -   Verify that the "Nomikai" action successfully shifts the final consensus score.
