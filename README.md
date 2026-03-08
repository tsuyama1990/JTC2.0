# The JTC 2.0 (Remastered Edition): Enterprise Business Accelerator

![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen)
![Version](https://img.shields.io/badge/Version-2.0.6-blue)
![Python](https://img.shields.io/badge/Python-3.12%2B-blue)

**The JTC 2.0 (Remastered Edition)** is an advanced, multi-agent simulation platform designed to radically streamline the new business creation process. By enforcing a strict "Chain of Thought" through Pydantic schemas, it eliminates AI hallucinations and generates perfect, obsolescence-proof Prompt Specifications (`AgentPromptSpec.md`) that can drive any modern AI coding agent (e.g., Cursor, Windsurf) to build exactly what your customers need.

## 🚀 Overview
- **What**: A comprehensive platform for validating business ideas and generating high-resolution prompt specifications.
- **Why**: Prevent AI hallucinations, escape vendor lock-in, and provide a psychologically safe environment to test business ideas before any engineering effort.

## ✨ Features

- **Schema-Driven Generation**: Completely eliminates AI hallucinations by enforcing a strict Pydantic model chain from Empathy Maps to Final Specifications.
- **Universal Output**: Generates a universal `AgentPromptSpec.md` containing site maps, state machines, and Mermaid flowcharts instead of just a URL.
- **Approval Gamification**: Review complex AI outputs comfortably via "Approval Stamp" (赤いハンコ) animations on a retro UI.
- **Real-World Data Ingestion**: Ingest actual customer interview transcripts to fact-check your business model against "The Mom Test."
- **Internal Board Simulation**: Simulate harsh internal reviews and map the hidden influence network to build consensus before writing a single line of code.

## 📋 Requirements

- **Python 3.12+**
- **uv** (Modern Python package manager)
- **API Keys**:
    - `OPENAI_API_KEY` (GPT-4o recommended)
    - `TAVILY_API_KEY` (For market research)

## 🛠 Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/your-org/jtc2-0.git
    cd jtc2-0
    ```

2.  **Install dependencies using uv**
    ```bash
    uv sync
    ```

3.  **Configure Environment Variables**
    Create a `.env` file in the root directory and add your API keys:
    ```bash
    cp .env.example .env
    # Edit .env to add OPENAI_API_KEY and TAVILY_API_KEY
    ```

## 🚀 Usage

**Start the Remastered Workflow:**

```bash
uv run main.py "AI for Agriculture"
```

The system will:
1.  Generate Lean Canvas ideas and prompt you to select one.
2.  Generate a Value Proposition Canvas and pause for your review (producing a PDF and a Pyxel Stamp).
3.  Ingest real-world transcripts if provided.
4.  Construct a Mental Model Diagram and Customer Journey, pausing again for review.
5.  Simulate a Virtual Customer interview and the Internal Board.
6.  Finally, output `AgentPromptSpec.md` and `ExperimentPlan.md` into your local directory.

**Ingest Transcripts (RAG):**
```bash
uv run main.py --ingest ./path/to/interview.txt
```

**Run Interactive Tutorials:**
```bash
uv run marimo edit tutorials/UAT_AND_TUTORIAL.py
```

## 🏗 Architecture / Structure

The system orchestrates specialized agents via LangGraph, maintaining a central `GlobalState` populated by strictly validated Pydantic models. It follows a "Fitness Journey" workflow, proceeding from Customer/Problem Fit to Problem/Solution Fit.

```ascii
.
├── src/
│   ├── agents/             # Logic for specialized agents (Virtual Customer, 3H Review, Builder)
│   ├── core/               # State orchestration (LangGraph), Services, Configs
│   ├── data/               # RAG ingestion logic
│   ├── domain_models/      # Strict Pydantic schemas (VPC, Journey, AgentPromptSpec)
│   └── ui/                 # Pyxel Retro UI and Stamp animations
├── tutorials/              # Interactive Notebooks
├── dev_documents/          # Architecture and Reference Documents
└── pyproject.toml          # Dependency Configurations
```

## 🗺️ Roadmap
- Continuous integration of advanced multi-agent patterns.
- Expansion of generated specifications to include backend models.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
