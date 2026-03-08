# The JTC 2.0: Enterprise Business Accelerator

![Status](https://img.shields.io/badge/Status-Cycle_5_Complete-green)
![Python](https://img.shields.io/badge/Python-3.12+-blue)

**The JTC 2.0** is a paradigm-shifting multi-agent system that fuses the rigorous methodology of **"Startup Science"** with the complex organizational dynamics of **Traditional Japanese Companies (JTCs)**. It is not just a chatbot; it is a role-playing simulation where your business ideas are subjected to "Gekizume" (harsh feedback) by AI agents, validated against real customer interviews, and automatically built into MVPs.

## 🚀 Overview

-   **What**: An AI-powered co-founder that helps you brainstorm, validate, and simulate the organizational resistance to new business ideas.
-   **Why**: To help intrapreneurs navigate the "Valley of Death" in large organizations by simulating the harsh reality of corporate decision-making before pitching to real stakeholders.
-   **How**: Uses **LangGraph** to orchestrate specialized agents (Ideator, Finance, Sales, CPO) and **Tavily** for real-time market research.

## ✨ Features

-   **Automated Ideation Engine**: Generates 10 distinct, research-backed Lean Canvas business ideas from a single topic.
-   **JTC Simulation Engine ("The Meeting")**: Watch your "New Employee" proxy defend your idea against skeptical "Finance Manager" and aggressive "Sales Manager" agents in a realistic debate.
-   **Real-World Data Ingestion (Secure RAG)**: Ingest customer interview transcripts (via `--ingest`) to ground the simulation in primary data. Features strict path validation and memory-safe processing for large files.
-   **CPO Mentor Agent**: A silent observer who provides fact-based, data-driven advice ("The Mom Test") using ingested transcripts to validate or pivot your idea.
-   **Nemawashi (Root-Binding) Engine**: Analyze the invisible influence network within the organization. Identify "Key Influencers" and simulate "Nomikai" (drinking parties) to build consensus behind the scenes using the French-DeGroot model.
-   **Automated MVP Construction**: Generate high-fidelity React/Tailwind UI from your Lean Canvas using v0.dev.
-   **Business Governance & Ringi-sho**: Automated financial analysis (LTV/CAC, ROI) and generation of a formal "Ringi-sho" approval document to secure executive buy-in.
-   **Pyxel Retro UI**: A gamified RPG-style interface for observing the simulation without personal emotional attachment ("De-identification").
-   **Modular Architecture**: Designed for scalability and maintainability with strict schema validation and separated responsibilities.

## 📋 Prerequisites

-   **Python 3.12+**
-   **uv** (Modern Python package manager)
-   **API Keys**:
    -   `OPENAI_API_KEY` (GPT-4o recommended)
    -   `TAVILY_API_KEY` (For market research)
    -   `V0_API_KEY` (For MVP Generation)

## 🛠 Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/your-org/jtc2-0.git
    cd jtc2-0
    ```

2.  **Install dependencies**
    ```bash
    uv sync
    ```

3.  **Configure Environment**
    Create a `.env` file in the root directory:
    ```bash
    OPENAI_API_KEY=sk-...
    TAVILY_API_KEY=tvly-...
    V0_API_KEY=v0-...
    ```


## 🎓 Interactive Tutorial & UAT (Beginners Start Here!)

To experience the "aha moment" without needing complex API setup, we provide an interactive tutorial powered by **Marimo**. It uses mock data by default, so you can run it immediately!

1. **Install dependencies (including marimo)**
   ```bash
   uv sync
   ```

2. **Run the interactive notebook**
   ```bash
   uv run marimo edit tutorials/UAT_AND_TUTORIAL.py
   ```
   *(This opens a browser window where you can run cells sequentially and see the system in action!)*

3. **Or run it directly in the terminal as a script:**
   ```bash
   uv run python tutorials/UAT_AND_TUTORIAL.py
   ```

## 🚀 Usage

**Ingest Customer Transcripts:**

First, feed the system with real-world data (e.g., interview notes):

```bash
uv run main.py --ingest ./path/to/interview.txt
```

**Start the Ideation & Simulation:**

```bash
uv run main.py "AI for Agriculture"
```

The system will:
1.  Research the topic and generate 10 Lean Canvas drafts.
2.  Ask you to select one "Plan A" to proceed.
3.  Launch the **JTC Simulation** where agents debate the plan.
4.  The **CPO Agent** will intervene after the meeting to provide data-backed mentoring based on your ingested transcripts.
5.  The **Nemawashi Engine** will analyze the political landscape and advise on who to influence first.
6.  The **Builder Agent** will construct an MVP Spec and generate a UI URL via v0.dev.

## 🏗 Architecture

**Directory Structure:**

```ascii
.
├── src/
│   ├── agents/             # Agent Logic (Ideator, CPO, Personas, Builder)
│   ├── core/               # Core Logic
│   │   ├── nemawashi/      # Consensus Building Package (Logic, Analytics, Nomikai)
│   │   ├── simulation.py   # Simulation Graph
│   │   └── config.py       # Configuration & Validation
│   ├── data/               # RAG Engine & Ingestion
│   ├── domain_models/      # Pydantic Schemas (LeanCanvas, Politics, GlobalState, MVP)
│   ├── tools/              # API Wrappers (Tavily, V0Client)
│   ├── ui/                 # Pyxel Renderer
│   └── main.py             # CLI Entry Point
├── tests/                  # Unit & UAT Tests
├── dev_documents/          # Specs & Logs
└── pyproject.toml          # Project Configuration
```

## 🗺 Roadmap

-   **Cycle 1: Foundation & Ideation (Completed)**
-   **Cycle 2: JTC Simulation (Completed)**
-   **Cycle 3: Real World Connection (RAG) (Completed)**
-   **Cycle 4: Consensus Building (Nemawashi) (Completed)**
-   **Cycle 5: MVP Generation (Completed)**
-   **Cycle 6: Governance & Finalization (Completed)**

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
