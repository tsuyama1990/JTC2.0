# The JTC 2.0 Remastered Edition: System Specification

Version: 2.0.6
Last Updated: 2026-03-08
Document Classification: System Architecture & Requirements Specification (PRD)

## 1. Introduction

### 1.1 Project Background and Objectives
"The JTC 2.0" is a simulation platform designed to drastically improve and streamline the new business creation process within traditional large Japanese corporations (JTCs). It achieves this by utilising Large Language Models (LLMs) and a multi-agent system.

The initial version successfully simulated internal politics (the rigorous "grilling" meetings) and automated the generation of Minimum Viable Products (MVPs) using v0.dev. However, it revealed critical challenges inherent to AI, namely "contextual leaps" (hallucinations) and "lock-in" to specific AI tools.

This Remastered Edition addresses these issues. It maps the validation process—from Customer-Problem Fit (CPF) to Problem-Solution Fit (PSF), as advocated in Masayuki Tadokoro's "Science of Startup"—directly onto the system without any logical leaps. By enforcing strict "schemas" (types) on the LLM using Pydantic and segmenting the thought process (Chain of Thought), the system completely eliminates hallucinations.

### 1.2 Redefinition of Final Deliverables (System Output)
This system discontinues the approach of directly executing specific UI generation APIs (like v0.dev). Instead, the system's final output is redefined as the generation of a **"Perfect Prompt Specification (`AgentPromptSpec.md`)"** and an **"MVP Experiment Plan."**

These documents are designed to be directly input into any autonomous AI coding agent, such as Cursor, Windsurf, or Google Antigravity. As a result, the system functions as a universal, "ultimate requirements definition engine" that will not become obsolete.

## 2. Core Architecture and Design Philosophy

### 2.1 Eliminating Hallucinations via Schema-Driven Generation and Chain of Thought
To prevent the loss of context during the AI's reasoning process, the output of every LangGraph node is strictly structured using `pydantic.BaseModel` with `extra="forbid"`. This enforces and visualises the "Chain of Thought" in prompt engineering at the system level.

The AI is strictly prohibited from making logical leaps, such as deriving a "feature" (solution) directly from an "empathy map." It must sequentially complete the following schemas (canvases):
1. Alternative Analysis
2. Value Proposition Canvas (VPC)
3. Mental Model Diagram
4. Customer Journey
5. Sitemap and User Stories

By chaining the output canvas of the previous step as the input for the next, the product's resolution is incrementally increased. This meticulous flow is designed to completely eliminate any room for "plausible lies" (hallucinations) based on generalities.

### 2.2 Multi-Agent Orchestration (LangGraph)
The system uses LangGraph to orchestrate three primary sub-graphs (meeting bodies):
*   **The JTC Board (Internal Approval Simulation):** Rigorous questioning of the business model and feasibility by the CFO, Head of Sales, and CPO.
*   **Virtual Market (Virtual Customer Test):** Harsh reviews and commitment evaluations of the solution by a virtual customer agent.
*   **The 3H Review (Product Refinement):** Comprehensive verification of the wireframes by the Hacker (Technology), Hipster (UX), and Hustler (Business).

### 2.3 De-identification UI (Pyxel) and "Approval" Aesthetics
While complex business logic runs in the backend, the frontend UI facing the user maintains a 16-colour, retro RPG aesthetic using "Pyxel". This is a crucial architectural decision to guarantee the user's psychological safety by "de-identifying" harsh criticisms or idea rejections from the AI as mere "game events."

Furthermore, whenever a canvas generation process is completed and passes system verification, a dynamic, pixel-art "Approval" stamp (a red Hanko) is stamped onto the Pyxel screen. This subverts the traditional JTC Hanko culture to give the user a strong sense of achievement and progress.

## 3. Entire Workflow (The Fitness Journey)

The system executes the following 6 phases, comprising 14 primary nodes (steps), in sequence. After each canvas generation, a "Human-in-the-Loop (HITL) Feedback Gate" is inserted to allow the user to apply course corrections.

### Phase 1: Idea Verification
*   **Step 1: Ideation & PEST Analysis (`ideator_node`)**
    *   Uses the Tavily Search API to find macro-environmental (PEST) inflection points.
    *   Generates 10 "Good Crazy" business ideas (`LeanCanvas` model).
*   **[HITL Gate 1]:** The user selects the "Plan A" to pursue.

