# Cycle 04 UAT: Nemawashi & Consensus Dynamics (French-DeGroot Model)

## 1. Test Scenarios

These scenarios are designed to validate the *math-as-gameplay* mechanics. The core hypothesis of Cycle 04 is that by mathematically modeling influence ($w_{ij}$), we can create a realistic simulation of office politics.

### Scenario ID: UAT-C04-01 - Consensus Convergence (Winning the Game)
**Priority**: High
**Description**:
The user starts with a "Solution" (e.g., "Feature A") that has low buy-in from the department heads.
*   **Initial State**:
    *   Finance Opinion: $0.2$ (Hates it)
    *   Sales Opinion: $0.4$ (Skeptical)
    *   Compliance Opinion: $0.1$ (Blocks it)
    *   User (Employee) Opinion: $1.0$ (Loves it)
The user must choose a sequence of "Lobbying Actions" (via CPO) to influence the network.
*   **Action**: "Drink with Sales" (Increase Trust $w_{Sales, Employee}$).
*   **Result**: Sales' opinion rises in the next round because they weigh the Employee's opinion higher.
*   **Ripple Effect**: Finance trusts Sales ($w_{Finance, Sales} = 0.6$). So in the *following* round, Finance's opinion rises because Sales is now positive.

**Marimo Implementation Plan**:
1.  **Setup Cell**: Initialize a $4 \times 4$ Trust Matrix with specific values.
2.  **Visualization Cell**: Display a Network Graph (nodes = agents, edges = trust).
3.  **Action Cell**: Dropdown to select "Lobby [Target]".
4.  **Simulation Cell**: Run `step()` and update the graph.
5.  **Validation Cell**: Plot the opinion trends over time. Verify they converge to $> 0.7$.

**Evaluation Criteria**:
1.  **Causality**: Did the opinion change *because* of the specific link I strengthened?
2.  **Feedback**: Did the system explain *why* opinion changed? (e.g., "Finance listened to Sales").
3.  **Victory Condition**: Did the gate unlock exactly when Mean Opinion > Threshold?

### Scenario ID: UAT-C04-02 - The "Echo Chamber" Failure (Losing the Game)
**Priority**: Medium
**Description**:
This scenario tests the *failure condition*. If the department heads have high trust in each other but low trust in the Employee (a "Clique"), and they all start negative, the Employee's opinion ($1.0$) should not be enough to sway them.
The user should try to lobby, but if they pick the wrong targets (e.g., trying to convince the stubborn Compliance officer directly instead of using an influencer), the opinions should converge to $0.0$ (Rejection).

**Marimo Implementation Plan**:
1.  **Setup Cell**: Initialize a "Clique" matrix (strong internal links, weak external links).
2.  **Action Cell**: User performs "Direct Pitch" (weak effect on clique).
3.  **Simulation Cell**: Run 5 rounds.
4.  **Validation Cell**: Assert that Mean Opinion remains $< 0.3$.

**Evaluation Criteria**:
1.  **Resistance**: The network should resist change if trust is low.
2.  **Game Over**: The system should correctly trigger a "Proposal Rejected" state.
3.  **Analysis**: The CPO should explain *why* it failed (e.g., "You didn't build enough trust with the influencer first").

## 2. Behavior Definitions

We use Gherkin syntax to define the expected behavior of the system features.

### Feature: Influence Matrix Dynamics
**As a** Player (User)
**I want** my actions to change the hidden relationships between agents
**So that** I can engineer a consensus.

**Scenario: Increasing Trust via Socializing**
  **Given** the "Sales Manager" has a trust score of $0.1$ towards the "Employee"
  **And** the user selects the action "Go for Drinks with Sales"
  **When** the turn is processed
  **Then** the trust score $w_{Sales, Employee}$ should increase by a significant delta (e.g., $+0.2$)
  **And** the "Self-Confidence" $w_{Sales, Sales}$ should decrease to normalize the row
  **And** the UI should show a notification "Sales Manager trusts you more now."

**Scenario: Increasing Opinion via Evidence**
  **Given** the "Finance Director" has an opinion of $0.3$ (Negative)
  **And** the user selects "Show ROI Data"
  **When** the turn is processed
  **Then** the opinion $x_{Finance}$ should increase directly (e.g., to $0.5$)
  **But** the trust matrix $W$ might remain unchanged (or change slightly).

### Feature: Opinion Propagation (The Math)
**As a** System Architect
**I want** the simulation to follow the DeGroot model
**So that** the behavior is mathematically consistent, not random.

**Scenario: Opinion Averaging**
  **Given** Agent A has opinion $0.0$ and trusts Agent B ($w_{AB}=0.5$) and Agent A ($w_{AA}=0.5$)
  **And** Agent B has opinion $1.0$
  **When** one simulation step runs
  **Then** Agent A's new opinion should be $0.5 \times 0.0 + 0.5 \times 1.0 = 0.5$
  **And** this calculation must be exact (within float precision).

### Feature: Gate 3 - One Feature Selection
**As a** User
**I want** to lock in my "One Feature" solution
**So that** I can start the consensus game.

**Scenario: Selecting the MVP Feature**
  **Given** the user has a list of 5 potential features
  **When** the user selects "Feature A: One-click ordering"
  **Then** the system should discard the other 4 features
  **And** the `AgentState` should update `solution_scope` to "Feature A"
  **And** the Simulation should initialize with this scope (resetting previous opinions).
