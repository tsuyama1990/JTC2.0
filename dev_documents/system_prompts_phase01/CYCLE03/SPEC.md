# Cycle 3 Specification: Real World Connection (RAG & CPO)

## 1. Summary

The primary objective of **Cycle 3** is to inject **Reality** into the simulation via **LlamaIndex** and the **CPO (Chief Product Officer) Agent**. This cycle enables the system to ingest unstructured primary data—specifically user interview transcripts (from tools like PLAUD NOTE) or market reports.

The CPO Agent acts as a mentor who operates in the "Roof Phase" (informal feedback after the meeting). Unlike the antagonistic Finance/Sales managers, the CPO uses the ingested data to provide constructive, fact-based advice ("Here is what the customer actually said..."). This implements the crucial **"Mom Test"** validation loop.

## 2. System Architecture

### 2.1. File Structure

This cycle adds the Data Layer. **Bold** files are new or modified.

```ascii
.
├── dev_documents/
├── src/
│   ├── agents/
│   │   ├── ...
│   │   └── **cpo.py**          # CPO Agent (Mentor)
│   ├── core/
│   │   ├── ...
│   │   └── state.py        # Updated GlobalState with RAG Context
│   ├── **data/**
│   │   ├── **__init__.py**
│   │   ├── **loader.py**       # Transcript Loader (txt, md)
│   │   └── **rag.py**          # LlamaIndex Interface
│   ├── ui/
│   │   └── ...
│   └── main.py
├── tests/
│   └── **test_rag.py**         # Unit Tests for Retrieval
├── .env.example
├── pyproject.toml
└── README.md
```

### 2.2. Component Interaction

1.  **User** uploads a transcript file (e.g., `interview.txt`) via CLI or GUI.
2.  **Loader** parses the text.
3.  **RAG Engine** (LlamaIndex) chunks and indexes the text into a local **Vector Store**.
4.  **CPO Agent** queries the Vector Store for insights related to the `selected_idea`'s riskiest assumptions.
5.  **CPO Agent** generates a "Mentor's Advice" message based on the retrieved facts, suggesting a pivot or validation.

## 3. Design Architecture

### 3.1. Domain Models (`src/core/state.py`)

```python
class Transcript(BaseModel):
    source: str
    content: str
    date: str

class GlobalState(BaseModel):
    # ... previous fields ...
    transcripts: List[Transcript] = []
    rag_index_path: str = "./vector_store"
```

### 3.2. RAG Design (`src/data/rag.py`)

-   **Library**: `llama-index`.
-   **Store**: Local `VectorStoreIndex` (simple JSON or ChromaDB if needed).
-   **Functionality**:
    -   `ingest_text(text: str)`: Creates embeddings.
    -   `query(question: str)`: Returns top-k relevant chunks.

### 3.3. CPO Agent (`src/agents/cpo.py`)

-   **Persona**: Experienced, calm, data-driven. "Let's look at the facts."
-   **System Prompt**: "You are a CPO. You ignore opinions and focus on customer evidence. You use the RAG tool to find contradictions between the Plan and the Customer Interview."

## 4. Implementation Approach

1.  **Dependencies**: Install `llama-index`, `llama-index-embeddings-openai`.
2.  **RAG Implementation**: Create `src/data/rag.py` to wrap LlamaIndex. Implement a simple persistent storage.
3.  **CPO Agent**: Implement `CPOAgent`. It should have a `consult_rag` tool.
4.  **Integration**: Add the CPO node to the LangGraph. The flow should be: Simulation -> CPO (Roof Phase) -> Pivot Decision.
5.  **CLI Update**: Add a command to ingest a file: `python main.py --ingest interview.txt`.

## 5. Test Strategy

### 5.1. Unit Testing
-   **File**: `tests/test_rag.py`
-   **Scope**:
    -   Verify that text is correctly chunked and indexed.
    -   Verify that `query()` returns relevant segments for a known input.

### 5.2. Integration Testing
-   **Scope**:
    -   Ingest a mock interview where a customer says "I hate subscriptions."
    -   Run the CPO Agent with a subscription-based idea.
    -   Verify the CPO Agent cites the "hate subscriptions" quote in its advice.
