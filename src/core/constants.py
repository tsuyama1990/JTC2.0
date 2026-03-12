from typing import Final

# --- Global Defaults ---
DEFAULT_FPS: Final[int] = 30
DEFAULT_WIDTH: Final[int] = 800
DEFAULT_HEIGHT: Final[int] = 600
DEFAULT_LINE_HEIGHT: Final[int] = 20
DEFAULT_CHARS_PER_LINE: Final[int] = 50
DEFAULT_PAGE_SIZE: Final[int] = 5
DEFAULT_DIALOGUE_X: Final[int] = 10
DEFAULT_DIALOGUE_Y: Final[int] = 400
DEFAULT_MAX_Y: Final[int] = 1000
DEFAULT_CONSOLE_SLEEP: Final[float] = 0.05
DEFAULT_MAX_TURNS: Final[int] = 10

# --- Validation Defaults ---
DEFAULT_MIN_TITLE_LENGTH: Final[int] = 5
DEFAULT_MAX_TITLE_LENGTH: Final[int] = 100
DEFAULT_ITERATOR_SAFETY_LIMIT: Final[int] = 10000

# --- RAG Defaults ---
DEFAULT_RAG_CHUNK_SIZE: Final[int] = 1024
DEFAULT_RAG_MAX_DOC_LENGTH: Final[int] = 1_000_000  # 1MB text limit
DEFAULT_RAG_MAX_QUERY_LENGTH: Final[int] = 1000
DEFAULT_RAG_MAX_INDEX_SIZE_MB: Final[int] = 500  # 500MB index limit
DEFAULT_RAG_BATCH_SIZE: Final[int] = 100

# --- Feature Extraction Defaults ---
DEFAULT_FEATURE_CHUNK_SIZE: Final[int] = 2000

# --- Circuit Breaker Defaults ---
DEFAULT_CB_FAIL_MAX: Final[int] = 5
DEFAULT_CB_RESET_TIMEOUT: Final[int] = 60

# --- Nemawashi Defaults ---
DEFAULT_NEMAWASHI_MAX_STEPS: Final[int] = 100
DEFAULT_NEMAWASHI_TOLERANCE: Final[float] = 1e-6
DEFAULT_NEMAWASHI_BOOST: Final[float] = 0.2
DEFAULT_NEMAWASHI_REDUCTION: Final[float] = 0.1

# --- V0 Defaults ---
DEFAULT_V0_RETRY_MAX: Final[int] = 3
DEFAULT_V0_RETRY_BACKOFF: Final[float] = 2.0


# --- Governance Defaults ---
DEFAULT_MIN_ROI_THRESHOLD: Final[float] = 3.0
DEFAULT_CAC: Final[float] = 500.0
DEFAULT_ARPU: Final[float] = 50.0
DEFAULT_CHURN: Final[float] = 0.05
DEFAULT_MAX_LLM_RESPONSE_SIZE: Final[int] = 10_000  # Bytes
DEFAULT_MAX_SEARCH_RESULT_SIZE: Final[int] = 5000

# --- Error Messages ---
ERR_UNIQUE_ID_VIOLATION: Final[str] = "Duplicate ID detected."
ERR_CONFIG_MISSING_OPENAI_KEY: Final[str] = "OPENAI_API_KEY missing in environment."
ERR_CONFIG_MISSING_TAVILY_KEY: Final[str] = "TAVILY_API_KEY missing in environment."
ERR_SEARCH_CONFIG_MISSING: Final[str] = "Search configuration invalid."
ERR_LLM_CONFIG_MISSING: Final[str] = "LLM configuration invalid."
ERR_SEARCH_FAILED: Final[str] = "Search operation failed."
ERR_LLM_FAILURE: Final[str] = "LLM invocation failed."
ERR_TOO_MANY_METRICS: Final[str] = "Too many custom metrics defined (Limit: {limit})."
ERR_INVALID_METRIC_KEY: Final[str] = "Invalid metric key: {key}."
ERR_MISSING_PERSONA: Final[str] = "Persona configuration missing."
ERR_MISSING_MVP: Final[str] = "MVP definition missing."
ERR_MATRIX_VALUES: Final[str] = "Matrix values must be between 0.0 and 1.0."
ERR_STAKEHOLDER_MISMATCH: Final[str] = "Matrix dimensions do not match stakeholder count."
ERR_MATRIX_SHAPE: Final[str] = "Matrix shape is invalid."
ERR_MATRIX_STOCHASTICITY: Final[str] = "Influence matrix rows must sum to 1.0."
ERR_LLM_RESPONSE_TOO_LARGE: Final[str] = "LLM response exceeds maximum allowed size."
ERR_JSON_PARSE: Final[str] = "Failed to parse JSON response."
ERR_FILE_WRITE: Final[str] = "Failed to write output file."
ERR_INVALID_COLOR: Final[str] = "Invalid color value."
ERR_INVALID_DIMENSIONS: Final[str] = "Invalid dimensions."
ERR_INVALID_FPS: Final[str] = "Invalid FPS value."
ERR_INVALID_RESOLUTION: Final[str] = "Invalid resolution."

