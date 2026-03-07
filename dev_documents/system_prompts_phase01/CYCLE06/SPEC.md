# Cycle 6 Specification: Governance & Finalization

## 1. Summary

The primary objective of **Cycle 6** is to apply the final layer of **Business Governance** and package the entire journey into a formal **Approval Document (Ringi-sho)**. This cycle implements the "Product-Market Fit" checks using **AARRR Metrics** (Acquisition, Activation, Retention, Revenue, Referral) and financial projections (LTV/CAC).

The system will also perform a final **Safety Check** using LangSmith traces to ensure no harmful content was generated, and then produce a Markdown or PDF report summarizing the Lean Canvas, Interview Data, Nemawashi Status, and MVP URL.

## 2. System Architecture

### 2.1. File Structure

This cycle adds the Governance Layer. **Bold** files are new or modified.

```ascii
.
├── dev_documents/
├── src/
│   ├── agents/
│   │   ├── ...
│   │   └── **governance.py**   # Compliance & Document Agent
│   ├── core/
│   │   ├── ...
│   │   └── **metrics.py**      # Financial Calculators
│   └── main.py
├── tests/
│   └── **test_metrics.py**     # Unit Tests for Financials
├── .env.example
├── pyproject.toml
└── README.md
```

### 2.2. Component Interaction

1.  **Orchestrator** passes the final state to the **Governance Agent**.
2.  **Metrics Engine** calculates projected LTV, CAC, and Payback Period based on industry benchmarks (via Tavily).
3.  **Governance Agent** checks for "Red Flags" (e.g., LTV < 3 * CAC).
4.  **Document Generator** compiles all data into a `RINGI_SHO.md`.
5.  **System** outputs the final report path.

## 3. Design Architecture

### 3.1. Domain Models (`src/core/metrics.py`)

```python
class Financials(BaseModel):
    cac: float
    ltv: float
    payback_months: float
    roi: float

class RingiSho(BaseModel):
    title: str
    executive_summary: str
    financial_projection: Financials
    risks: List[str]
    approval_status: str = "Draft"
```

## 4. Implementation Approach

1.  **Metrics Logic**: Implement `calculate_ltv_cac(churn_rate, arpu, cpa)` in `src/core/metrics.py`.
2.  **Governance Agent**: Create an agent that takes the Lean Canvas and Metrics, and writes a formal business letter.
3.  **Tavily Integration**: Use Tavily to fetch "Average CAC for [Industry]" to use as a baseline if no real data exists.
4.  **Final Output**: Create a template for the Ringi-sho and fill it with Jinja2 or f-strings.

## 5. Test Strategy

### 5.1. Unit Testing
-   **File**: `tests/test_metrics.py`
-   **Scope**:
    -   Verify LTV formula: $ARPU / Churn$.
    -   Verify Payback Period: $CAC / (ARPU \times Margin)$.

### 5.2. Integration Testing
-   **Scope**:
    -   Run the Governance Agent with a high-churn scenario.
    -   Verify it flags the risk in the final report.
    -   Verify the `RINGI_SHO.md` file is created on disk.
