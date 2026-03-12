1. **Understand Cycle 05 scope:**
   - Modify `spec_generation_node` (Builder Agent) to aggregate the entire `GlobalState` (VPC, Mental Model, Journey, Sitemap, 3H Review feedback) and apply "subtraction thinking" to output `AgentPromptSpec`.
   - Modify `experiment_planning_node` to output `ExperimentPlan`.
   - Implement `[HITL Gate 3]` logic (trigger Pyxel approval animation and generate PDFs - wait, the spec says "triggering the final Pyxel approval animation and generating the corresponding PDFs", maybe this means writing Markdown files via `FileService` since we don't have PDFs for Spec/Experiment). The `FileService` needs a method to generate/write the nicely formatted Markdown.
   - Refactor `BuilderAgent` properly.
   - Update tests for Cycle 05:
     - Data aggregation test (complex `GlobalState` -> `spec_generation_node`).
     - Output formatting test (Markdown, Mermaid sanitization).
     - E2E Path Traversal Prevention in file output (`../../../etc/passwd` checks).

2. **Steps:**
   - **Step 1:** Add FileService methods to generate Markdown files for `AgentPromptSpec` and `ExperimentPlan`.
   - **Step 2:** Refactor `BuilderAgent` in `src/agents/builder.py`. Provide better prompt for "subtraction thinking". Ensure we return the state correctly. Wait, they are currently returning simple `{"agent_prompt_spec": result}` and `{"experiment_plan": result}`. We need to implement the FileService write inside `spec_generation_node` and `experiment_planning_node` or the agent.
   - **Step 3:** Implement the markdown file writing logic in `src/core/nodes.py` (for `spec_generation_node` and `experiment_planning_node`). Also apply Path Traversal protection in `FileService`.
   - **Step 4:** Tests! Write `tests/unit/test_builder_agent.py` or update it, `tests/unit/test_nodes_cycle05.py`. Wait, testing path traversal in `FileService` should be added.
