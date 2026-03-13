# The JTC 2.0: Enterprise Business Accelerator (Remastered Edition)

![Status](https://img.shields.io/badge/Status-Architected-green)
![Python](https://img.shields.io/badge/Python-3.12+-blue)
![LangGraph](https://img.shields.io/badge/Agent_Engine-LangGraph-orange)
![Pydantic](https://img.shields.io/badge/Data_Validation-Pydantic-purple)

**The JTC 2.0 (Remastered Edition)** is an intelligent agent-based simulation and startup validation tool. It guides your rough ideas through rigorous ideation using LangGraph orchestrators and strictly typed data schemas, acting as an advanced Requirements Engineering Engine.

## 🚀 Key Features

*   **Ideation Engine & Research Validation:** Transforms basic topics into structured 10 distinct Lean Canvas drafts using live search data.
*   **Pydantic Schema Validation:** Employs strictly typed data models throughout the lifecycle to guarantee consistency and remove hallucinatory logic.
*   **Decoupled Orchestration:** Ensures separation of business logic running in LangGraph from local user validations via terminal and simulation nodes.
*   **JTC Meeting Simulation:** Run realistic multi-agent "Gekizume" (harsh feedback) debates with specialized Persona Agents (Finance Manager, Sales Manager, etc.).
*   **Gamified Retro UI:** Review the ongoing debates visually via a Pyxel-based Retro RPG interface, providing a psychological buffer through the Proxy Agent.
*   **Reality Injection via RAG and CPO Agent:** Ingests raw customer interview transcripts into a LlamaIndex Vector Database to ground the debate. The CPO agent uses this factual data to validate or invalidate assumptions directly against the Value Proposition Canvas and Alternative Analysis models.
*   **Automated Specification Generation:** Transforms validated concepts into flawless, universally compatible `AgentPromptSpec.md` markdown specifications for AI coding tools.
*   **Experiment Planning:** Rigorously generates `ExperimentPlan.md` outlining the MVP execution, AARRR metric targets, and pivot conditions based on your generated idea.
*   **Governance & Financial Approval:** Mathematically simulates influence consensus building and financial viability (LTV, CAC, ROI) to automatically construct a Japanese-style corporate approval document ("Ringi-sho").

## 📋 Prerequisites

-   **Python 3.12+**
-   **uv** package manager
-   **API Keys**: `OPENAI_API_KEY`, `TAVILY_API_KEY`, `V0_API_KEY` configured in your `.env`.

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

Launch the ideation process by entering your core business topic. The orchestrator will research your topic and present 10 distinct validated lean canvas proposals for your review.

```bash
uv run main.py "AI solutions for independent plumbers"
```
*You'll be prompted to verify and choose a Plan A directly within the CLI.*

You can also use Marimo notebooks to run through the full "Fitness Journey Workflow" visually in your browser. This notebook acts as the ultimate User Acceptance Test (UAT), guiding you through scenarios such as Mock Mode, Real Mode, and Circuit Breaker testing.

```bash
uv run marimo edit tutorials/UAT_AND_TUTORIAL.py
```

## 📂 Project Structure

```ascii
.
├── src/
│   ├── agents/             # Persona definitions (Ideator, CPO, Hacker, etc.)
│   ├── core/               # LangGraph orchestration, Config, and LLM wrappers
│   ├── data/               # LlamaIndex RAG implementation and parsers
│   ├── domain_models/      # Strict Pydantic schemas (LeanCanvas, VPC, MentalModel)
│   ├── ui/                 # Pyxel "Retro RPG" rendering engine
│   └── main.py             # CLI Entry Point
├── tests/                  # Unit, Integration, and Mock Mode E2E tests
├── dev_documents/          # Architectural Specifications and UAT Plans
├── tutorials/              # Marimo notebooks for interactive validation
└── pyproject.toml          # Strict dependency and linter configurations
```

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.