# --- V0 Error Messages ---
ERR_V0_API_KEY_MISSING: Final[str] = "V0 API Key missing."
ERR_V0_GENERATION_FAILED: Final[str] = "V0 generation failed."
ERR_V0_NETWORK_ERROR: Final[str] = "V0 network error."
ERR_V0_NO_URL: Final[str] = "No URL returned from V0."

# --- RAG Error Messages ---
ERR_CIRCUIT_OPEN: Final[str] = "Circuit breaker is open."
ERR_PATH_TRAVERSAL: Final[str] = "Path traversal detected."
ERR_RAG_INDEX_SIZE: Final[str] = "Index size limit exceeded."
ERR_RAG_QUERY_TOO_LARGE: Final[str] = "Query too large."
ERR_RAG_TEXT_TOO_LARGE: Final[str] = "Document text too large."

# --- UI Messages ---
MSG_NO_IDEAS: Final[str] = "No ideas generated yet."
MSG_GENERATED_HEADER: Final[str] = "=== Generated Lean Canvas Ideas ==="
MSG_PRESS_ENTER: Final[str] = "Press Enter to continue..."
MSG_SELECT_PROMPT: Final[str] = "Select an idea ID (q to quit): "
MSG_ID_NOT_FOUND: Final[str] = "ID not found. Try again."
MSG_INVALID_INPUT: Final[str] = "Invalid input."
MSG_SELECTED: Final[str] = "Selected: {title}"
MSG_CYCLE_COMPLETE: Final[str] = "Cycle complete."
MSG_TOPIC_EMPTY: Final[str] = "Topic cannot be empty."
MSG_PHASE_START: Final[str] = "Starting Phase: {phase}"
MSG_RESEARCHING: Final[str] = "Researching topic: {topic}..."
MSG_WAIT: Final[str] = "Please wait..."
MSG_EXECUTION_ERROR: Final[str] = "Execution error occurred."
MSG_SIM_TITLE: Final[str] = "JTC 2.0 Simulation"
MSG_WAITING_FOR_DEBATE: Final[str] = "Waiting for debate..."
MSG_NEMAWASHI_TITLE: Final[str] = "Nemawashi Influence Network"

# --- Metrics Descriptions ---
DESC_METRICS_CUSTOM: Final[str] = "Custom metrics defined by the simulation"

# --- Feature Descriptions ---
DESC_FEATURE_NAME: Final[str] = "Name of the feature"
DESC_FEATURE_DESC: Final[str] = "Description of the feature"
DESC_FEATURE_PRIORITY: Final[str] = "Implementation priority (MoSCoW)"

# --- MVP Descriptions ---
DESC_MVP_TYPE: Final[str] = "Type of MVP (e.g. Landing Page, Wizard of Oz)"
DESC_MVP_CORE_FEATURES: Final[str] = "List of core features included in the MVP"
DESC_MVP_SUCCESS_CRITERIA: Final[str] = "Criteria to measure MVP success"

# --- Persona Descriptions ---
DESC_PERSONA_NAME: Final[str] = "Name of the persona"
DESC_PERSONA_OCCUPATION: Final[str] = "Job title or role"
DESC_PERSONA_DEMOGRAPHICS: Final[str] = "Age, gender, location, etc."
DESC_PERSONA_BIO: Final[str] = "Short biography"
DESC_PERSONA_GOALS: Final[str] = "Primary goals"
DESC_PERSONA_FRUSTRATIONS: Final[str] = "Key frustrations"
DESC_EMPATHY_SAYS: Final[str] = "What the persona says"
DESC_EMPATHY_THINKS: Final[str] = "What the persona thinks"
DESC_EMPATHY_DOES: Final[str] = "What the persona does"
DESC_EMPATHY_FEELS: Final[str] = "What the persona feels"

# --- Prompts ---
PROMPT_PERSONA_GENERATOR: Final[str] = (
    "You are an expert UX Researcher and Product Strategist. "
    "Your task is to generate a highly detailed, realistic Customer Persona and an Empathy Map "
    "(Says, Thinks, Does, Feels) based on the provided business idea. "
    "Ensure the output strictly adheres to the requested JSON schema and avoid hallucinations."
)

