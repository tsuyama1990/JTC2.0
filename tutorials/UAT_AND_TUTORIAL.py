import marimo

__generated_with = "0.9.14"
app = marimo.App(width="medium")


@app.cell
def __():
    import os
    import unittest.mock
    from unittest.mock import MagicMock, patch

    # 1. Setup Environment (Mock Keys)
    if "OPENAI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = "sk-mock-openai-key"
    if "TAVILY_API_KEY" not in os.environ:
        os.environ["TAVILY_API_KEY"] = "tv-mock-tavily-key"
    if "V0_API_KEY" not in os.environ:
        os.environ["V0_API_KEY"] = "mock-v0-key"

    print("Environment variables set.")
    return MagicMock, os, patch, unittest


@app.cell
def __(MagicMock, patch):
    # 2. Mock External Services

    # Mock OpenAI
    patch_openai = patch("langchain_openai.ChatOpenAI")
    mock_openai = patch_openai.start()
    mock_openai_instance = mock_openai.return_value

    # Mock Tavily
    patch_tavily = patch("src.tools.search.TavilyClient")
    mock_tavily = patch_tavily.start()
    mock_tavily_instance = mock_tavily.return_value
    mock_tavily_instance.search.return_value = {
        "results": [
            {"title": "Result 1", "url": "http://example.com/1", "content": "Content 1"},
            {"title": "Result 2", "url": "http://example.com/2", "content": "Content 2"},
        ]
    }

    # Mock RAG
    patch_rag = patch("src.data.rag.RAG")
    mock_rag_class = patch_rag.start()
    mock_rag_instance = mock_rag_class.return_value
    mock_rag_instance.query.return_value = "Mocked RAG Context: Customers hate the price."

    # Mock LlamaIndex OpenAI to prevent init errors in RAG if it were real
    patch_llama_openai = patch("llama_index.llms.openai.OpenAI")
    patch_llama_openai.start()
    patch_llama_embedding = patch("llama_index.embeddings.openai.OpenAIEmbedding")
    patch_llama_embedding.start()

    # Mock V0Client
    patch_v0 = patch("src.tools.v0_client.httpx.Client")
    mock_httpx = patch_v0.start()
    mock_httpx_instance = mock_httpx.return_value.__enter__.return_value
    mock_httpx_instance.post.return_value.status_code = 200
    mock_httpx_instance.post.return_value.json.return_value = {"url": "https://v0.dev/mock-result"}

    print("Mocks activated.")
    return (
        mock_httpx,
        mock_httpx_instance,
        mock_openai,
        mock_openai_instance,
        mock_rag_class,
        mock_rag_instance,
        mock_tavily,
        mock_tavily_instance,
        patch_llama_embedding,
        patch_llama_openai,
        patch_openai,
        patch_rag,
        patch_tavily,
        patch_v0,
    )


@app.cell
def __(MagicMock, mock_openai_instance):
    # 3. Smart LLM Mocking

    from src.agents.ideator import LeanCanvasList
    from src.agents.builder import FeatureList
    from src.domain_models.mvp import MVPSpec, MVPType
    from src.domain_models.lean_canvas import LeanCanvas

    # Mock for Ideator (LeanCanvasList)
    mock_runnable_ideas = MagicMock()
    mock_runnable_ideas.invoke.return_value = LeanCanvasList(canvases=[
        LeanCanvas(
            id=i,
            problem=["Problem A"],
            customer_segments=["Segment A"],
            unique_value_prop=f"Unique Value Prop {i}",
            solution=f"Solution {i}",
            status="draft"
        ) for i in range(10)
    ])

    # Mock for Builder (FeatureList)
    mock_runnable_features = MagicMock()
    mock_runnable_features.invoke.return_value = FeatureList(
        features=["Cat Translation", "Purr Analyzer", "Meow Synthesizer"]
    )

    # Mock for Builder (MVPSpec)
    mock_runnable_mvp = MagicMock()
    mock_runnable_mvp.invoke.return_value = MVPSpec(
        app_name="Cat AI",
        tagline="Meow",
        core_feature="Cat Translation",
        target_audience="Cat Owners",
        design_style="Playful",
        v0_prompt="Build a cat translator",
        components=["Header", "TranslatorInput"],
        tech_stack=["React", "Tailwind"]
    )

    # Mock for generic text (Finance/Sales Agents)
    from langchain_core.messages import AIMessage
    def mock_llm_invoke(input, **kwargs):
        return AIMessage(content="Mocked LLM Response: I have analyzed the plan and I have concerns about ROI.")

    # Side Effect Dispatcher
    def with_structured_output_side_effect(schema, **kwargs):
        if schema == LeanCanvasList:
            return mock_runnable_ideas
        if schema == FeatureList:
            return mock_runnable_features
        if schema == MVPSpec:
            return mock_runnable_mvp
        return mock_runnable_ideas # Fallback

    mock_openai_instance.with_structured_output.side_effect = with_structured_output_side_effect
    mock_openai_instance.invoke.side_effect = mock_llm_invoke

    print("Smart LLM Mock configured.")
    return (
        AIMessage,
        FeatureList,
        LeanCanvas,
        LeanCanvasList,
        MVPSpec,
        MVPType,
        mock_llm_invoke,
        mock_runnable_features,
        mock_runnable_ideas,
        mock_runnable_mvp,
        with_structured_output_side_effect,
    )


