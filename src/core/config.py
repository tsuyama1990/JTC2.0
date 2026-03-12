from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.theme import (
    AGENT_POS_CPO,
    AGENT_POS_FINANCE,
    AGENT_POS_NEW_EMP,
    AGENT_POS_SALES,
    COLOR_BG,
    COLOR_CPO,
    COLOR_FINANCE,
    COLOR_NEW_EMP,
    COLOR_SALES,
    COLOR_TEXT,
)
from src.core.validators import ConfigValidators


class ValidationConfig(BaseSettings):
    """Validation constraints for domain models."""

    min_title_length: int = Field(default=3, description="Minimum length for titles")
    max_title_length: int = Field(default=100, description="Maximum length for titles")
    min_content_length: int = Field(default=3, description="Minimum length for content blocks")
    max_content_length: int = Field(default=1000, description="Maximum length for content blocks")

    min_list_length: int = Field(default=1, description="Minimum items in lists")
    max_list_length: int = Field(default=20, description="Maximum items in lists")

    max_custom_metrics: int = Field(default=50, description="Maximum custom metrics allowed")
    min_metric_value: float = Field(default=0.0, description="Minimum value for metrics")
    max_percentage_value: float = Field(default=100.0, description="Maximum percentage value")


class ErrorMessages(BaseSettings):
    """Error messages for the application."""

    unique_id_violation: str = "Unique ID constraint violated."
    config_missing_openai: str = "OPENAI_API_KEY is not set."
    config_missing_tavily: str = "TAVILY_API_KEY is not set."
    search_config_missing: str = "Search configuration is incomplete."
    llm_config_missing: str = "LLM configuration is incomplete."
    search_failed: str = "Search operation failed."
    llm_failure: str = "LLM operation failed."
    too_many_metrics: str = "Too many custom metrics defined. Maximum is {limit}."
    invalid_metric_key: str = "Invalid custom metric key: {key}."
    missing_persona: str = "Target persona is required for this phase."
    missing_mvp: str = "MVP definition is required for this phase."


class UIConfig(BaseSettings):
    """UI Strings and Configuration."""

    page_size: int = Field(
        alias="UI_PAGE_SIZE",
        default=3,
        description="Number of items per page in UI",
    )

    no_ideas: str = "No ideas generated."
    generated_header: str = "\n--- Generated Ideas ---"
    press_enter: str = "Press Enter to continue..."
    select_prompt: str = "\nSelect an idea by ID, or 'q' to quit, 'n'/'p' for pages: "
    id_not_found: str = "Error: ID not found."
    invalid_input: str = "Invalid input."
    selected: str = "Selected Plan:"
    cycle_complete: str = "\n=== Cycle Complete ==="
    topic_empty: str = "Topic cannot be empty."
    phase_start: str = "Starting Phase: {phase}"
    researching: str = "Researching topic: {topic}..."
    wait: str = "Please wait..."
    execution_error: str = "Execution error occurred."


class AgentConfig(BaseModel):
    """Configuration for a single agent in the UI."""

    model_config = ConfigDict(frozen=True)

    role: str = Field(..., description="Role name of the agent")
    label: str = Field(..., description="Short label for UI")
    color: int = Field(..., description="Color code for the agent")
    x: int = Field(..., description="X position")
    y: int = Field(..., description="Y position")
    w: int = Field(..., description="Width")
    h: int = Field(..., description="Height")
    text_x: int = Field(..., description="Text X offset")
    text_y: int = Field(..., description="Text Y offset")

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: int) -> int:
        return ConfigValidators.validate_color(v)

    @field_validator("w", "h")
    @classmethod
    def validate_dimensions(cls, v: int) -> int:
        return ConfigValidators.validate_dimension(v)


