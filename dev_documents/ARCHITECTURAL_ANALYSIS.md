I have compared the code with the spec and found that the codebase contains systemic hardcoding patterns that violate the `SYSTEM_ARCHITECTURE.md` specifications. Specifically:

- Direct imports of concrete implementations for LLM (`langchain_openai`, `langchain_core`) in `src/agents/*.py` and `src/core/llm.py` bypass the Dependency Inversion Principle.
- Direct imports of `llama_index` in `src/data/rag.py` create tight coupling.
- Direct imports of `tavily` in `src/tools/search.py` and `httpx` in `src/tools/v0_client.py` create tight coupling to vendor-specific libraries.

I will refactor the codebase to introduce abstract interfaces in `src/core/interfaces.py` and inject concrete implementations, completely removing vendor-specific imports from the business logic (Agents) and enforcing interfaces in Core components.
