from typing import Final

# Error Messages
ERR_CONFIG_MISSING_OPENAI_KEY: Final[str] = "OPENAI_API_KEY is missing"
ERR_CONFIG_MISSING_TAVILY_KEY: Final[str] = "TAVILY_API_KEY is missing"
ERR_SEARCH_CONFIG_MISSING: Final[str] = (
    "Search configuration error: API key is missing. Please check your .env file."
)
ERR_LLM_CONFIG_MISSING: Final[str] = (
    "LLM configuration error: API key is missing. Please check your .env file."
)
ERR_SEARCH_FAILED: Final[str] = "Search service unavailable."
ERR_LLM_FAILURE: Final[str] = "LLM generation failed."
ERR_UNIQUE_ID_VIOLATION: Final[str] = "Generated ideas must have unique IDs."

# UI Messages
MSG_NO_IDEAS: Final[str] = "\nNo ideas generated. Please try again or check logs."
MSG_GENERATED_HEADER: Final[str] = "\n=== Generated {count} Ideas ==="
MSG_PRESS_ENTER: Final[str] = "\nPress Enter to see more..."
MSG_SELECT_PROMPT: Final[str] = "\n[GATE 1] Select an Idea ID (0-9) to proceed: "
MSG_ID_NOT_FOUND: Final[str] = "ID {idx} not found. Please try again."
MSG_INVALID_INPUT: Final[str] = "Please enter a valid number."
MSG_SELECTED: Final[str] = "\n✓ Selected Plan: {title}"
MSG_CYCLE_COMPLETE: Final[str] = "Cycle 1 Complete. State updated."
MSG_TOPIC_EMPTY: Final[str] = "Topic cannot be empty."
MSG_PHASE_START: Final[str] = "\nPhase: {phase}"
MSG_RESEARCHING: Final[str] = "Researching and Ideating for: '{topic}'..."
MSG_WAIT: Final[str] = "(This may take 30-60 seconds due to search and LLM generation)..."
MSG_EXECUTION_ERROR: Final[str] = "\nError during execution: {e}"
