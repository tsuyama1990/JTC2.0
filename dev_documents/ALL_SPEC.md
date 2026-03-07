# The JTC 2.0 Next Generation Specification Document (Remastered Edition)

Version: 2.0.6
Last Updated: 2026-03-08
Document Classification: System Architecture & Product Requirements Document (PRD)

## 1. Introduction

### 1.1 Project Background and Objectives
"The JTC 2.0" is a simulation platform designed to radically streamline and enhance the new business creation process within Traditional Japanese Companies (JTCs) using Large Language Models (LLMs) and a multi-agent system. In the initial version, the system achieved the simulation of internal office politics (harsh feedback meetings) and the automatic generation of Minimum Viable Products (MVPs) using v0.dev. However, challenges emerged, particularly the tendency for AI to make "logical leaps" (hallucinations) and the system's lock-in to specific AI tools.

This Remastered edition maps the validation process from "Customer-Problem Fit (CPF)" to "Problem-Solution Fit (PSF)"—as advocated in Masayuki Tadokoro's *Startup Science*—onto the system without any logical jumps. By enforcing strict "Schemas" using Pydantic on the LLM and breaking down the thought process (Chain of Thought), the system completely eliminates hallucinations.

### 1.2 Redefinition of the Final Output
This system discontinues the direct execution of specific UI generation APIs (like v0.dev). Instead, the final output of the system is redefined as the **"Generation of a 'Perfect Prompt Specification Document (AgentPromptSpec.md)' and an 'MVP Experiment Plan' that can be directly inputted into any autonomous AI coding agent such as Cursor, Windsurf, or Google Antigravity."** This ensures the system functions as a universal "ultimate requirements definition engine" that will not become obsolete.

## 2. Core Architecture and Design Philosophy

### 2.1 Eliminating Hallucinations via Pydantic and Chain of Thought
To prevent context loss during the AI's reasoning process, the outputs of all LangGraph nodes are strictly structured using `pydantic.BaseModel` and `extra="forbid"`. This approach enforces and visualises the "Chain of Thought" at the system level. The AI is absolutely forbidden from making logical leaps, such as jumping directly from an "Empathy Map" to a "Feature" (the solution). It must sequentially complete specific schemas (canvases) step-by-step: "Alternative Analysis" -> "Value Proposition" -> "Mental Model Diagram" -> "Customer Journey" -> "Sitemap and User Stories".

By chaining the canvas outputted in the previous step as the input for the next, the resolution of the product is gradually increased. This meticulous flow completely eliminates the space for plausible lies (hallucinations) based on generalities.

### 2.2 Multi-Agent Orchestration (LangGraph)
Using LangGraph, the system orchestrates the following three main sub-graphs (meeting bodies):
*   **The JTC Board (Internal Approval Simulation):** Harsh feedback on the business model and feasibility by the Finance Manager, Sales Manager, and Chief Product Officer (CPO).
*   **Virtual Market (Virtual Market Test):** Severe reviews and commitment judgements on the solution by a virtual customer agent.
*   **The 3H Review (Product Refinement):** A multifaceted validation of the wireframes by the Hacker (technology), Hipster (UX), and Hustler (business).

### 2.3 De-identification UI (Pyxel) and the "Approval" Effect
While complex business logic progresses on the backend, the frontend UI presented to the user maintains a 16-colour retro RPG-style screen using "Pyxel". This is a crucial architectural decision to de-identify severe criticism or the rejection of ideas by the AI as merely "game events," thereby ensuring the user's psychological safety.

Furthermore, whenever the generation process for various canvases (like the Alternative Analysis or Customer Journey) is completed and passes the system's validation, a dynamic pixel-art "Approval" stamp (a red Hanko) is stamped onto the Pyxel screen. By playfully reversing the traditional Japanese Hanko culture, the design gives the user a strong sense of achievement and progression as they break through each barrier.

## 3. Overall Workflow (The Fitness Journey Workflow)

The system executes the following 6 phases, comprising a total of 14 major nodes (steps), in sequence. After each canvas is generated, a "Human In the Loop (HITL) Feedback Gate" is inserted to accept course corrections from the user.

### Phase 1: Idea Verification
*   **Step 1: Ideation & PEST Analysis (`ideator_node`)**
    Uses the Tavily Search API to find macro-environmental (PEST) inflection points. Generates 10 "Good Crazy" business ideas (using the LeanCanvas model).
*   **[HITL Gate 1]:** The user selects the "Plan A" they wish to pursue.

### Phase 2: Customer / Problem Fit
*   **Step 2: Persona & Empathy Mapping (`persona_node`)**
    Generates a high-resolution Persona and EmpathyMap from the selected idea.
*   **Step 3: Alternative Analysis (`alternative_analysis_node`)**
    Identifies current alternative solutions (e.g., Excel, existing SaaS) and deduces the "10x Value" that outweighs the effort of switching (switching costs).
*   **Step 4: Value Proposition Design (`vpc_node`)**
    Validates and structures how the "Pain Relievers" and "Gain Creators" provided by the solution fit the customer's "Customer Jobs" and "Pains/Gains".
