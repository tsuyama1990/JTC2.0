# Cycle 03 Specification: Primary Info Injection (RAG) & Customer-Problem Fit

## 1. Summary

Cycle 03 addresses the most critical failure mode of AI-driven business generation: "Hallucinated Market Fit". In Cycle 02, the system simulated a "Hell Meeting" based on external *secondary* data (Tavily). Now, in **Gate 2 (Customer-Problem Fit)**, we force the user to leave the building and collect *primary* data.

The core feature of this cycle is the **Integration of LlamaIndex for RAG (Retrieval-Augmented Generation)**. The user is required to conduct "The Mom Test" interviews, record them (e.g., using PLAUD NOTE), and upload the transcripts. The system then ingests these transcripts, chunks them, and stores them in a local Vector DB.

Crucially, the "Department Head Agents" (Finance, Sales) are reprogrammed to prioritize this local data over their general knowledge. If the user claims "People will pay $100", but the transcript says "That's too expensive", the agents will quote the transcript to block the project. Conversely, if the transcript proves the need, the agents must concede.

This cycle creates a closed-loop verification system where "Fact" beats "Theory". It culminates in the generation of a data-backed **Empathy Map** and the identification of the **Riskiest Assumption**.

## 2. System Architecture

We are adding the Data Layer (RAG) and enhancing the State Machine to handle file uploads.

### File Structure
**Bold files** are to be created or modified in this cycle.

```ascii
.
├── src/
│   ├── agents/
│   │   ├── **analyst.py**        # New Agent to analyze transcripts
│   │   └── opponents.py          # Modified to use RAG tool
│   ├── core/
│   │   ├── **state.py**          # Added 'interview_transcripts', 'empathy_map'
│   │   └── graph.py              # New node: 'ingest_data'
│   ├── data/
│   │   ├── **rag.py**            # LlamaIndex Setup (Ingestion, Indexing)
│   │   └── **models.py**         # EmpathyMap Schema
│   └── ui/
│       └── **file_upload.py**    # CLI/UI logic to read text files
└── tests/
    ├── **test_rag.py**
    └── **test_analyst.py**
```

### Core Components Blueprints

#### `src/data/rag.py`
Sets up the Vector Store (e.g., ChromaDB or simple in-memory FAISS for MVP).
```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Document

def ingest_transcript(text: str, interview_id: str):
    """
    Chunks the text and adds it to the vector index with metadata.
    """
    doc = Document(text=text, metadata={"source": interview_id})
    index = VectorStoreIndex.from_documents([doc])
    index.storage_context.persist(persist_dir="./storage")
    return index

def query_knowledge_base(query: str) -> str:
    """
    Retrieves relevant snippets from the interviews.
    """
    # ... loading logic ...
    return query_engine.query(query).response
```

#### `src/agents/analyst.py`
A neutral agent that synthesizes the interviews.
```python
def call_analyst_agent(state: AgentState):
    """
    Reads all transcripts and builds an Empathy Map.
    Identifies the Riskiest Assumption.
    """
    # 1. Retrieve key pains/gains from RAG
    # 2. Fill EmpathyMap schema
    return {"empathy_map": ...}
```

#### `src/core/state.py` (Extended)
```python
class EmpathyMap(BaseModel):
    says: List[str]
    thinks: List[str]
    does: List[str]
    feels: List[str]
    pain: List[str]
    gain: List[str]

class AgentState(TypedDict):
    # ... existing ...
    # List of raw text or file paths
    interview_transcripts: List[str]
    # The synthesized map
    empathy_map: Optional[EmpathyMap]
    # The assumption validated/invalidated
    riskiest_assumption: str
```

## 3. Design Architecture

### Domain Models (`src/data/models.py`)

1.  **`TranscriptSegment`**:
    *   Represents a chunk of conversation.
    *   Fields: `speaker` (User/Customer), `text`, `sentiment` (Positive/Negative/Neutral).
    *   **Why**: To allow agents to filter for "Negative feedback about price".

2.  **`ValidationResult`**:
    *   The outcome of Gate 2.
    *   Fields: `is_validated` (bool), `evidence_quote` (str), `pivot_needed` (bool).

