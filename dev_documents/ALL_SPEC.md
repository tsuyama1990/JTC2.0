# The JTC 2.0 Next-Generation Specification Document (Remastered Edition)
Version: 2.0.6
Last Updated: 2026-03-08
Document Classification: System Architecture & Product Requirements Document (PRD)

## 1. Introduction
### 1.1 Project Background and Objectives
"The JTC 2.0" is a simulation platform aimed at drastically streamlining and modernising the new business creation process within Traditional Japanese Companies (JTCs) using LLMs (Large Language Models) and a multi-agent system. While the initial version successfully simulated office politics (Gekizume meetings) and automatically generated MVPs via v0.dev, it revealed challenges such as AI-specific "context jumps (hallucination)" and "vendor lock-in to specific AI tools."

In this remastered edition, the validation process from "Customer-Problem Fit (CPF)" to "Problem-Solution Fit (PSF)"—as proposed in Masayuki Tadokoro's "Startup Science"—is mapped onto the system with absolutely no logical leaps. By enforcing strict "Schemas" using Pydantic on the LLM and subdividing the thinking process (Chain of Thought), hallucinations are completely eliminated.

### 1.2 Redefinition of the Final Deliverable (System Output)
This system abolishes the approach of directly executing specific UI generation APIs (like v0.dev). Instead, the final output of the system is redefined as **the generation of a "Perfect Prompt Specification (AgentPromptSpec.md)" and an "MVP Experiment Plan" that can be input directly into any autonomous AI coding agent such as Cursor, Windsurf, or Google Antigravity.** As a result, the system functions as a universal, obsolescence-proof "Ultimate Requirements Definition Engine."

## 2. Core Architecture and Design Philosophy
### 2.1 Eliminating Hallucination via Pydantic and Chain of Thought
To prevent context loss during the AI's reasoning process, the output of every LangGraph node is strictly structured using `pydantic.BaseModel` and `extra="forbid"`. This approach forces and visualises the "Chain of Thought" in AI prompt engineering at the system level.

The AI is strictly prohibited from jumping straight from an "Empathy Map" to "Features (Solutions)." It must fill out the schema (canvases) sequentially: "Alternative Analysis" → "Value Proposition" → "Mental Model Diagram" → "Customer Journey" → "Sitemap & User Stories." By chaining the canvas output of the previous step as the input to the next, the product's resolution is incrementally increased. This precise flow completely removes any room for the AI's characteristic "plausible lies based on generalities."

### 2.2 Multi-Agent Orchestration (LangGraph)
LangGraph is used to orchestrate three main sub-graphs (committees):
- **The JTC Board (Internal Approval Simulation):** Intense interrogation of the business model and feasibility by the Finance Manager, Sales Manager, and CPO.
- **Virtual Market (Virtual Market Test):** Harsh reviews and commitment judgements on the solution by a virtual customer agent.
- **The 3H Review (Product Polish):** Multi-faceted validation of wireframes by Hacker (Tech), Hipster (UX), and Hustler (Business) agents.

### 2.3 De-identification UI (Pyxel) and "Approval" Direction
While complex business logic progresses on the backend, the frontend UI facing the user maintains a 16-colour retro RPG-style screen using "Pyxel." This is a crucial architectural decision to de-identify harsh criticisms or idea rejections from the AI by framing them as "in-game events," thereby ensuring the user's psychological safety.

Furthermore, every time the generation process of various canvases is completed and passes system validation, an animation of a pixel-art "Approval" stamp (a red Hanko) is dynamically stamped on the Pyxel screen. This design leverages the unique Japanese "Hanko culture" to give the user a strong sense of achievement and progression ("clearing a checkpoint").

## 3. Overall Workflow (The Fitness Journey Workflow)
The system executes the following 6 phases and 14 main nodes (steps) in sequence. After each canvas is generated, a "Human In the Loop (HITL) Feedback Gate" is inserted to allow the user to make course corrections.

### Phase 1: Idea Verification
- **Step 1: Ideation & PEST Analysis (ideator_node):** Uses the Tavily Search API to search for macro-environmental (PEST) inflection points. Generates 10 "Good Crazy" business ideas (LeanCanvas models).
- **[HITL Gate 1]:** The user selects the "Plan A" to pursue.

### Phase 2: Customer / Problem Fit (CPF)
- **Step 2: Persona & Empathy Mapping (persona_node):** Generates high-resolution Personas and EmpathyMaps from the selected idea.
- **Step 3: Alternative Analysis (alternative_analysis_node):** Identifies current alternatives (Excel, existing SaaS, etc.) and infers the "10x Value" needed to overcome switching costs.
- **Step 4: Value Proposition Design (vpc_node):** Validates and structures how the proposed "Pain Relievers" and "Gain Creators" fit the customer's "Customer Jobs" and "Pain/Gains."
- **[HITL Gate 1.5 - CPF Feedback]:** The models generated in Steps 2-4 are output as a PDF, and the "Approval" stamp is pressed on Pyxel. The user reviews the PDF and inputs adjustment instructions.
- **Step 5: Problem Interview RAG (transcript_ingestion_node):** Vectorises user-conducted customer interview transcripts using LlamaIndex. The CPO agent fact-checks them based on "The Mom Test."