*   **[HITL Gate 1.5 - CPF Feedback]:** The models generated in Steps 2 to 4 are outputted as a PDF, and an "Approval" stamp is pressed on the Pyxel UI. The user reviews the PDF and can provide instructions (feedback) to adjust the persona or VPC if necessary.
*   **Step 5: Problem Interview RAG (`transcript_ingestion_node`)**
    Vectorises audio transcripts (from tools like PLAUD) of customer interviews conducted by the user using LlamaIndex. The CPO agent performs a fact-check based on "The Mom Test" criteria.

### Phase 3: Problem / Solution Fit
*   **Step 6: Mental Model & Journey Mapping (`mental_model_journey_node`)**
    Visualises the underlying "Towers of Thought" (beliefs, values) behind the user's behaviour as a MentalModelDiagram. It maps the chronological behaviour based on that mental model onto a CustomerJourney and extracts the UserStory from the touchpoint with the strongest Pain.
*   **Step 7: Sitemap & Lo-Fi Wireframing (`sitemap_wireframe_node`)**
    Defines the overall URL structure and page transitions of the application as a Sitemap. Based on the defined sitemap, it outputs the structure of specific screens required to achieve the user story as a pure text hierarchy `WireframeText` model, stripped of design elements.
*   **[HITL Gate 1.8 - PSF Feedback]:** The mental model, journey, and sitemap are outputted as a PDF, and an "Approval" stamp is pressed on Pyxel. The user reviews the PDF and provides instructions (feedback) to trim features or amend the story.

### Phase 4: Validation & Review
*   **Step 8: Virtual Solution Interview (`virtual_customer_node`)**
    Presents the wireframe and sitemap to a "Virtual Customer Agent" injected with the persona and mental model prompts. The virtual customer provides feedback on questions like "How much would you pay for this?" and "Where would you drop off?".
*   **[HITL Gate 2]:** The user observes the virtual customer's reaction and decides whether to pivot the idea or proceed.
*   **Step 9: JTC Board Simulation (`jtc_simulation_node`)**
    Harsh feedback from the Finance Manager (regarding ROI and costs) and the Sales Manager (regarding cannibalisation and ease of selling). This is rendered in the Pyxel UI.
*   **Step 10: 3H Review (`3h_review_node`)**
    Final review and refinement of the product specifications by the Hacker (technical feasibility), Hipster (UX friction), and Hustler (unit economics).

### Phase 5 & 6: Output Generation
*   **Step 11: Agent Prompt Spec Generation (`spec_generation_node`)**
    Aggregates all context gathered so far to generate a complete Markdown prompt, `AgentPromptSpec`, intended for AI coding tools.
*   **Step 12: Experiment Planning (`experiment_planning_node`)**
    Generates an `ExperimentPlan` (an AARRR-based KPI tree) that defines "what to measure and how" using the generated MVP.
*   **[HITL Gate 3 - Final Output FB]:** Upon completion of the experiment plan and final specifications generation, the final "Approval" stamp is pressed, and the series of final deliverables are converted to PDF.
*   **Step 13: Governance Check (`governance_node`)**
    Outputs the final report in the format of a JTC "Ringi-Sho" (稟議書 - approval document).

## 4. Detailed Domain Models Added/Changed (Pydantic Schemas)

These are new data model definitions to prevent AI hallucinations and maintain context.

### 4.1 Value Proposition Canvas (`ValuePropositionCanvas`)
*   `CustomerProfile`: Contains `customer_jobs`, `pains`, and `gains`.
*   `ValueMap`: Contains `products_and_services`, `pain_relievers`, and `gain_creators`.
*   `ValuePropositionCanvas`: Combines the profile and map, adding a `fit_evaluation` to verify the logical fit.

