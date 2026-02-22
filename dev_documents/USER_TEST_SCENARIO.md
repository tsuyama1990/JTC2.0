# User Test Scenario & Tutorial Master Plan

## 1. Tutorial Strategy: "The Zero-to-One Experience"

This document defines the strategy for onboarding users to "The JTC 2.0" and verifying the system's functionality through a unified executable tutorial.

### Core Philosophy
*   **Playable Documentation**: Documentation that you can run is better than documentation you just read. We use **Marimo** (`.py` files executed as reactive notebooks) to create an interactive tutorial.
*   **Dual Mode Execution**: The tutorial must run in two modes:
    1.  **Mock Mode (CI/Default)**: Uses pre-recorded or dummy responses for OpenAI/Tavily/v0. This allows users to "feel" the flow without spending API credits or waiting for network calls. It is also used for GitHub Actions.
    2.  **Real Mode**: Uses actual API keys (`.env`) to generate real ideas, conduct real searches, and build real UIs.

### The Narrative Arc
The tutorial follows the journey of a disgruntled JTC employee named "Tanaka-san" (the User).
1.  **Day 1 (Cycle 01)**: Tanaka-san types "AI for Cats" and gets 10 ideas. He picks one.
2.  **Day 2 (Cycle 02)**: He faces the "Hell Meeting". Finance and Sales destroy his idea.
3.  **Day 3 (Cycle 03)**: He goes to the "Roof" (CPO) and learns he needs data. He uploads a fake interview.
4.  **Day 4 (Cycle 04)**: He performs "Nemawashi" (Lobbying) to win over the department heads.
5.  **Day 5 (Cycle 05)**: He gets approval and instantly generates a website (MVP).

## 2. Tutorial Plan: `tutorials/UAT_AND_TUTORIAL.py`

We will create a **SINGLE** Marimo file named `tutorials/UAT_AND_TUTORIAL.py`. This file serves as both the primary End-to-End Test and the User Manual.

### File Structure (Conceptual)

```python
import marimo as mo
import os

# --- Section 1: Introduction ---
mo.md("# Welcome to The JTC 2.0")
mo.md("This interactive tutorial will guide you through the process of launching a startup within a traditional Japanese company.")

# --- Section 2: Configuration ---
# Toggle for Mock Mode
mock_mode = mo.ui.switch(label="Mock Mode (No API Cost)", value=True)
mo.md(f"Current Mode: {'MOCK' if mock_mode.value else 'REAL'}")

# --- Section 3: Cycle 01 (Idea Gen) ---
topic_input = mo.ui.text_area(label="Enter a business topic", value="AI for Elderly Care")
# Execution button
gen_btn = mo.ui.button(label="Generate Ideas")

# Logic to call backend...
if gen_btn.value:
    # Call LangGraph...
    ideas = app.invoke(...)
    mo.ui.table(ideas)

# --- Section 4: Cycle 02 (Hell Meeting) ---
# ... Visualization of the battle ...

# --- Section 5: Cycle 03 (The Pivot) ---
# ... Upload widget for transcripts ...

# --- Section 6: Cycle 04 (Nemawashi) ---
# ... Network graph visualization ...

# --- Section 7: Cycle 05 (Launch) ---
# ... Iframe for v0.dev URL ...
```

### Key Technical Requirements
1.  **State Persistence**: The Marimo notebook must maintain the `AgentState` in memory between cells.
2.  **Dependency Injection**: The backend code (`src/core/graph.py`) must accept a `mock_mode` flag or injected clients to switch between Real/Mock execution.
3.  **Error Handling**: If an API call fails (in Real Mode), the notebook should display a friendly error toast, not a stack trace.

## 3. Tutorial Validation (CI/CD)

To ensure this master tutorial never breaks, we will treat it as a test suite.

### Automated Validation Steps
1.  **Install**: `uv sync`
2.  **Lint**: `ruff check tutorials/UAT_AND_TUTORIAL.py`
3.  **Headless Execution**: We will run a script that executes the Marimo file top-to-bottom (using Marimo's CLI or test runner if available, or a custom script) with `MOCK_MODE=True`.
4.  **Assertion**: The script will verify that the final cell contains a "Success" message or a valid object (e.g., `state['mvp_url']` is not None).

### User Validation Steps
1.  User clones repo.
2.  User runs `marimo edit tutorials/UAT_AND_TUTORIAL.py`.
3.  User steps through the story.
4.  User learns the system logic *by doing*.

## 4. Specific Test Cases Mapped to Cycles

| Cycle | Scenario ID | Description | Expected Outcome in Tutorial |
| :--- | :--- | :--- | :--- |
| **01** | `UAT-C01-01` | Generate 10 Ideas | A table of 10 rows appears. |
| **02** | `UAT-C02-01` | Hell Meeting | Text bubbles from "Finance" appear in red. |
| **03** | `UAT-C03-01` | Mom Test Upload | System parses text file and updates Empathy Map. |
| **04** | `UAT-C04-01` | Consensus Win | Graph nodes change color (Red -> Green). |
| **05** | `UAT-C05-01` | MVP Launch | A valid URL is displayed. |

## 5. Conclusion

By consolidating the UAT and Tutorial into a single `tutorials/UAT_AND_TUTORIAL.py` file, we achieve:
*   **Simplicity**: Users only need to run one command.
*   **Maintainability**: Docs and Tests are the same artifact.
*   **Engagement**: Learning is active, not passive.