@app.cell
def __():
    # 4. Import Project Modules
    # Using relative imports or src based on environment
    from src.core.graph import create_app
    from src.domain_models.state import GlobalState, Phase
    from src.domain_models.transcript import Transcript
    from langgraph.checkpoint.memory import MemorySaver

    print("Modules imported.")
    return GlobalState, MemorySaver, Phase, Transcript, create_app


@app.cell
def __(GlobalState, MemorySaver, create_app):
    # 5. Initialize App
    memory = MemorySaver()
    workflow = create_app(checkpointer=memory)

    # Config for thread
    config = {"configurable": {"thread_id": "tutorial_user_1"}}

    print("App initialized.")
    return config, memory, workflow


@app.cell
def __(GlobalState, config, workflow):
    # 6. Scenario 1: Ideation (The Spark)
    print("\n--- Scenario 1: Ideation ---")

    initial_state = GlobalState(topic="AI for Cats")

    # Start Execution
    result = workflow.invoke(initial_state, config=config)

    # Verify State after Ideator
    current_state = workflow.get_state(config).values
    ideas_iter = current_state.get("generated_ideas")
    ideas = list(ideas_iter) if ideas_iter else []

    print(f"Generated {len(ideas)} ideas.")
    if len(ideas) != 10:
        raise AssertionError(f"Expected 10 ideas, got {len(ideas)}")

    print("Scenario 1 Passed: Ideas generated.")
    return current_state, ideas, result


@app.cell
def __(Phase, config, ideas, workflow):
    # 7. Scenario 1 Cont: Selection
    print("\n--- Selecting Idea ---")

    # User selects idea 0
    selected_idea = ideas[0]

    # Update state and Resume
    workflow.update_state(config, {"selected_idea": selected_idea})
    result_2 = workflow.invoke(None, config=config)

    # Verify Phase Transition to VERIFICATION
    current_state_2 = workflow.get_state(config).values
    phase = current_state_2.get("phase")
    print(f"Current Phase: {phase}")

    if phase != Phase.VERIFICATION:
        raise AssertionError(f"Expected Phase.VERIFICATION, got {phase}")

    print("Selection Passed: State updated, Phase is VERIFICATION.")
    return current_state_2, phase, result_2, selected_idea


@app.cell
def __(Phase, Transcript, config, workflow):
    # 8. Scenario 2: Simulation (The Grill)
    print("\n--- Scenario 2: Simulation ---")

    # Inject transcript
    transcript = Transcript(source="interview_1.txt", content="Customer says: I love cats but hate the smell.")
    workflow.update_state(config, {"transcripts": [transcript]})

    # Resume (runs ingestion, simulation, nemawashi, cpo, solution proposal)
    result_3 = workflow.invoke(None, config=config)

    # Verify Output
    current_state_3 = workflow.get_state(config).values

    # Check Debate History
    history = current_state_3.get("debate_history", [])
    print(f"Debate History Length: {len(history)}")
    # Note: Mocked LLM always says "I have concerns", so agents might loop or finish.
    # We just ensure it ran.

    # Check Phase (Should be SOLUTION after proposal)
    phase_3 = current_state_3.get("phase")
    print(f"Current Phase: {phase_3}")

    if phase_3 != Phase.SOLUTION:
         raise AssertionError(f"Expected Phase.SOLUTION, got {phase_3}")

    # Check Candidate Features (from Builder)
    features = current_state_3.get("candidate_features")
    print(f"Candidate Features: {features}")

    if not features:
        raise AssertionError("No candidate features extracted.")

    print("Scenario 2 Passed: Simulation ran, Features proposed.")
    return current_state_3, features, history, phase_3, result_3, transcript


@app.cell
def __(config, workflow):
    # 9. Scenario 4: MVP (Cycle 5)
    print("\n--- Scenario 4: MVP ---")

    # User selects a feature
    # We need to simulate the selection by updating state
    # We update 'selected_feature'
    workflow.update_state(config, {"selected_feature": "Cat Translation"})

    # Resume
    result_4 = workflow.invoke(None, config=config)

    # Verify MVP URL
    current_state_4 = workflow.get_state(config).values
    mvp_url = current_state_4.get("mvp_url")
    print(f"MVP URL: {mvp_url}")

    if mvp_url != "https://v0.dev/mock-result":
        raise AssertionError(f"Unexpected MVP URL: {mvp_url}")

    print("Scenario 4 Passed: MVP Generated.")
    return current_state_4, mvp_url, result_4


@app.cell
def __(Phase, config, workflow):
    # 10. Completion
    print("\n--- Completing Workflow ---")

    # Resume from PMF (mocked interrupt) to Governance
    result_5 = workflow.invoke(None, config=config)

    final_state = workflow.get_state(config).values
    final_phase = final_state.get("phase")
    print(f"Final Phase: {final_phase}")

    if final_phase != Phase.GOVERNANCE:
         # Note: Governance node sets phase to GOVERNANCE, then workflow ends.
         # So final state phase should be GOVERNANCE.
         raise AssertionError(f"Expected Phase.GOVERNANCE, got {final_phase}")

    print("Tutorial Completed Successfully.")
    return final_phase, final_state, result_5


if __name__ == "__main__":
    app.run()