### 4.2 Mental Model Diagram (`MentalModelDiagram`)
*   `MentalTower`: Contains a `belief` (the user's underlying value) and related `cognitive_tasks`.
*   `MentalModelDiagram`: A collection of `towers` and a `feature_alignment` string mapping provided features to these towers.

### 4.3 Alternative Analysis Model (`AlternativeAnalysis`)
*   `AlternativeTool`: Contains `name`, `financial_cost`, `time_cost`, and `ux_friction`.
*   `AlternativeAnalysis`: Lists current alternatives, defines the `switching_cost`, and states the `ten_x_value` (10x value) required to overcome it.

### 4.4 Customer Journey Model (`CustomerJourney`)
*   `JourneyPhase`: Contains `phase_name`, `touchpoint`, `customer_action`, `mental_tower_ref`, `pain_points`, and an `emotion_score` (-5 to 5).
*   `CustomerJourney`: A list of phases, highlighting the `worst_pain_phase`.

### 4.5 Sitemap & User Story Model (`SitemapAndStory`)
*   `Route`: URL path, name, purpose, and whether it is protected.
*   `UserStory`: Follows the "As a... I want to... So that..." format, with acceptance criteria and a target route.
*   `SitemapAndStory`: Combines the sitemap routes with a single `core_story`.

### 4.6 Experiment Plan Model (`ExperimentPlan`)
*   `MetricTarget`: A metric name, its target value for PMF, and the measurement method.
*   `ExperimentPlan`: Details the riskiest assumption, experiment type, acquisition channel, AARRR metrics, and pivot conditions.

### 4.7 Agent Specification Document Model (`AgentPromptSpec`)
*   `StateMachine`: Defines the UI layout for success, loading, error, and empty states.
*   `AgentPromptSpec`: Includes the sitemap, routing constraints, core user story, state machine, validation rules, and a Mermaid flowchart string.

## 5. Agent Definitions

Prompt guidelines for the dedicated AI agents driving the LangGraph nodes.

**[Important Principle: Absolute Context Inheritance]**
All agents in this system must not propose ideas or features based solely on their own training data or intuition (i.e., from scratch). All structured data generated sequentially via the Chain of Thought process in Phases 1 to 3 (personas, empathy maps, VPCs, mental model diagrams, customer journeys, sitemaps, etc.) must be loaded into the prompt as "absolute prerequisites". Agents are strictly controlled to build product specifications and validate effectiveness only while adhering to these "customer understanding canvases".

### 5.1 Virtual Customer Agent
*   **Role:** The target persona themselves.
*   **Prompt System:** "You are [Persona Name]. At the core of your thoughts are beliefs such as [MentalModelDiagram.towers]. You currently use [AlternativeTool] but are deeply troubled by [Pain]. Regarding the feature about to be proposed, please provide strictly unvarnished feedback on whether you would be willing to pay to use it, or if it is unnecessary. Please be particularly sensitive to 'hassle' (switching costs)."

### 5.2 The 3H Review Agents
*   **Hacker Agent:** "While adhering to the prerequisite sitemap and functional requirements, review the wireframe from the perspectives of technical debt, scalability, and security. Avoid unnecessarily complex DB structures or real-time communication; seek out ways to substitute them with spreadsheets or mock existing APIs."
*   **Hipster Agent:** "While adhering to the prerequisite mental model and persona, review the UX based on the user principle of 'Don't make me think'. Point out onboarding friction that contradicts the mental model, excessive tap counts, and unhelpful error states."
*   **Hustler Agent:** "While adhering to the prerequisite alternative analysis and VPC, review the business model from the perspective of unit economics (LTV > 3x CAC). Strictly question who will find this, how they will find it, and why they will continue to pay for it."

### 5.3 Builder Agent (Role Change)
*   **Old Role:** Calls the v0.dev API to generate a URL.
*   **New Role:** Loads all previously generated context (VPC, mental model, journey, story, sitemap, 3H review results) as an integrated prerequisite. Applying "subtractive thinking" (deleting unnecessary features that do not directly solve user pain), it generates the ultimate requirements definition document, `AgentPromptSpec`, which is compatible with any AI coding tool.

## 6. Final Output Format Specifications

If the system completes successfully, the following files will be outputted to a local directory.

### 6.1 MVP_PROMPT_SPEC.md
A file designed to be copied and pasted directly into the chat interface of AI editors/agents like Cursor, Windsurf, v0.dev, or Google Antigravity.

### 6.2 EXPERIMENT_PLAN.md
A sprint plan demonstrating how to conduct hypothesis testing in the real world using the generated MVP. It includes details such as traffic acquisition routes for the landing page, policies for concierge-style support manuals, and the borderline AARRR metrics to judge "PMF Achievement".

### 6.3 PDF Output of Canvas Documents and Pyxel Approval Effect [NEW]
The system executes the following processes at the milestones of each reasoning phase to facilitate smooth co-creation (HITL) with a human.

1.  **Target Documents:** Value Proposition Canvas, Mental Model Diagram, Alternative Analysis Model, Customer Journey Model, Sitemap & User Story Model, Experiment Plan Model.
2.  **Approval Effect on Pyxel:** Immediately after each document is successfully generated as a Pydantic model, an animation and sound effect of a red "Approval" stamp being firmly pressed onto the Pyxel retro UI screen is played.
3.  **Simplified Output of High-Resolution PDFs:** Simultaneously, behind the scenes, the various canvases are visually organised and outputted as high-resolution PDF files to a local directory (e.g., `/outputs/canvas/`).
4.  **Human In the Loop (HITL) Feedback:** The user briefly reviews the outputted PDF and can intervene and input correction feedback from a human perspective into the Pyxel prompt input screen (e.g., "I want to narrow the target slightly more," "Increase the resolution of the Pain").

## 7. Non-Functional Requirements & Observability

### 7.1 Complete Integration of LangSmith Tracing
LangSmith tracing, which was disabled in previous versions, is now a mandatory requirement by default (allowing environment variables via `extra="ignore"` or explicit field definitions).
*   **Purpose:**
    1.  To monitor and control infinite loops (deadlocks) and token consumption during virtual customer tests and 3H reviews.
    2.  To debug context propagation (Pydantic model conversion loss) between steps.

### 7.2 Circuit Breakers and Hard Limits
In multi-agent dialogues (especially Simulation and 3H Review), a moderator logic must be inserted to forcibly terminate the conversation by detecting specific string expressions (e.g., "I agree", "We are running in parallel") in addition to setting `max_turns`, in order to prevent API wastage.
