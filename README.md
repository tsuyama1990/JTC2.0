# The JTC 2.0: Enterprise Business Accelerator (Remastered Edition)

![Status](https://img.shields.io/badge/Status-Architected-green)
![Python](https://img.shields.io/badge/Python-3.12+-blue)
![LangGraph](https://img.shields.io/badge/Agent_Engine-LangGraph-orange)
![Pydantic](https://img.shields.io/badge/Data_Validation-Pydantic-purple)

**The JTC 2.0 (Remastered Edition)** is an intelligent agent-based simulation and startup validation tool. It guides your rough ideas through rigorous ideation using LangGraph orchestrators and strictly typed data schemas, acting as an advanced Requirements Engineering Engine.

## 🚀 Key Features

*   **Ideation Engine & Research Validation:** Transforms basic topics into structured 10 distinct Lean Canvas drafts using live search data.
*   **Pydantic Schema Validation:** Employs strictly typed data models throughout the lifecycle to guarantee consistency and remove hallucinatory logic.
*   **JTC Meeting Simulation:** Run realistic multi-agent "Gekizume" (harsh feedback) debates with specialized Persona Agents (Finance Manager, Sales Manager, etc.).
*   **Gamified Retro UI:** Review the ongoing debates visually via a Pyxel-based Retro RPG interface, providing a psychological buffer through the Proxy Agent.
*   **Reality Validation via RAG:** Ground decision-making in primary data using LlamaIndex by ingesting user interviews and transcripts to ensure the "Mom Test" is passed.
*   **Nemawashi (Consensus Building):** Mathematically model and simulate the invisible layer of organizational politics using the French-DeGroot Model. Identify Key Influencers and simulate informal "Nomikai" events to strategically build support.
*   **AI Coder Prompt Generation:** Automatically compiles your validated Lean Canvas, Customer Journey, and Mental Models into an `AgentPromptSpec` designed to be copy-pasted into Cursor or Windsurf to instantly generate your frontend MVP.
*   **Governance & Ringi-sho Finalization:** Applies a business governance check utilizing AARRR metrics and real-time financial projections (LTV/CAC) to generate a formal Japanese Approval Document (Ringi-sho).

## 📋 Prerequisites

-   **Python 3.12+**
-   **uv** package manager
-   **API Keys**: `OPENAI_API_KEY`, `TAVILY_API_KEY` configured in your `.env`.

## 🛠 Installation & Setup

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
    ```bash
    cp .env.example .env
    # Add your keys: OPENAI_API_KEY, TAVILY_API_KEY
    # UV_PROJECT_ENVIRONMENT=".venv"
    ```

## 🚀 Usage

Launch the ideation process by entering your core business topic. The orchestrator will research your topic and present validated lean canvas proposals for your review.

```bash
uv run main.py "AI solutions for independent plumbers"
```
*You'll be prompted to verify and choose a Plan A directly within the CLI.*

You can also use Marimo notebooks to run through the full "Fitness Journey Workflow" visually in your browser.

```bash
uv run marimo edit tutorials/UAT_AND_TUTORIAL.py
```

## 📂 Project Structure

```ascii
.
├── src/
│   ├── agents/             # Persona definitions (Ideator, CPO, Governance, etc.)
│   ├── core/               # LangGraph orchestration, Config, Metrics, and LLM wrappers
│   ├── data/               # LlamaIndex RAG implementation and parsers
│   ├── domain_models/      # Strict Pydantic schemas (LeanCanvas, Metrics, VPC, MentalModel)
│   ├── ui/                 # Pyxel "Retro RPG" rendering engine
│   └── main.py             # CLI Entry Point
├── tests/                  # Unit, Integration, and Mock Mode E2E tests
├── dev_documents/          # Architectural Specifications and UAT Plans
├── tutorials/              # Marimo notebooks for interactive validation
└── pyproject.toml          # Strict dependency and linter configurations
```

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.