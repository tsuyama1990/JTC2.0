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
ERR_TOO_MANY_METRICS: Final[str] = "Too many custom metrics. Limit is {limit}"
ERR_INVALID_METRIC_KEY: Final[str] = "Metric key '{key}' contains invalid characters."
ERR_MISSING_PERSONA: Final[str] = "Target persona is required for VERIFICATION phase."
ERR_MISSING_MVP: Final[str] = "MVP definition is required for SOLUTION phase."

# Validation Errors (Config)
ERR_INVALID_COLOR: Final[str] = "Color must be between 0 and 15"
ERR_INVALID_DIMENSIONS: Final[str] = "Dimensions must be positive"
ERR_INVALID_RESOLUTION: Final[str] = "Resolution must be positive"
ERR_INVALID_FPS: Final[str] = "FPS must be between 1 and 60"

# Nemawashi Errors
ERR_MATRIX_SHAPE: Final[str] = "Influence matrix must be square (NxN)."
ERR_MATRIX_VALUES: Final[str] = "Matrix values must be between 0.0 and 1.0."
ERR_MATRIX_STOCHASTICITY: Final[str] = "Influence matrix rows must sum to 1.0."
ERR_STAKEHOLDER_MISMATCH: Final[str] = "Number of stakeholders must match matrix dimensions."
ERR_DISCONNECTED_GRAPH: Final[str] = "Influence network contains disconnected components."
ERR_PATH_TRAVERSAL: Final[str] = "Path traversal detected in persist_dir. Must be within project root."
ERR_RAG_INDEX_SIZE: Final[str] = "Vector store size exceeds limit ({limit} MB). Loading blocked."
ERR_RAG_TEXT_TOO_LARGE: Final[str] = "Text too large ({size} chars) for ingestion."
ERR_RAG_QUERY_TOO_LARGE: Final[str] = "Query too large ({size} chars)."
ERR_CIRCUIT_OPEN: Final[str] = "Circuit breaker is open. External service unavailable."
ERR_RATE_LIMIT: Final[str] = "Rate limit exceeded for external API."

# UI Messages
MSG_NO_IDEAS: Final[str] = "\nNo ideas generated. Please try again or check logs."
MSG_GENERATED_HEADER: Final[str] = "\n=== Generated Ideas ==="
MSG_PRESS_ENTER: Final[str] = "\nPress Enter to see more..."
MSG_SELECT_PROMPT: Final[str] = (
    "\n[GATE 1] Select an Idea ID (0-9) to proceed (or 'n' for next page): "
)
MSG_ID_NOT_FOUND: Final[str] = "ID {idx} not found in this batch. Please try again."
MSG_INVALID_INPUT: Final[str] = "Please enter a valid number or 'n'."
MSG_SELECTED: Final[str] = "\n✓ Selected Plan: {title}"
MSG_CYCLE_COMPLETE: Final[str] = "Cycle 1 Complete. State updated."
MSG_TOPIC_EMPTY: Final[str] = "Topic cannot be empty."
MSG_PHASE_START: Final[str] = "\nPhase: {phase}"
MSG_RESEARCHING: Final[str] = "Researching and Ideating for: '{topic}'..."
MSG_WAIT: Final[str] = "(This may take 30-60 seconds due to search and LLM generation)..."
MSG_EXECUTION_ERROR: Final[str] = "\nError during execution: {e}"

# Simulation Messages
MSG_SIM_TITLE: Final[str] = "JTC Simulation"
MSG_WAITING_FOR_DEBATE: Final[str] = "Waiting for debate start..."

# Nemawashi UI
MSG_NEMAWASHI_TITLE: Final[str] = "Nemawashi Consensus Map"
MSG_CONSENSUS_REACHED: Final[str] = "Consensus Reached!"
MSG_CONSENSUS_FAILED: Final[str] = "Consensus Failed."
MSG_INFLUENCER_IDENTIFIED: Final[str] = "Key Influencer Identified: {name}"
MSG_NOMIKAI_SUCCESS: Final[str] = "Nomikai successful. {target} is now more open."

