# The JTC 2.0 (Remastered Edition)

A multi-agent simulation platform designed to radically streamline the new business creation process within traditional large Japanese corporations (JTCs).

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

## 1. Key Features

*   **Schema-Driven Generation (Zero Hallucination):** Enforces strict Pydantic models at every step of the generation process (Chain of Thought). The system logically advances through rigorous strategy and validation frameworks, mapping out the problem space before generating a solution. Core steps now include:
    *   Alternative Analysis and Switching Costs
    *   Value Proposition Canvas (VPC)
    *   Mental Model Diagram mapping
    *   Chronological Customer Journey creation
    *   Sitemap mapping and User Story generation
*   **Universal AI Prompt Output:** Instead of locking into a specific UI generator, the system produces a flawless `AgentPromptSpec.md`—the ultimate requirement document ready to be digested by modern AI coding agents like Cursor, Windsurf, or Google Antigravity.
*   **Data-Driven Experimentation:** Alongside the final specifications, the system generates a tailored `EXPERIMENT_PLAN.md` based on AARRR metrics to empirically validate the core assumptions of the product.
*   **Psychological Safety via Gamification:** Masks harsh corporate feedback and critical customer reviews behind a retro, 16-colour Pyxel RPG interface, complete with a satisfying "Approval" stamp mechanic for positive reinforcement.
*   **Human-in-the-Loop (HITL) Validation:** Automatically generates high-resolution PDFs of strategic canvases and pauses execution, allowing the human operator to provide course corrections before proceeding to the next stage.
*   **Robust Multi-Agent Simulation:** Features three sophisticated sub-graphs: The JTC Board (financial/political review), Virtual Market (customer validation), and the 3H Review (Hacker, Hipster, Hustler) to pressure-test ideas.

## 2. Architecture Overview

The core logic is orchestrated via LangGraph, maintaining a strict separation of concerns between domain models, the core workflow, external APIs, and the Pyxel UI frontend.

```mermaid
graph TD
    subgraph Frontend [Pyxel UI]
        UI[Retro 16-Color UI]
        Stamp[Approval Stamp Animation]
    end

    subgraph Backend [LangGraph Core]
        State[(GlobalState)]

        N1[Ideator Node]
        N2[Persona & Empathy Node]
        N3[Alternative & VPC Node]
        N4[Mental Model & Journey Node]
        N5[Sitemap & Wireframe Node]
        N6[Virtual Customer Node]
        N7[JTC Simulation Node]
        N8[3H Review Node]
        N9[Spec Generation Node]

        N1 -->|LeanCanvas| N2
        N2 -->|Persona| N3
        N3 -->|VPC| N4
        N4 -->|Journey| N5
        N5 -->|Sitemap| N6
        N6 -->|Feedback| N7
        N7 -->|Approval| N8
        N8 -->|Refined Spec| N9

        N1 -.-> State
        N2 -.-> State
        N3 -.-> State
        N4 -.-> State
        N5 -.-> State
        N6 -.-> State
        N7 -.-> State
        N8 -.-> State
        N9 -.-> State
    end

    subgraph External
        LLM[OpenAI GPT-4]
        Tavily[Tavily Search]
        PDF[PDF Generator]
    end

    Backend <--> LLM
    Backend <--> Tavily
    N3 --> PDF
    N5 --> PDF
    N9 --> PDF

    UI <..> State
    UI --> Stamp
```

## 3. Prerequisites

*   Python 3.12+
*   `uv` (Extremely fast Python package installer and resolver)
*   OpenAI API Key (for real executions)
*   Tavily API Key (optional, for PEST analysis search)

## 4. Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-org/jtc2-0.git
    cd jtc2-0
    ```

2.  **Install dependencies using `uv`:**
    ```bash
    uv sync
    ```

3.  **Environment Variables:**
    Copy the example `.env` file and fill in your API keys.
    ```bash
    cp .env.example .env
    ```

## 5. Usage

**Quick Start Tutorial (Mock Mode):**
To experience the entire workflow without spending API tokens, you can run the interactive Marimo tutorial.
```bash
uv run marimo run tutorials/UAT_AND_TUTORIAL.py
```

**Running the Core Application:**
```bash
uv run python -m src.ui.app
```

## 6. Development Workflow

The development plan is strictly divided into exactly 6 implementation cycles.

To ensure code quality and prevent AI-generated spaghetti code, this project uses strict linting and type checking.

*   **Run formatting and linting:**
    ```bash
    uv run ruff check .
    uv run ruff format .
    ```
*   **Run type checking (Strict Mode):**
    ```bash
    uv run mypy .
    ```
*   **Run tests:**
    ```bash
    uv run pytest
    ```

## 7. Project Structure

```text
jtc2-0/
├── src/
│   ├── core/              # LangGraph nodes and orchestrator
│   ├── domain_models/     # Strict Pydantic schemas (VPC, Journey, Mental Model, Sitemap, etc.)
│   ├── services/          # File I/O and PDF generation
│   └── ui/                # Pyxel retro interface
├── tests/                 # Unit and Integration tests
├── tutorials/             # Marimo notebooks for UAT
└── pyproject.toml         # Dependency and linter configuration
```

## 8. License

This project is licensed under the MIT License - see the LICENSE file for details.