PROMPT_ALTERNATIVE_ANALYSIS: Final[str] = (
    "You are a sharp Business Analyst. Your task is to perform an Alternative Analysis. "
    "Identify the current alternative tools (e.g., Excel, manual work, existing SaaS) "
    "the persona uses, determine the switching costs, and articulate the 10x value proposition "
    "that would compel them to switch to our new solution. "
    "Output must strictly match the required JSON schema."
)

PROMPT_VALUE_PROPOSITION: Final[str] = (
    "You are an expert Product Manager. Your task is to generate a Value Proposition Canvas. "
    "Based on the provided persona and alternative analysis, map the Customer Profile (Jobs, Pains, Gains) "
    "to the Value Map (Products & Services, Pain Relievers, Gain Creators). "
    "Finally, evaluate how well they fit. "
    "Output must strictly match the required JSON schema."
)

PROMPT_FINANCE_AGENT: Final[str] = (
    "You are a conservative Finance Manager at a large Japanese traditional company. "
    "You always ask about cost, risk, and timeline. "
    "You use market data to find reasons why new ideas will fail. "
    "Be critical but professional."
)

PROMPT_SALES_AGENT: Final[str] = (
    "You are an aggressive Sales Manager. "
    "You worry about cannibalizing existing products and whether the sales force can actually sell this. "
    "You care about immediate revenue and customer trust."
)

PROMPT_NEW_EMPLOYEE_AGENT: Final[str] = (
    "You are a new employee presenting a startup idea. "
    "You are nervous. You try to answer questions but often falter. "
    "You defend the idea passionately but acknowledge weaknesses."
)

# --- Default Paths & Files ---
DEFAULT_RINGI_SHO_PATH: Final[str] = "RINGI_SHO.md"
DEFAULT_CANVAS_OUTPUT_DIR: Final[str] = "./outputs/canvas"

# --- Default JSON configurations ---
DEFAULT_SIMULATION_TURN_SEQUENCE: Final[str] = (
    '[{"node_name": "pitch", "role": "New Employee", "description": "New Employee Pitch"}, {"node_name": "finance_critique", "role": "Finance Manager", "description": "Finance Critique"}, {"node_name": "defense_1", "role": "New Employee", "description": "New Employee Defense"}, {"node_name": "sales_critique", "role": "Sales Manager", "description": "Sales Critique"}, {"node_name": "defense_2", "role": "New Employee", "description": "New Employee Defense"}]'
)
DEFAULT_HITL_INTERRUPT_NODES: Final[str] = (
    '["ideator", "vpc", "sitemap_wireframe", "virtual_customer", "experiment_planning"]'
)
DEFAULT_RAG_ALLOWED_PATHS: Final[str] = '["data", "vector_store", "tests"]'

# --- Templates and Queries ---
DEFAULT_GOV_SEARCH_QUERY_TEMPLATE: Final[str] = (
    "average CAC churn ARPU LTV for {industry} startups benchmarks"
)
DEFAULT_SEARCH_QUERY_TEMPLATE: Final[str] = (
    "emerging business trends and painful problems in {topic}"
)

# --- Default Lists ---
DEFAULT_CIRCUIT_BREAKERS: Final[list[str]] = ["平行線ですね", "同意します"]

# --- 3H Review Prompts ---
PROMPT_HACKER: Final[str] = (
    "【前提とするサイトマップと機能要件を遵守しつつ】技術的負債、スケーラビリティ、セキュリティの観点からワイヤーフレームをレビューせよ。不要に複雑なDB構造やリアルタイム通信を避け、スプレッドシートや既存APIのモックで代替できないか追求せよ。同意できる場合は「[APPROVED]」と出力せよ。"
)
PROMPT_HIPSTER: Final[str] = (
    "【前提とするメンタルモデルとペルソナを遵守しつつ】ユーザーの『Don't make me think（考えさせるな）』の原則に基づきUXをレビューせよ。メンタルモデルに反するオンボーディングの摩擦、タップ回数の多さ、エラー時の不親切さを指摘せよ。同意できる場合は「[APPROVED]」と出力せよ。"
)
PROMPT_HUSTLER: Final[str] = (
    "【前提とする代替品分析とVPCを遵守しつつ】ユニットエコノミクス（LTV > 3x CAC）の観点からビジネスモデルをレビューせよ。誰がどうやって見つけるのか、なぜ継続してお金を払うのかを厳しく問いただせ。同意できる場合は「[APPROVED]」と出力せよ。"
)