# Domain Model Descriptions
DESC_MVP_TYPE: Final[str] = "Type of MVP (e.g., Landing Page, Wizard of Oz)"
DESC_FEATURE_NAME: Final[str] = "Short name of the feature"
DESC_FEATURE_DESC: Final[str] = "Detailed description of what the feature does"
DESC_FEATURE_PRIORITY: Final[str] = "Priority level (Must-have, Should-have, etc.)"
DESC_MVP_CORE_FEATURES: Final[str] = "List of core features included in the MVP"
DESC_MVP_SUCCESS_CRITERIA: Final[str] = "Quantifiable criteria for MVP success"

DESC_PERSONA_NAME: Final[str] = "Name of the target persona"
DESC_PERSONA_OCCUPATION: Final[str] = "Job title or role"
DESC_PERSONA_DEMOGRAPHICS: Final[str] = "Age, gender, location, and other demographic details"
DESC_PERSONA_GOALS: Final[str] = "What the persona wants to achieve"
DESC_PERSONA_FRUSTRATIONS: Final[str] = "Pain points and obstacles preventing success"
DESC_PERSONA_BIO: Final[str] = "Short biography describing the persona's background"
DESC_EMPATHY_SAYS: Final[str] = "Quotes or statements from the customer"
DESC_EMPATHY_THINKS: Final[str] = "Internal thoughts and beliefs"
DESC_EMPATHY_DOES: Final[str] = "Actions and behaviors"
DESC_EMPATHY_FEELS: Final[str] = "Emotional state and feelings"

DESC_METRICS_AARRR: Final[str] = (
    "Standard AARRR metrics (Acquisition, Activation, Retention, Revenue, Referral)"
)
DESC_METRICS_CUSTOM: Final[str] = "Additional custom metrics specific to the business model"

# Configuration Defaults (Nemawashi)
DEFAULT_NEMAWASHI_MAX_STEPS: Final[int] = 10
DEFAULT_NEMAWASHI_TOLERANCE: Final[float] = 1e-6
DEFAULT_NEMAWASHI_BOOST: Final[float] = 0.3
DEFAULT_NEMAWASHI_REDUCTION: Final[float] = 0.1

# Configuration Defaults (RAG)
DEFAULT_RAG_CHUNK_SIZE: Final[int] = 4000
DEFAULT_RAG_MAX_DOC_LENGTH: Final[int] = 10000
DEFAULT_RAG_MAX_QUERY_LENGTH: Final[int] = 500
DEFAULT_RAG_MAX_INDEX_SIZE_MB: Final[int] = 500
DEFAULT_CB_FAIL_MAX: Final[int] = 5
DEFAULT_CB_RESET_TIMEOUT: Final[int] = 60

# Configuration Defaults (Validation)
DEFAULT_MIN_TITLE_LENGTH: Final[int] = 3
DEFAULT_MAX_TITLE_LENGTH: Final[int] = 100
DEFAULT_ITERATOR_SAFETY_LIMIT: Final[int] = 10000

# UI Defaults
DEFAULT_PAGE_SIZE: Final[int] = 5
DEFAULT_FPS: Final[int] = 30
DEFAULT_WIDTH: Final[int] = 160
DEFAULT_HEIGHT: Final[int] = 120

# UI Layout Defaults
DEFAULT_CHARS_PER_LINE: Final[int] = 38
DEFAULT_LINE_HEIGHT: Final[int] = 8
DEFAULT_DIALOGUE_X: Final[int] = 5
DEFAULT_DIALOGUE_Y: Final[int] = 15
DEFAULT_MAX_Y: Final[int] = 75
DEFAULT_CONSOLE_SLEEP: Final[float] = 0.5
DEFAULT_MAX_TURNS: Final[int] = 5
