# Cycle 5 Specification: MVP Generation (v0.dev)

## 1. Summary

The primary objective of **Cycle 5** is to bridge the gap between "Idea" and "Execution" by automating the creation of a **Minimum Viable Product (MVP)**. We will integrate the **v0.dev API** (by Vercel) to generate high-fidelity React/Tailwind CSS user interfaces directly from the finalized Lean Canvas.

This cycle implements **Gate 3 (Problem-Solution Fit)**, where the user must prune the feature list down to a single "Must-Have" feature before generation. The system then constructs a detailed prompt for v0.dev and returns a live URL for the prototype.

## 2. System Architecture

### 2.1. File Structure

This cycle adds the Code Generation Layer. **Bold** files are new or modified.

```ascii
.
├── dev_documents/
├── src/
│   ├── agents/
│   │   ├── ...
│   │   └── **builder.py**      # MVP Architect Agent
│   ├── core/
│   │   ├── ...
│   │   └── state.py        # GlobalState with MVPSpec
│   ├── tools/
│   │   ├── ...
│   │   └── **v0_client.py**    # v0.dev API Wrapper
│   └── main.py
├── tests/
│   └── **test_v0.py**          # Unit Tests for API Client
├── .env.example
├── pyproject.toml
└── README.md
```

### 2.2. Component Interaction

1.  **User** confirms the single "Core Feature" to build.
2.  **Builder Agent** constructs a `MVPSpec` (Detailed UI requirements).
3.  **v0 Client** sends the spec to the v0.dev `generate` endpoint.
4.  **v0.dev** returns a `generation_id` or `url`.
5.  **System** displays the URL in the console/UI.

## 3. Design Architecture

### 3.1. Domain Models (`src/core/state.py`)

```python
class MVPSpec(BaseModel):
    app_name: str
    core_feature: str
    ui_style: str = "Modern, Clean, Corporate"
    components: List[str] = ["Hero Section", "Feature Demo", "Call to Action"]

class GlobalState(BaseModel):
    # ... previous fields ...
    mvp_spec: Optional[MVPSpec] = None
    mvp_url: Optional[str] = None
```

### 3.2. v0 Client (`src/tools/v0_client.py`)

-   **Endpoint**: `https://api.v0.dev/chat/completions` (or specific generation endpoint).
-   **Auth**: `V0_API_KEY` (or similar Vercel token).
-   **Function**: `generate_ui(prompt: str) -> str` (Returns URL).

## 4. Implementation Approach

1.  **Configuration**: Add `V0_API_KEY` to `.env`.
2.  **Tool Creation**: Implement `V0Client` class to handle HTTP requests to v0.dev.
3.  **Builder Agent**: Create `BuilderAgent`. Its job is to take the abstract `LeanCanvas.solution` and turn it into a concrete UI description (e.g., "A dashboard with a line chart and a sidebar").
4.  **Integration**: Add the Builder node to the LangGraph after the Consensus phase.
5.  **Gate 3 Logic**: Implement a check that forces the user to select only 1 feature if the list > 1.

## 5. Test Strategy

### 5.1. Unit Testing
-   **File**: `tests/test_v0.py`
-   **Scope**:
    -   Mock the HTTP request to v0.dev.
    -   Verify the prompt construction logic (e.g., ensures "React" and "Tailwind" are mentioned).

### 5.2. Integration Testing
-   **Scope**:
    -   Run the Builder Agent with a sample idea.
    -   Verify it produces a valid `MVPSpec`.
    -   (Optional) Call the actual API with a dry-run flag if available, or just log the prompt.
