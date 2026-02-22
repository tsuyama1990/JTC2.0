# Cycle 02 UAT: The Hell Meeting (Adversarial Simulation)

## 1. Test Scenarios

These scenarios are designed to validate the "Emotional Reality" and "Business Logic" of the system. The "Hell Meeting" is not just a game; it is a serious simulation of organizational dynamics.

### Scenario ID: UAT-C02-01 - Adversarial Critique (The "Hell Meeting")
**Priority**: High
**Description**:
This scenario validates that the system can simulate a hostile corporate environment without becoming abusive or irrelevant. The user selects a valid business idea from Cycle 01 (e.g., "AI-powered Gardening Assistant"). The system must then launch a simulation where two distinct personas—Finance Director and Sales Manager—attack the idea using *external data*.

The "Finance Director" should focus on cost, ROI, and budget. They should use Tavily to find the cost of similar existing solutions or the price of APIs, arguing that the margin is too thin.
The "Sales Manager" should focus on customer acquisition, market size, and cannibalization. They should argue that "our existing customers don't want this."

**Marimo Implementation Plan**:
1.  **Setup Cell**: Load a pre-defined `LeanCanvas` into the state.
2.  **Execution Cell**: Run the `graph.invoke()` for the meeting phase.
3.  **Output Cell**: Display the transcript line-by-line with "Actor Name: Message".
4.  **Validation Cell**: Use an LLM judge to rate the critique on:
    *   **Specificity**: Did they mention actual numbers/companies?
    *   **Persona**: Did Finance sound like Finance?
    *   **Hostility**: Was it tough but fair (Professional)?

**Evaluation Criteria**:
1.  **Data Usage**: The critique must reference at least one real-world fact (competitor, regulation, cost) found via search.
2.  **Role Consistency**: Finance should not talk about UX; Sales should not talk about server costs.
3.  **Response Handling**: The "New Employee Agent" must attempt a defense, even if weak. It should not crash or hallucinate agreement ("You are right, I quit").

### Scenario ID: UAT-C02-02 - The Silent CPO's Advice (Mentorship)
**Priority**: Medium
**Description**:
After the "Hell Meeting", the user (and the battered proxy agent) needs a path forward. The CPO Agent acts as the "Good Cop" or the "Wise Mentor". This scenario validates that the CPO's advice is *derived from the meeting*, not generic platitudes.

If Finance complained about "High API costs", the CPO should suggest "Finding a cheaper model" or "Pre-paying for credits". If Sales complained about "No market need", the CPO should suggest "Doing more interviews" (leading to Cycle 03).

**Marimo Implementation Plan**:
1.  **Context Cell**: Load a meeting transcript where Finance attacks the cost structure.
2.  **Execution Cell**: Run the CPO node only.
3.  **Output Cell**: Print the advice.
4.  **Validation Cell**: Check if the advice contains keywords related to the specific critique (e.g., "cost", "margin", "pricing").

**Evaluation Criteria**:
1.  **Relevance**: The advice must address the strongest point made by the opponents.
2.  **Actionability**: It should suggest a concrete next step (e.g., "Go interview 5 people about price sensitivity"), not just "Think harder."
3.  **Tone**: The tone should be supportive but realistic ("That was rough, but they have a point about X...").

## 2. Behavior Definitions

We use Gherkin syntax to define the expected behavior of the system features.

### Feature: Adversarial Simulation
**As a** User (Intrapreneur)
**I want** to see my idea criticized by realistic corporate personas
**So that** I can identify weaknesses before presenting to real humans.

**Scenario: Finance Agent critiques a low-margin idea**
  **Given** the current `LeanCanvas` has a "Subscription Model" with low price ($5/mo)
  **And** the "Finance Director" agent is active
  **When** the agent analyzes the canvas
  **Then** it should search for "average SaaS churn rate" or "customer acquisition cost"
  **And** it should generate a critique stating that "LTV < CAC" (Lifetime Value is less than Acquisition Cost)
  **And** it should use a skeptical or dismissive tone ("This is a charity, not a business.").

**Scenario: Sales Agent critiques a niche idea**
  **Given** the current `LeanCanvas` targets "Left-handed Eskimo dentists"
  **And** the "Sales Manager" agent is active
  **When** the agent analyzes the canvas
  **Then** it should search for the "total addressable market (TAM)" of dentists in that region
  **And** it should argue that the market size is too small to justify the development cost
  **And** it should suggest that "we should focus on our core accounts instead."

### Feature: Proxy Agent Defense
**As a** User
**I want** my digital avatar to defend the idea
**So that** I don't feel personally attacked.

**Scenario: Employee Agent responds to critique**
  **Given** the Finance Agent has just said "This is too expensive."
  **When** it is the Employee Agent's turn
  **Then** it should acknowledge the point ("I understand the concern...")
  **And** it should pivot to a counter-argument based on value ("But the efficiency gains justify the premium...")
  **And** it should NOT apologize profusely or abandon the idea immediately.

### Feature: CPO Mentorship
**As a** User
**I want** to receive constructive feedback after the conflict
**So that** I know how to improve the idea.

**Scenario: CPO summarizes the meeting**
  **Given** the meeting transcript contains arguments about "Legal Risks" and "Brand Safety"
  **When** the CPO Agent runs
  **Then** it should identify "Regulatory Compliance" as the blocker
  **And** it should advise the user to "Consult with Legal" or "Find a loophole/precedent" in the next cycle.
