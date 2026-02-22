# Cycle 05 Specification: MVP Generation (v0.dev) & Product-Market Fit

## 1. Summary

Cycle 05 is the final frontier of "The JTC 2.0". After navigating the political labyrinth (Cycle 04), the user has secured "Budget Approval". Now, they must "Build and Sell".

This cycle automates the creation of a tangible **Minimum Viable Product (MVP)**. Instead of months of development, we use the `v0.dev` API (by Vercel) to generate a high-fidelity React/Tailwind UI based on the "One Feature" selected in Cycle 03/04. This allows the user to click a link and see their idea come to life instantly.

However, launch is not the end. The system then simulates the **Product-Market Fit (PMF)** phase using the AARRR (Acquisition, Activation, Retention, Referral, Revenue) framework. The system generates simulated user data (based on the quality of the initial idea and the Empathy Map match) and populates a dashboard.

The simulation pauses at **Gate 4 (PMF Check)**. The user is presented with a "Retention Curve". If it flatlines, they have PMF. If it trends to zero, they must decide: **Pivot** (Return to Cycle 01/03) or **Persevere** (Optimize). This decision loop completes the "Lean Startup" methodology.

## 2. System Architecture

We are adding the Execution Layer (v0.dev) and the Metrics Engine.

### File Structure
**Bold files** are to be created or modified in this cycle.

```ascii
.
├── src/
│   ├── agents/
│   │   ├── **growth_hacker.py**  # Agent to interpret metrics
│   │   └── **builder.py**        # Agent to prompt v0.dev
│   ├── core/
│   │   ├── **state.py**          # Added 'mvp_url', 'metrics_data'
│   │   └── graph.py              # New nodes: 'build_mvp', 'measure_metrics'
│   ├── data/
│   │   └── **metrics_engine.py** # Logic to simulate AARRR data
│   ├── tools/
│   │   └── **v0_client.py**      # Wrapper for v0.dev API
│   └── ui/
│       └── **dashboard.py**      # Visualization of the AARRR funnel
└── tests/
    ├── **test_v0_client.py**
    └── **test_metrics.py**
```

### Core Components Blueprints

#### `src/tools/v0_client.py`
```python
def generate_ui(prompt: str) -> str:
    """
    Calls v0.dev API to generate a UI.
    Returns the URL of the generated component.
    """
    # 1. Construct payload with system prompt "You are an expert React dev..."
    # 2. Call API
    # 3. Poll for completion
    # 4. Return URL
    return "https://v0.dev/..."
```

#### `src/data/metrics_engine.py`
```python
def simulate_launch_week(idea_score: float, execution_score: float) -> AARRRMetrics:
    """
    Generates synthetic data based on the quality of the idea.
    """
    acquisition = 1000
    activation_rate = 0.1 * idea_score # Better ideas activate more users
    retention_curve = [100, 50, 40, 35, 34, 34] # Flatline = Good
    if idea_score < 0.5:
        retention_curve = [100, 20, 5, 1, 0, 0] # Churn = Bad

    return AARRRMetrics(...)
```

#### `src/core/state.py` (Extended)
```python
class AARRRMetrics(BaseModel):
    daily_active_users: List[int]
    retention_cohorts: List[List[float]]
    revenue: float

class AgentState(TypedDict):
    # ...
    mvp_url: str
    metrics: AARRRMetrics
    pmf_status: str # "searching", "found", "failed"
```

## 3. Design Architecture

### Domain Models

1.  **`MVPRequest`**:
    *   Constructed by the `Builder Agent`.
    *   Fields: `component_name`, `requirements` (List[str]), `style_guide` (e.g., "Corporate, Blue").
    *   **Transformation**: The agent reads the `LeanCanvas` and `EmpathyMap` to write detailed requirements (e.g., "Must have a signup form for Dentists").

2.  **`PivotDecision`**:
    *   The User's final choice.
    *   Enum: `ZOOM_IN`, `ZOOM_OUT`, `CUSTOMER_SEGMENT_SHIFT`, `PERSEVERE`.
    *   **Logic**: Each choice triggers a specific rollback in the Graph (e.g., Zoom In -> Go to Cycle 03 but keep the feature).

### The "Simulation of Reality"
We cannot actually launch the product to real users in 5 minutes. Therefore, the **Metrics Engine** is a critical component. It must be deterministic but complex enough to be convincing.
*   **Formula**: $Retention = f(Problem\_Severity \times Solution\_Fit)$.
*   If `riskiest_assumption` was validated with strong quotes, Retention should be high.
*   If the consensus in Cycle 04 was weak ($0.71$), the Execution Score is low, lowering Activation.

## 4. Implementation Approach

### Step 1: v0.dev Client
1.  Obtain v0 API Key (Mock it for now, or use real one if available).
2.  Implement `src/tools/v0_client.py`.
3.  Implement robust error handling (timeouts, 429s).
4.  **Verification**: Write a script that calls the API (or a mock) and asserts it returns a URL string starting with `https://v0.dev`.

### Step 2: The Builder Agent
1.  Create `src/agents/builder.py`.
2.  Prompt Engineering: "Translate this Lean Canvas into a single-page React App description."
3.  It should focus on the "One Feature" locked in Cycle 04.
4.  **Verification**: Feed it a "Dog Walking" canvas. Assert the output prompt mentions "Map", "Booking Button", etc.

### Step 3: Metrics Engine
1.  Implement `src/data/metrics_engine.py`.
2.  Implement the "Retention Curve Generator".
3.  **Verification**: Test with `score=0.9` (Expect flat curve). Test with `score=0.1` (Expect drop to zero).

### Step 4: Gate 4 (The Dashboard)
1.  Update `src/ui/dashboard.py` (CLI or Pyxel).
2.  Display the `mvp_url` (Clickable if possible).
3.  Render the Retention Curve (ASCII chart or Pyxel graph).
4.  Ask User: "Pivot or Persevere?"

## 5. Test Strategy

### Unit Testing Approach (Min 300 words)
*   **Metrics Logic**:
    *   *Test*: Ensure that `simulate_launch_week` never returns negative users.
    *   *Test*: Ensure that `revenue` calculation matches `active_users * price`.
*   **v0 Payload Construction**:
    *   *Test*: The API requires specific JSON structure. We will test that `v0_client` builds this correctly, escaping quotes in the prompt string.
*   **State Updates**:
    *   *Test*: When `metrics` are generated, they should be appended to the state, not overwriting history (if we track weekly).

### Integration Testing Approach (Min 300 words)
*   **Prompt-to-Code Pipeline**:
    *   *Scenario*: User Idea -> Builder Agent -> Prompt -> v0 Client.
    *   *Verification*: We can't verify the *visual quality* of the generated UI automatically, but we can verify that the *prompt* sent to v0 contains the key keywords from the User's Idea.
*   **The Pivot Loop**:
    *   *Scenario*:
        1.  Metrics show failure (Retention = 0).
        2.  User selects "Pivot: Customer Segment Shift".
        3.  System should transition state back to **Cycle 01/03**.
        4.  System should clear `interview_transcripts` (since we have a new segment).
        5.  System should preserve `financial_budget` (minus the cost of the failed launch).
    *   *Verification*: Check `AgentState` before and after the transition.
*   **Mock Mode vs Real Mode**:
    *   The system must support running without a real v0 API key for CI/CD.
    *   *Test*: Set `MOCK_V0=true`. Run pipeline. Assert `mvp_url` is a dummy placeholder `https://v0.dev/mock-id`.