### Phase 3: Problem / Solution Fit (PSF)
- **Step 6: Mental Model & Journey Mapping (mental_model_journey_node):** Visualises the "Tower of Thought (beliefs/values)" behind user actions as a MentalModelDiagram. Maps temporal actions based on this model to a CustomerJourney, extracting UserStories from the most painful touchpoints.
- **Step 7: Sitemap & Lo-Fi Wireframing (sitemap_wireframe_node):** Defines the overall URL structure and page transitions as a Sitemap. Outputs the structure of specific screens as pure text-hierarchy WireframeText models.
- **[HITL Gate 1.8 - PSF Feedback]:** The Mental Model, Journey, and Sitemap are output as a PDF, and the "Approval" stamp is pressed. The user provides feedback to trim features or correct stories.

### Phase 4: Validation & Review
- **Step 8: Virtual Solution Interview (virtual_customer_node):** Presents wireframes and the sitemap to a "Virtual Customer Agent" infused with the persona and mental model prompt. The agent provides feedback on willingness to pay and drop-off points.
- **[HITL Gate 2]:** The user decides whether to pivot or proceed based on the virtual customer's reaction.
- **Step 9: JTC Board Simulation (jtc_simulation_node):** Intense interrogation by the Finance Manager (ROI/Cost) and Sales Manager (Cannibalisation/Sellability), rendered on the Pyxel UI.
- **Step 10: 3H Review (3h_review_node):** Final review and correction of product specs by the Hacker (Tech Feasibility), Hipster (UX Friction), and Hustler (Unit Economics).

### Phase 5 & 6: Output Generation
- **Step 11: Agent Prompt Spec Generation (spec_generation_node):** Aggregates all context to generate a perfect markdown prompt `AgentPromptSpec` for AI coding tools.
- **Step 12: Experiment Planning (experiment_planning_node):** Generates an `ExperimentPlan` (AARRR-based KPI tree) defining what and how to measure using the MVP.
- **[HITL Gate 3 - Final Output FB]:** Upon completion, the final "Approval" stamp is pressed, and all deliverables are converted to PDF.
- **Step 13: Governance Check (governance_node):** Outputs the final report in the JTC "Ringi-Sho" format.

## 4. Modified Domain Models (Pydantic Schemas)
New data models defined to prevent AI hallucination and maintain context.

### 4.1 ValuePropositionCanvas
```python
class CustomerProfile(BaseModel):
    customer_jobs: list[str] = Field(..., description="Customer jobs and tasks")
    pains: list[str] = Field(..., description="Risks or negative emotions hindering jobs")
    gains: list[str] = Field(..., description="Benefits expected from the jobs")

class ValueMap(BaseModel):
    products_and_services: list[str] = Field(..., description="List of main products/services")
    pain_relievers: list[str] = Field(..., description="How it specifically removes customer pain")
    gain_creators: list[str] = Field(..., description="How it specifically creates customer gain")

class ValuePropositionCanvas(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_profile: CustomerProfile
    value_map: ValueMap
    fit_evaluation: str = Field(..., description="Validation of logical fit between relievers/pain and creators/gain")
```

### 4.2 MentalModelDiagram
```python
class MentalTower(BaseModel):
    belief: str = Field(..., description="User's underlying beliefs (e.g., 'I don't want to waste time')")
    cognitive_tasks: list[str] = Field(..., description="Tasks/judgements made based on that belief")

class MentalModelDiagram(BaseModel):
    model_config = ConfigDict(extra="forbid")
    towers: list[MentalTower] = Field(..., description="Towers constituting user's thought space")
    feature_alignment: str = Field(..., description="Mapping of how features support the towers")
```

### 4.3 AlternativeAnalysis
```python
class AlternativeTool(BaseModel):
    name: str = Field(..., description="Name of alternative (e.g., Excel, SaaS)")
    financial_cost: str = Field(..., description="Financial cost")
    time_cost: str = Field(..., description="Time cost")
    ux_friction: str = Field(..., description="Maximum stress/friction felt by user")

class AlternativeAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_alternatives: list[AlternativeTool]
    switching_cost: str = Field(..., description="Cost/effort required to switch")
    ten_x_value: str = Field(..., description="10x value overcoming switching costs (UVP)")
```

