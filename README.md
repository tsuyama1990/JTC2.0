# The JTC 2.0: Enterprise Business Accelerator

![Status](https://img.shields.io/badge/Status-Cycle_1_Complete-green)
![Python](https://img.shields.io/badge/Python-3.12+-blue)

**The JTC 2.0** is a paradigm-shifting multi-agent system that fuses the rigorous methodology of **"Startup Science"** with the complex organizational dynamics of **Traditional Japanese Companies (JTCs)**. It is not just a chatbot; it is a role-playing simulation where your business ideas are subjected to "Gekizume" (harsh feedback) by AI agents, validated against real customer interviews, and automatically built into MVPs.

## 🚀 Overview

-   **What**: An AI-powered co-founder that helps you brainstorm, validate, and simulate the organizational resistance to new business ideas.
-   **Why**: To help intrapreneurs navigate the "Valley of Death" in large organizations by simulating the harsh reality of corporate decision-making before pitching to real stakeholders.
-   **How**: Uses **LangGraph** to orchestrate specialized agents (Ideator, Finance, Sales) and **Tavily** for real-time market research.

## ✨ Features (Cycle 1 Verified)

-   **Automated Ideation Engine**: Generates 10 distinct, research-backed Lean Canvas business ideas from a single topic.
-   **Market Research Integration**: Automatically pulls "Emerging Trends" and "Painful Problems" using Tavily Search API.
-   **Strict Schema Validation**: All ideas are guaranteed to follow the Lean Canvas structure using Pydantic models.
-   **Interactive Selection**: CLI interface for reviewing and selecting the "Plan A" to proceed with.

## 📋 Prerequisites

-   **Python 3.12+**
-   **uv** (Modern Python package manager)
-   **API Keys**:
    -   `OPENAI_API_KEY` (GPT-4o recommended)
    -   `TAVILY_API_KEY` (For market research)

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
    ```

## 🚀 Usage

**Run the Ideation Engine:**

```bash
uv run main.py "AI for Agriculture"
```

Or simply run interactively:

```bash
uv run main.py
```

The system will:
1.  Research the topic.
2.  Generate 10 Lean Canvas drafts.
3.  Ask you to select one to proceed (Gate 1).

## 🏗 Architecture

**Directory Structure:**

```ascii
.
├── src/
│   ├── agents/             # Agent Logic (Ideator)
│   ├── core/               # LangGraph Workflow & Config
│   ├── domain_models/      # Pydantic Schemas (LeanCanvas, GlobalState)
│   ├── tools/              # API Wrappers (Tavily)
│   └── main.py             # CLI Entry Point
├── tests/                  # Unit & UAT Tests
├── dev_documents/          # Specs & Logs
└── pyproject.toml          # Project Configuration
```

## 🗺 Roadmap

-   **Cycle 1: Foundation & Ideation (Completed)**
-   **Cycle 2**: JTC Simulation (Proxy & Meeting)
-   **Cycle 3**: Real World Connection (RAG)
-   **Cycle 4**: Consensus Building (Nemawashi)
-   **Cycle 5**: MVP Generation
-   **Cycle 6**: Governance & Finalization

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