class NemawashiConfig(BaseSettings):
    """Configuration for Nemawashi Consensus Building."""

    max_steps: int = Field(
        alias="NEMAWASHI_MAX_STEPS",
        default=50,
        description="Max iterations for consensus",
    )
    tolerance: float = Field(
        alias="NEMAWASHI_TOLERANCE",
        default=1e-4,
        description="Convergence tolerance",
    )
    nomikai_boost: float = Field(
        alias="NEMAWASHI_NOMIKAI_BOOST",
        default=0.2,
        description="Boost factor from Nomikai",
    )
    nomikai_reduction: float = Field(
        alias="NEMAWASHI_NOMIKAI_REDUCTION",
        default=0.1,
        description="Stubbornness reduction from Nomikai",
    )


class V0Config(BaseSettings):
    """Configuration for v0.dev integration."""

    retry_max: int = Field(alias="V0_RETRY_MAX", default=3, description="Max retries for API calls")
    retry_backoff: float = Field(
        alias="V0_RETRY_BACKOFF",
        default=2.0,
        description="Exponential backoff factor",
    )


class SimulationConfig(BaseSettings):
    """Configuration for the Pyxel Simulation UI."""

    width: int = Field(default=256, description="Window width")
    height: int = Field(default=256, description="Window height")
    fps: int = Field(default=30, description="Frames per second")
    title: str = Field(default="JTC Simulation: The Meeting", description="Window title")
    bg_color: int = Field(default=COLOR_BG, description="Background color")
    text_color: int = Field(default=COLOR_TEXT, description="Text color")

    chars_per_line: int = Field(default=32, description="Characters per line in dialogue")
    line_height: int = Field(default=10, description="Line height in pixels")
    dialogue_x: int = Field(default=10, description="Dialogue box X position")
    dialogue_y: int = Field(default=150, description="Dialogue box Y position")
    max_y: int = Field(default=500, description="Max Y for scrolling")
    waiting_msg: str = Field(default="Waiting for debate...", description="Message when waiting")

    turn_sequence: list[dict[str, str]] = Field(
        default_factory=lambda: [
            {"node_name": "pitch", "role": "New Employee", "description": "New Employee Pitch"},
            {
                "node_name": "finance_critique",
                "role": "Finance Manager",
                "description": "Finance Critique",
            },
            {
                "node_name": "defense_1",
                "role": "New Employee",
                "description": "New Employee Defense",
            },
            {
                "node_name": "sales_critique",
                "role": "Sales Manager",
                "description": "Sales Critique",
            },
            {
                "node_name": "defense_2",
                "role": "New Employee",
                "description": "New Employee Final Defense",
            },
        ],
        description="List of simulation steps defining the turn sequence.",
    )

    console_sleep: float = Field(default=1.5, description="Sleep time for console fallback")
    max_turns: int = Field(default=10, description="Max turns in simulation")

    # Explicit fields for individual agents to allow env var overrides
    agent_new_emp: AgentConfig = Field(
        default_factory=lambda: AgentConfig(
            role="New Employee", label="NewEmp", color=COLOR_NEW_EMP, **AGENT_POS_NEW_EMP
        ),
        description="Configuration for New Employee Agent",
    )
    agent_finance: AgentConfig = Field(
        default_factory=lambda: AgentConfig(
            role="Finance Manager", label="Finance", color=COLOR_FINANCE, **AGENT_POS_FINANCE
        ),
        description="Configuration for Finance Agent",
    )
    agent_sales: AgentConfig = Field(
        default_factory=lambda: AgentConfig(
            role="Sales Manager", label="Sales", color=COLOR_SALES, **AGENT_POS_SALES
        ),
        description="Configuration for Sales Agent",
    )
    agent_cpo: AgentConfig = Field(
        default_factory=lambda: AgentConfig(
            role="CPO", label="CPO", color=COLOR_CPO, **AGENT_POS_CPO
        ),
        description="Configuration for CPO Agent",
    )

    @property
    def agents(self) -> dict[str, AgentConfig]:
        """Backwards compatibility accessor for agents dict."""
        return {
            "New Employee": self.agent_new_emp,
            "Finance Manager": self.agent_finance,
            "Sales Manager": self.agent_sales,
            "CPO": self.agent_cpo,
        }

    @field_validator("width", "height")
    @classmethod
    def validate_resolution(cls, v: int) -> int:
        return ConfigValidators.validate_resolution(v)

    @field_validator("fps")
    @classmethod
    def validate_fps(cls, v: int) -> int:
        return ConfigValidators.validate_fps(v)

    @field_validator("bg_color", "text_color")
    @classmethod
    def validate_color(cls, v: int) -> int:
        return ConfigValidators.validate_color(v)