### 4.4 CustomerJourney
```python
class JourneyPhase(BaseModel):
    phase_name: str = Field(..., description="Phase name (e.g., Awareness, Consideration)")
    touchpoint: str = Field(..., description="Contact point with system/environment")
    customer_action: str = Field(..., description="Specific action taken")
    mental_tower_ref: str = Field(..., description="Belief underlying this action")
    pain_points: list[str] = Field(..., description="Pain felt in this phase")
    emotion_score: int = Field(..., ge=-5, le=5, description="Emotional fluctuation (-5 to 5)")

class CustomerJourney(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phases: list[JourneyPhase] = Field(..., min_length=3, max_length=7)
    worst_pain_phase: str = Field(..., description="Phase with deepest pain to solve")
```

### 4.5 SitemapAndStory
```python
class Route(BaseModel):
    path: str = Field(..., description="URL path (e.g., /, /login)")
    name: str = Field(..., description="Page name")
    purpose: str = Field(..., description="Purpose of page")
    is_protected: bool = Field(..., description="Requires auth?")

class UserStory(BaseModel):
    model_config = ConfigDict(extra="forbid")
    as_a: str = Field(..., description="Persona")
    i_want_to: str = Field(..., description="Action")
    so_that: str = Field(..., description="Goal/Value")
    acceptance_criteria: list[str] = Field(..., description="Acceptance criteria")
    target_route: str = Field(..., description="Main URL path for this action")

class SitemapAndStory(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sitemap: list[Route] = Field(..., description="Overall routing structure")
    core_story: UserStory = Field(..., description="Most critical story to validate as MVP")
```

### 4.6 ExperimentPlan
```python
class MetricTarget(BaseModel):
    metric_name: str = Field(..., description="Metric name (e.g., Day 7 Retention)")
    target_value: str = Field(..., description="Target value for PMF")
    measurement_method: str = Field(..., description="How to measure")

class ExperimentPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    riskiest_assumption: str = Field(..., description="Riskiest assumption being tested")
    experiment_type: str = Field(..., description="MVP Type (e.g., LP, Wizard of Oz)")
    acquisition_channel: str = Field(..., description="Where to get first 100 users")
    aarrr_metrics: list[MetricTarget] = Field(..., description="AARRR tracking metrics")
    pivot_condition: str = Field(..., description="Conditions for immediate pivot")
```

### 4.7 AgentPromptSpec
```python
class StateMachine(BaseModel):
    success: str = Field(..., description="Complete layout for normal data")
    loading: str = Field(..., description="Waiting UI using Skeleton")
    error: str = Field(..., description="Fallback UI and Retry button")
    empty: str = Field(..., description="Empty state with CTA")

class AgentPromptSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sitemap: str = Field(..., description="Routing and information architecture")
    routing_and_constraints: str = Field(..., description="SSR/Client bounds, UI library limits")
    core_user_story: UserStory
    state_machine: StateMachine
    validation_rules: str = Field(..., description="Zod schema or edge cases")
    mermaid_flowchart: str = Field(..., description="State/Data flow diagram in Mermaid")
```

## 5. Agents Definition
Strict rules for AI agents: They must inherit absolute context and never propose features from scratch. They only operate based on the structured data (Personas, Canvases) passed to them.

### 5.1 Virtual Customer Agent
- **Role:** The target persona.
- **Prompt:** "You are [Persona Name]. Your core beliefs are [MentalModelDiagram.towers]. You currently use [AlternativeTool] but suffer from [Pain]. Provide brutal feedback on the proposed feature regarding your willingness to pay and switching costs."

### 5.2 The 3H Review Agents
- **Hacker Agent:** Reviews wireframes for technical debt and scalability within the sitemap constraints. Recommends simple workarounds over complex DBs.
- **Hipster Agent:** Reviews UX based on "Don't make me think." Points out friction in onboarding and excess taps.
- **Hustler Agent:** Reviews unit economics (LTV > 3x CAC) based on the VPC. Interrogates acquisition channels and retention drivers.

### 5.3 Builder Agent
- **New Role:** Instead of calling v0.dev, it ingests all context and applies "subtractive thinking" (removing features that don't solve core pains) to generate the ultimate markdown prompt `AgentPromptSpec`.

## 6. Output Specifications
### 6.1 `MVP_PROMPT_SPEC.md`
A markdown file ready to be pasted into Cursor, Windsurf, or v0.dev. It contains strict instructions on tech stack, sitemap, core user stories, data schemas, validation rules, state machines, UI structure, and accessibility.

### 6.2 `EXPERIMENT_PLAN.md`
A sprint plan showing how to validate assumptions in the real world, including acquisition channels, concierge manuals, and AARRR PMF borders.

### 6.3 PDF Exports and Pyxel Approvals
- The system generates high-resolution PDFs of the models in `/outputs/canvas/`.
- The Pyxel UI plays an "Approval" stamp animation and sound effect.
- Users provide HITL feedback based on the generated PDFs.

## 7. Observability
- **LangSmith Tracing:** Must be fully integrated to monitor multi-agent interactions and debug context propagation.
- **Circuit Breakers:** Implement `max_turns` and keyword-based termination logic to prevent infinite loops and token waste during simulations.
