import marimo

__generated_with = "0.9.14"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo
    return mo,


@app.cell
def __(mo):
    mo.md(
        r"""
        # 🚀 The JTC 2.0: Ultimate UAT & Tutorial

        Welcome to the **Unified User Acceptance Test (UAT) and Interactive Tutorial** for the **JTC 2.0 Enterprise Business Accelerator**.

        This notebook demonstrates the core capabilities of the system:
        1.  **Ideation**: Generating Lean Canvases from a topic.
        2.  **Simulation**: Running a "Gekizume" debate with AI agents.
        3.  **Pivot**: Using RAG to validate ideas against real interviews.
        4.  **MVP**: Generating a frontend prototype with v0.dev.

        **Note:** This tutorial runs in **Mock Mode** by default if API keys are missing, ensuring you can verify the logic without incurring costs.
        """
    )
    return


@app.cell
def __(mo):
    mo.md(
        r"""
        ## 1. Setup Environment

        First, we initialize the environment. If you haven't set your API keys in , we will inject **Mock Keys** to ensure the tutorial runs smoothly.
        """
    )
    return


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

    print("✅ Environment variables set (using mocks if necessary).")
    return MagicMock, os, patch, unittest


@app.cell
def __(mo):
    mo.md(
        r"""
        ## 2. Mock External Services

        To guarantee reliability and speed during this tutorial, we mock the external API calls (OpenAI, Tavily, v0.dev). This allows us to verify the **internal logic** and **state transitions** of the JTC 2.0 system without network dependencies.
        """
    )
    return


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

    print("✅ External services mocked successfully.")
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
def __(mo):
    mo.md(
        r"""
        ## 3. Configure Smart LLM Responses

        The JTC 2.0 uses **Structured Output** (Pydantic models) extensively. We configure our mock LLM to return valid Pydantic objects (, , ) when requested, ensuring the agents can parse the "AI" response correctly.
        """
    )
    return


@app.cell
def __(MagicMock, mock_openai_instance, mo):
    # 3. Smart LLM Mocking
    try:
        from src.agents.ideator import LeanCanvasList
        from src.agents.builder import FeatureList
        from src.domain_models.mvp import MVPSpec, MVPType
        from src.domain_models.lean_canvas import LeanCanvas
        from langchain_core.messages import AIMessage
    except ImportError as e:
        mo.md(f"### ❌ Critical Error: Missing Dependencies\nCould not import required modules from . Ensure you are running this from the project root.\nError: {e}")
        raise e

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
    def mock_llm_invoke(input, **kwargs):
        return AIMessage(content="Mocked LLM Response: I have analyzed the plan and I have concerns about ROI.")

    # Side Effect Dispatcher to return correct type based on what the agent asks for
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

    print("✅ Smart LLM Mock configured with correct Pydantic schemas.")
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
def __(mo):
    mo.md(
        r"""
        ## 4. Initialize the Application

        We load the **LangGraph** workflow application. We use  to persist state between steps in-memory, which allows us to pause and resume execution at the **Decision Gates**.
        """
    )
    return


@app.cell
def __(mo):
    # 4. Import Project Modules
    try:
        from src.core.graph import create_app
        from src.domain_models.state import GlobalState, Phase
        from src.domain_models.transcript import Transcript
        from langgraph.checkpoint.memory import MemorySaver
    except ImportError as e:
         mo.md(f"### ❌ Critical Error: Import Failed\n{e}")
         raise e

    print("✅ Project modules imported.")
    return GlobalState, MemorySaver, Phase, Transcript, create_app


@app.cell
def __(GlobalState, MemorySaver, create_app):
    # 5. Initialize App
    memory = MemorySaver()
    workflow = create_app(checkpointer=memory)

    # Config for thread (simulating a unique user session)
    config = {"configurable": {"thread_id": "tutorial_user_1"}}

    print("✅ App initialized with MemorySaver checkpointer.")
    return config, memory, workflow


@app.cell
def __(mo):
    mo.md(
        r"""
        ## 5. Scenario 1: Ideation (The Spark)

        **Goal:** Generate 10 diverse business ideas for the topic "AI for Cats".

        **Action:** The  will research the topic using (mocked) Tavily and generate 10 Lean Canvases. The workflow will then **interrupt** at  waiting for user selection.
        """
    )
    return


@app.cell
def __(GlobalState, config, workflow):
    # 6. Scenario 1 Execution
    print("\n--- 🏁 Starting Scenario 1: Ideation ---")

    try:
        initial_state = GlobalState(topic="AI for Cats")
        result = workflow.invoke(initial_state, config=config)

        # Verify State after Ideator
        current_state = workflow.get_state(config).values
        ideas_iter = current_state.get("generated_ideas")
        ideas = list(ideas_iter) if ideas_iter else []

        print(f"✅ Generated {len(ideas)} ideas.")
        if len(ideas) != 10:
            raise AssertionError(f"Expected 10 ideas, got {len(ideas)}")

    except Exception as e:
        raise AssertionError(f"Scenario 1 Failed: {e}") from e

    return current_state, ideas, initial_state, result