class GovernanceConfig(BaseSettings):
    """Configuration for Governance and Financials."""

    min_roi_threshold: float = Field(
        alias="MIN_ROI_THRESHOLD",
        default=3.0,
        description="Minimum ROI for approval",
    )
    default_cac: float = Field(alias="DEFAULT_CAC", default=500.0, description="Fallback CAC")
    default_arpu: float = Field(alias="DEFAULT_ARPU", default=50.0, description="Fallback ARPU")
    default_churn: float = Field(
        alias="DEFAULT_CHURN", default=0.05, description="Fallback Churn Rate"
    )
    max_llm_response_size: int = Field(
        alias="MAX_LLM_RESPONSE_SIZE",
        default=10_000,
        description="Max bytes for LLM JSON response",
    )
    output_path: str = Field(
        alias="RINGI_SHO_PATH", default="RINGI_SHO.md", description="Path for Ringi-sho output"
    )
    search_query_template: str = Field(
        alias="GOV_SEARCH_QUERY_TEMPLATE",
        default="average CAC churn ARPU LTV for {industry} startups benchmarks",
        description="Template for financial search",
    )
    max_search_result_size: int = Field(
        alias="MAX_SEARCH_RESULT_SIZE",
        default=5000,
        description="Max chars for search result context",
    )

    @field_validator("search_query_template")
    @classmethod
    def validate_template(cls, v: str) -> str:
        if "{industry}" not in v:
            msg = "search_query_template must contain {industry} placeholder."
            raise ValueError(msg)
        return v