### Phase 2: Customer / Problem Fit (CPF)
*   **Step 2: Persona & Empathy Mapping (`persona_node`)**
    *   Generates a high-resolution Persona and EmpathyMap from the selected idea.
*   **Step 3: Alternative Analysis (`alternative_analysis_node`)**
    *   Identifies current alternative solutions (Excel, existing SaaS, etc.) and deduces a "10x Value" that outweighs the switching costs.
*   **Step 4: Value Proposition Design (`vpc_node`)**
    *   Verifies and structures how the proposed "Pain Relievers" and "Gain Creators" match (Fit) the customer's "Customer Jobs" and "Pain/Gain."
*   **[HITL Gate 1.5 - CPF Feedback]:** The models generated in Steps 2-4 are output as a PDF, and the "Approval" stamp is shown on Pyxel. The user reviews the PDF and can input adjustment instructions (feedback) for the Persona or VPC.
*   **Step 5: Problem Interview RAG (`transcript_ingestion_node`)**
    *   Vectorises the audio transcripts (e.g., PLAUD) of customer interviews conducted by the user using LlamaIndex. The CPO agent performs a fact-check based on "The Mom Test" criteria.

### Phase 3: Problem / Solution Fit (PSF)
*   **Step 6: Mental Model & Journey Mapping (`mental_model_journey_node`)**
    *   Visualises the "Towers of Thought" (beliefs/values) behind the user's actions as a `MentalModelDiagram`. Maps chronological actions based on this mental model into a `CustomerJourney`, extracting the `UserStory` from the touchpoint with the strongest pain.
*   **Step 7: Sitemap & Lo-Fi Wireframing (`sitemap_wireframe_node`)**
    *   Defines the overall URL structure and page transitions as a `Sitemap`. Based on this, it outputs a `WireframeText` model—a pure text hierarchy devoid of design elements—representing the screen structure needed to achieve the user story.
*   **[HITL Gate 1.8 - PSF Feedback]:** The Mental Model, Journey, and Sitemap are output as a PDF, and the "Approval" stamp is shown on Pyxel. The user reviews the PDF and provides feedback to trim features or correct the story.

### Phase 4: Validation & Review
*   **Step 8: Virtual Solution Interview (`virtual_customer_node`)**
    *   Presents the wireframe and sitemap to a "Virtual Customer Agent" injected with the Persona and Mental Model prompts. The virtual customer provides feedback on "How much would I pay for this?" and "Where would I drop off?"
*   **[HITL Gate 2]:** The user reviews the virtual customer's reaction and decides whether to pivot or proceed.
*   **Step 9: JTC Board Simulation (`jtc_simulation_node`)**
    *   Rigorous questioning by the CFO (ROI/Costs) and Head of Sales (Cannibalisation/Marketability). Rendered via the Pyxel UI.
*   **Step 10: 3H Review (`3h_review_node`)**
    *   Final review and correction of product specifications by the Hacker (Technical Feasibility), Hipster (UX Friction), and Hustler (Unit Economics).

### Phase 5 & 6: Output Generation
*   **Step 11: Agent Prompt Spec Generation (`spec_generation_node`)**
    *   Aggregates all previous context to generate `AgentPromptSpec`, a perfect markdown prompt for AI coding tools.
*   **Step 12: Experiment Planning (`experiment_planning_node`)**
    *   Generates an `ExperimentPlan` (AARRR-based KPI tree) defining "what and how to measure" using the generated MVP.
*   **[HITL Gate 3 - Final Output FB]:** Upon completion of the experiment plan and final specification, the final "Approval" stamp is pressed, and all deliverables are converted to PDF.
*   **Step 13: Governance Check (`governance_node`)**
    *   Outputs the final report in the JTC "Ringi-Sho" (Approval Document) format.

## 4. Domain Models (Pydantic Schemas)

New data models are defined to prevent AI hallucination and maintain context. All models must use `ConfigDict(extra="forbid")`.

### 4.1 Value Proposition Canvas (ValuePropositionCanvas)
*   `CustomerProfile`: Contains `customer_jobs`, `pains`, and `gains`.
*   `ValueMap`: Contains `products_and_services`, `pain_relievers`, and `gain_creators`.
*   `ValuePropositionCanvas`: Contains the profile, map, and a `fit_evaluation` string confirming logical alignment.