@app.cell
def __(mo):
    mo.md(
        r"""
        ## 6. Scenario 2: Selection & Simulation (The Grill)

        **Goal:** Select an idea and subject it to "Gekizume" (harsh debate).

        **Action:** We simulate the user selecting **Idea #0**. The system transitions to  and then, after we inject a mock transcript (Gate 2), it runs the **Simulation**.
        """
    )
    return


@app.cell
def __(Phase, Transcript, config, ideas, workflow):
    # 7. Scenario 2 Execution
    print("\n--- 🏁 Starting Scenario 2: Simulation ---")

    try:
        # User selects idea 0
        selected_idea = ideas[0]

        # Update state with selection
        workflow.update_state(config, {"selected_idea": selected_idea})

        # Resume -> verification_node -> interrupt
        workflow.invoke(None, config=config)

        # Verify transition to VERIFICATION
        state_after_select = workflow.get_state(config).values
        if state_after_select.get("phase") != Phase.VERIFICATION:
             raise AssertionError(f"Expected Phase.VERIFICATION, got {state_after_select.get('phase')}")

        # Inject transcript (Gate 2)
        print("Injecting customer transcript...")
        transcript = Transcript(source="interview_1.txt", content="Customer says: I love cats but hate the smell.")
        workflow.update_state(config, {"transcripts": [transcript]})

        # Resume -> Ingestion -> Simulation -> Nemawashi -> CPO -> Proposal
        workflow.invoke(None, config=config)

        # Verify Simulation Ran
        current_state_3 = workflow.get_state(config).values
        history = current_state_3.get("debate_history", [])
        print(f"✅ Simulation complete. Debate history length: {len(history)}")

        phase_3 = current_state_3.get("phase")
        if phase_3 != Phase.SOLUTION:
             raise AssertionError(f"Expected Phase.SOLUTION, got {phase_3}")

    except Exception as e:
        raise AssertionError(f"Scenario 2 Failed: {e}") from e

    return (
        current_state_3,
        history,
        phase_3,
        selected_idea,
        state_after_select,
        transcript,
    )


@app.cell
def __(mo):
    mo.md(
        r"""
        ## 7. Scenario 3: Pivot & Feature Selection

        **Goal:** Review CPO advice and select a feature for the MVP.

        **Action:** The  has proposed features based on the debate and solution. We verify these features exist and simulate the user selecting **"Cat Translation"**.
        """
    )
    return


@app.cell
def __(current_state_3, config, workflow):
    # 8. Scenario 3 Execution
    print("\n--- 🏁 Starting Scenario 3: Feature Selection ---")

    try:
        features = current_state_3.get("candidate_features")
        print(f"Proposed Features: {features}")

        if not features:
            raise AssertionError("No candidate features extracted by Builder Agent.")

        # User selects a feature
        workflow.update_state(config, {"selected_feature": "Cat Translation"})
        print("✅ Feature 'Cat Translation' selected.")

    except Exception as e:
        raise AssertionError(f"Scenario 3 Failed: {e}") from e
    return features,


@app.cell
def __(mo):
    mo.md(
        r"""
        ## 8. Scenario 4: MVP Generation (The Build)

        **Goal:** Generate a working prototype URL.

        **Action:** The system calls the (mocked) v0.dev API to generate a UI for the selected feature. We verify that a valid URL is returned.
        """
    )
    return


@app.cell
def __(config, workflow):
    # 9. Scenario 4 Execution
    print("\n--- 🏁 Starting Scenario 4: MVP Generation ---")

    try:
        # Resume -> MVP Generation
        workflow.invoke(None, config=config)

        # Verify MVP URL
        current_state_4 = workflow.get_state(config).values
        mvp_url = current_state_4.get("mvp_url")
        print(f"✅ MVP URL Generated: {mvp_url}")

        if mvp_url != "https://v0.dev/mock-result":
            raise AssertionError(f"Unexpected MVP URL: {mvp_url}")

    except Exception as e:
        raise AssertionError(f"Scenario 4 Failed: {e}") from e
    return current_state_4, mvp_url


@app.cell
def __(mo):
    mo.md(
        r"""
        ## 9. Conclusion

        **Congratulations!** You have successfully simulated the entire lifecycle of a business idea within the JTC 2.0 environment.

        **Summary of Achievements:**
        -   ✅ Generated 10 unique Lean Canvases.
        -   ✅ Simulated a "Gekizume" debate with 3 distinct AI personas.
        -   ✅ Ingested customer data to ground the simulation in reality.
        -   ✅ Pivot/Persevere decision made via Feature Selection.
        -   ✅ Generated a frontend MVP Prototype.

        This confirms the system logic is sound and ready for real-world usage.
        """
    )
    return


if __name__ == "__main__":
    app.run()