### The "Fact Priority" Invariant
We must design the prompts for the Department Head Agents such that RAG context always overrides pre-trained knowledge.
*   *Prompt Pattern*: "You have access to interview transcripts. If the user's claim conflicts with the transcript, REJECT the claim citing the transcript. If the transcript supports the claim, ACCEPT it even if it sounds counter-intuitive."

### Persistence of Vector Data
Since `LangGraph` state is typically JSON-serializable, we cannot store the entire `VectorStoreIndex` object in the state. Instead, `src/data/rag.py` manages a persistent on-disk storage (e.g., `./storage/`), and the State merely tracks the *existence* of valid data (e.g., `has_interviews=True`).

## 4. Implementation Approach

### Step 1: LlamaIndex Setup
1.  Install `llama-index`.
2.  Implement `src/data/rag.py`.
3.  Create a function `create_index(texts: List[str])` that saves to disk.
4.  Create a function `query_index(query: str)` that loads from disk and answers.
5.  **Verification**: Write a script that indexes a dummy text ("My cat loves pizza") and queries "What does the cat eat?".

### Step 2: The Empathy Map Agent
1.  Create `src/agents/analyst.py`.
2.  Define the `EmpathyMap` Pydantic model.
3.  Implement the logic: `Analyst` queries the RAG engine for "What are the customer's frustrations?" -> Populates `EmpathyMap.pain`.
4.  **Verification**: Feed a transcript of a complaining customer. Assert `pain` list is not empty.

### Step 3: Modifying Opponents (The Pivot)
1.  Update `src/agents/opponents.py`.
2.  Add a step where Opponents query the RAG engine before speaking.
    *   *Finance*: "Does the customer mention budget?"
    *   *Sales*: "Does the customer express intent to buy?"
3.  **Verification**: Create a test case where the transcript says "I have zero budget". Ensure Finance Agent quotes this.

### Step 4: The Gate 2 Logic
1.  Update `src/core/graph.py`.
2.  Insert the `ingest_data` node (or a manual state update via UI).
3.  Add a conditional edge: If `riskiest_assumption` is INVALIDATED -> Loop back to Idea Generation (Pivot). If VALIDATED -> Proceed to Cycle 04.

## 5. Test Strategy

### Unit Testing Approach (Min 300 words)
*   **RAG Ingestion**: We will test that `src/data/rag.py` handles various text formats.
    *   *Test*: Ingest a very short text. Ingest a very long text (forcing chunking). Assert no errors.
*   **Empathy Map Schema**:
    *   *Test*: Create an `EmpathyMap` with empty lists. Ensure it validates (it's valid to have no data yet).
    *   *Test*: Create an `EmpathyMap` with structured data. Serialize to JSON and back.
*   **Analyst Logic**:
    *   *Test*: Mock the `query_knowledge_base` function to return "The customer hates waiting."
    *   *Test*: Run the Analyst Agent. Assert that `EmpathyMap.pain` contains "waiting" or similar semantics.

### Integration Testing Approach (Min 300 words)
*   **The "Mom Test" Verification**: This is the key integration test.
    *   *Scenario*:
        1.  User Idea: "Uber for Dog Walking".
        2.  System State: `riskiest_assumption` = "People trust strangers with dogs."
        3.  Injection: User uploads a transcript where a customer says: "I would never let a stranger take my dog."
        4.  Agent Action: The Analyst Agent must flag `riskiest_assumption` as **FALSE**.
        5.  Workflow: The Graph must transition to a "Pivot Required" state, not "Gate Passed".
    *   *Verification*: Check the final state of the graph.
*   **Persistence Test**:
    *   *Scenario*: Ingest data, kill the process, restart the process.
    *   *Verification*: Can we still query the index? This ensures the vector store is correctly persisted to disk and reloaded.
*   **Hallucination Check**:
    *   *Scenario*: Upload a transcript about "Coffee". Ask the RAG about "Spaceships".
    *   *Verification*: The RAG should return "I don't know" or empty results, rather than making up facts about spaceships.