### 4.2 Mental Model Diagram (MentalModelDiagram)
*   `MentalTower`: Contains a core `belief` and associated `cognitive_tasks`.
*   `MentalModelDiagram`: Contains a list of `towers` and a `feature_alignment` string mapping features to these towers.

### 4.3 Alternative Analysis Model (AlternativeAnalysis)
*   `AlternativeTool`: Contains `name`, `financial_cost`, `time_cost`, and `ux_friction`.
*   `AlternativeAnalysis`: Contains a list of `current_alternatives`, `switching_cost`, and `ten_x_value`.

### 4.4 Customer Journey Model (CustomerJourney)
*   `JourneyPhase`: Contains `phase_name`, `touchpoint`, `customer_action`, `mental_tower_ref`, `pain_points`, and an `emotion_score` (-5 to 5).
*   `CustomerJourney`: Contains a list of `phases` (3 to 7 items) and the `worst_pain_phase`.

### 4.5 Sitemap & User Story Model (SitemapAndStory)
*   `Route`: Contains `path`, `name`, `purpose`, and `is_protected`.
*   `UserStory`: Contains `as_a`, `i_want_to`, `so_that`, `acceptance_criteria`, and `target_route`.
*   `SitemapAndStory`: Contains the `sitemap` and the `core_story`.

### 4.6 Experiment Plan Model (ExperimentPlan)
*   `MetricTarget`: Contains `metric_name`, `target_value`, and `measurement_method`.
*   `ExperimentPlan`: Contains `riskiest_assumption`, `experiment_type`, `acquisition_channel`, a list of `aarrr_metrics`, and `pivot_condition`.

### 4.7 Agent Prompt Spec Model (AgentPromptSpec)
*   `StateMachine`: Defines layout states for `success`, `loading`, `error`, and `empty`.
*   `AgentPromptSpec`: Contains `sitemap`, `routing_and_constraints`, `core_user_story`, `state_machine`, `validation_rules`, and a `mermaid_flowchart`.

## 5. Agents Definition

### 5.1 Virtual Customer Agent
*   **Role:** The target persona.
*   **Prompt System:** "You are [Persona Name]. Your thoughts are based on [MentalModelDiagram.towers]. You currently use [AlternativeTool] but suffer from [Pain]. Review the proposed features strictly based on whether you would pay to use them, paying special attention to switching costs."

### 5.2 The 3H Review Agents
*   **Hacker Agent:** Reviews wireframes for technical debt, scalability, and security, avoiding complex DBs or real-time comms in favour of mock APIs or spreadsheets. Must adhere to the provided sitemap.
*   **Hipster Agent:** Reviews UX based on the "Don't make me think" principle. Points out friction in onboarding and deviations from the user's mental model.
*   **Hustler Agent:** Reviews the business model focusing on Unit Economics (LTV > 3x CAC) based on the VPC and Alternative Analysis.

### 5.3 Builder Agent
*   **New Role:** Reads all generated context (VPC, Journey, 3H feedback) as absolute prerequisites. Applies "subtractive thinking" (removing features that don't directly solve user pain) to generate the ultimate `AgentPromptSpec`.

## 6. Final Output Format

### 6.1 MVP_PROMPT_SPEC.md
A markdown file designed to be copy-pasted directly into AI editors like Cursor or Windsurf. It includes roles, stack details, routing constraints, sitemaps, core user stories, data schemas, validation rules, state machines (Mermaid), UI structures, and interaction requirements.

### 6.2 EXPERIMENT_PLAN.md
A sprint plan detailing how to validate hypotheses in the real world, including acquisition channels, concierge approaches, and AARRR metrics to determine PMF.

### 6.3 Canvas PDF Output and Pyxel Approval Animation
At each HITL gate, Pydantic canvas models are converted into high-resolution PDFs and saved locally (e.g., `/outputs/canvas/`). Simultaneously, the Pyxel UI plays an animation of a red "Approval" stamp with sound effects. Users can then review the PDFs and provide feedback to the system.

## 7. Non-Functional Requirements & Observability

### 7.1 LangSmith Trace Integration
LangSmith tracing is mandatory to monitor for infinite loops (deadlocks) during Virtual Customer tests and 3H Reviews, and to debug context propagation between steps.

### 7.2 Circuit Breakers and Hard Limits
To prevent API waste during multi-agent dialogues, a moderator logic is implemented. It enforces a `max_turns` limit and monitors for specific string expressions indicating agreement or a stalemate to force-terminate the loop.