class Settings(BaseSettings):
    """Configuration settings for the application."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="forbid")

    # Explicitly enforce required keys without defaults
    openai_api_key: SecretStr = Field(alias="OPENAI_API_KEY", description="OpenAI API Key")
    tavily_api_key: SecretStr = Field(alias="TAVILY_API_KEY", description="Tavily Search API Key")
    v0_api_key: SecretStr = Field(alias="V0_API_KEY", description="V0.dev API Key")

    @field_validator("openai_api_key", "tavily_api_key", "v0_api_key", mode="before")
    @classmethod
    def validate_non_empty_key(cls, v: str | SecretStr) -> str | SecretStr:
        secret = v.get_secret_value() if isinstance(v, SecretStr) else str(v)
        if not secret or not secret.strip():
            msg = "API key cannot be empty or whitespace-only."
            raise ValueError(msg)
        return v

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v: SecretStr) -> SecretStr:
        ConfigValidators.validate_openai_key(v)
        return v

    @field_validator("tavily_api_key")
    @classmethod
    def validate_tavily_key(cls, v: SecretStr) -> SecretStr:
        ConfigValidators.validate_tavily_key(v)
        return v

    @field_validator("v0_api_key")
    @classmethod
    def validate_v0_api_key(cls, v: SecretStr) -> SecretStr:
        """Validate the format of the V0 API Key."""
        import re

        secret = v.get_secret_value()
        if len(secret) < 10:
            msg = "v0_api_key must be at least 10 characters long."
            raise ValueError(msg)
        if not re.match(r"^[\w\-]+$", secret):
            msg = "v0_api_key contains invalid characters."
            raise ValueError(msg)
        return v

    v0_api_url: str = Field(
        alias="V0_API_URL",
        description="V0.dev API URL",
        pattern=r"^https://api\.v0\.dev/.*$",
    )

    llm_model: str = Field(alias="LLM_MODEL", default="gpt-4o", description="LLM Model name")

    rag_persist_dir: str = Field(alias="RAG_PERSIST_DIR", description="Directory for RAG index")
    rag_chunk_size: int = Field(
        alias="RAG_CHUNK_SIZE", default=1024, description="Chunk size for RAG"
    )
    rag_max_document_length: int = Field(
        alias="RAG_MAX_DOC_LENGTH",
        default=1_000_000,
        description="Max document length",
    )
    rag_max_query_length: int = Field(
        alias="RAG_MAX_QUERY_LENGTH",
        default=1000,
        description="Max query length",
    )
    rag_max_index_size_mb: int = Field(
        alias="RAG_MAX_INDEX_SIZE_MB",
        default=500,
        description="Max index size in MB",
    )
    rag_allowed_paths: str | list[str] = Field(
        alias="RAG_ALLOWED_PATHS",
        description="Allowed directories for RAG",
    )
    rag_rate_limit_interval: float = Field(
        alias="RAG_RATE_LIMIT_INTERVAL",
        default=0.1,
        description="Min interval between RAG calls in seconds",
    )
    rag_scan_depth_limit: int = Field(
        alias="RAG_SCAN_DEPTH_LIMIT",
        default=10,
        description="Max recursion depth for directory scanning",
    )

    @field_validator("rag_allowed_paths", mode="before")
    @classmethod
    def parse_allowed_paths(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [p.strip() for p in v.split(",") if p.strip()]
        return v

    @field_validator("rag_max_index_size_mb")
    @classmethod
    def validate_rag_index_size(cls, v: int) -> int:
        if v <= 0:
            msg = "rag_max_index_size_mb must be positive."
            raise ValueError(msg)
        return v

    @field_validator("rag_scan_depth_limit")
    @classmethod
    def validate_scan_depth(cls, v: int) -> int:
        if v <= 0:
            msg = "rag_scan_depth_limit must be positive."
            raise ValueError(msg)
        return v

    rag_batch_size: int = Field(
        alias="RAG_BATCH_SIZE",
        default=100,
        description="Batch size for RAG ingestion",
    )
    rag_query_timeout: float = Field(
        alias="RAG_QUERY_TIMEOUT", default=30.0, description="Timeout for RAG queries in seconds"
    )

    feature_chunk_size: int = Field(
        alias="FEATURE_CHUNK_SIZE",
        default=5,
        description="Chunk size for feature extraction",
    )

    circuit_breaker_fail_max: int = Field(
        alias="CB_FAIL_MAX",
        default=3,
        description="Circuit breaker fail threshold",
    )
    circuit_breaker_reset_timeout: int = Field(
        alias="CB_RESET_TIMEOUT",
        default=300,
        description="Circuit breaker reset timeout",
    )

    iterator_safety_limit: int = Field(
        alias="ITERATOR_SAFETY_LIMIT",
        default=1000,
        description="Max items for iterators",
    )

    search_max_results: int = Field(
        alias="SEARCH_MAX_RESULTS", default=5, description="Max search results"
    )
    search_depth: str = Field(
        alias="SEARCH_DEPTH", default="advanced", description="Search depth (basic/advanced)"
    )
    search_query_template: str = Field(
        alias="SEARCH_QUERY_TEMPLATE",
        default="emerging business trends and painful problems in {topic}",
        description="Template for search queries",
    )

    log_level: str = Field(alias="LOG_LEVEL", default="INFO", description="Logging level")
    ui_page_size: int = Field(alias="UI_PAGE_SIZE", default=3, description="Page size for UI")

    # Nested configurations - Use Field to allow Pydantic to manage them
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    errors: ErrorMessages = Field(default_factory=ErrorMessages)
    ui: UIConfig = Field(default_factory=UIConfig)
    simulation: SimulationConfig = Field(default_factory=SimulationConfig)
    nemawashi: NemawashiConfig = Field(default_factory=NemawashiConfig)
    v0: V0Config = Field(default_factory=V0Config)
    governance: GovernanceConfig = Field(default_factory=GovernanceConfig)


@lru_cache
def get_settings() -> Settings:
    """Load and cache settings."""
    return Settings()
