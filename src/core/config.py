from functools import lru_cache
from typing import Self

from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.constants import (
    DEFAULT_CB_FAIL_MAX,
    DEFAULT_CB_RESET_TIMEOUT,
    DEFAULT_CHARS_PER_LINE,
    DEFAULT_CONSOLE_SLEEP,
    DEFAULT_DIALOGUE_X,
    DEFAULT_DIALOGUE_Y,
    DEFAULT_FEATURE_CHUNK_SIZE,
    DEFAULT_FPS,
    DEFAULT_HEIGHT,
    DEFAULT_ITERATOR_SAFETY_LIMIT,
    DEFAULT_LINE_HEIGHT,
    DEFAULT_MAX_TITLE_LENGTH,
    DEFAULT_MAX_TURNS,
    DEFAULT_MAX_Y,
    DEFAULT_MIN_TITLE_LENGTH,
    DEFAULT_NEMAWASHI_BOOST,
    DEFAULT_NEMAWASHI_MAX_STEPS,
    DEFAULT_NEMAWASHI_REDUCTION,
    DEFAULT_NEMAWASHI_TOLERANCE,
    DEFAULT_PAGE_SIZE,
    DEFAULT_RAG_BATCH_SIZE,
    DEFAULT_RAG_CHUNK_SIZE,
    DEFAULT_RAG_MAX_DOC_LENGTH,
    DEFAULT_RAG_MAX_INDEX_SIZE_MB,
    DEFAULT_RAG_MAX_QUERY_LENGTH,
    DEFAULT_V0_API_URL,
    DEFAULT_V0_RETRY_BACKOFF,
    DEFAULT_V0_RETRY_MAX,
    DEFAULT_WIDTH,
    ERR_CONFIG_MISSING_OPENAI_KEY,
    ERR_CONFIG_MISSING_TAVILY_KEY,
    ERR_INVALID_METRIC_KEY,
    ERR_LLM_CONFIG_MISSING,
    ERR_LLM_FAILURE,
    ERR_MISSING_MVP,
    ERR_MISSING_PERSONA,
    ERR_SEARCH_CONFIG_MISSING,
    ERR_SEARCH_FAILED,
    ERR_TOO_MANY_METRICS,
    ERR_UNIQUE_ID_VIOLATION,
    MSG_CYCLE_COMPLETE,
    MSG_EXECUTION_ERROR,
    MSG_GENERATED_HEADER,
    MSG_ID_NOT_FOUND,
    MSG_INVALID_INPUT,
    MSG_NO_IDEAS,
    MSG_PHASE_START,
    MSG_PRESS_ENTER,
    MSG_RESEARCHING,
    MSG_SELECT_PROMPT,
    MSG_SELECTED,
    MSG_SIM_TITLE,
    MSG_TOPIC_EMPTY,
    MSG_WAIT,
    MSG_WAITING_FOR_DEBATE,
)
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

    min_title_length: int = Field(default=DEFAULT_MIN_TITLE_LENGTH, description="Minimum length for titles")
    max_title_length: int = Field(default=DEFAULT_MAX_TITLE_LENGTH, description="Maximum length for titles")
    min_content_length: int = Field(default=3, description="Minimum length for content blocks")
    max_content_length: int = Field(default=1000, description="Maximum length for content blocks")

    min_list_length: int = Field(default=1, description="Minimum items in lists")
    max_list_length: int = Field(default=20, description="Maximum items in lists")

    max_custom_metrics: int = Field(default=50, description="Maximum custom metrics allowed")
    min_metric_value: float = Field(default=0.0, description="Minimum value for metrics")
    max_percentage_value: float = Field(default=100.0, description="Maximum percentage value")


class ErrorMessages(BaseSettings):
    """Error messages for the application."""

    unique_id_violation: str = ERR_UNIQUE_ID_VIOLATION
    config_missing_openai: str = ERR_CONFIG_MISSING_OPENAI_KEY
    config_missing_tavily: str = ERR_CONFIG_MISSING_TAVILY_KEY
    search_config_missing: str = ERR_SEARCH_CONFIG_MISSING
    llm_config_missing: str = ERR_LLM_CONFIG_MISSING
    search_failed: str = ERR_SEARCH_FAILED
    llm_failure: str = ERR_LLM_FAILURE
    too_many_metrics: str = ERR_TOO_MANY_METRICS
    invalid_metric_key: str = ERR_INVALID_METRIC_KEY
    missing_persona: str = ERR_MISSING_PERSONA
    missing_mvp: str = ERR_MISSING_MVP


class UIConfig(BaseSettings):
    """UI Strings and Configuration."""

    page_size: int = Field(alias="UI_PAGE_SIZE", default=DEFAULT_PAGE_SIZE, description="Number of items per page in UI")

    no_ideas: str = MSG_NO_IDEAS
    generated_header: str = MSG_GENERATED_HEADER
    press_enter: str = MSG_PRESS_ENTER
    select_prompt: str = MSG_SELECT_PROMPT
    id_not_found: str = MSG_ID_NOT_FOUND
    invalid_input: str = MSG_INVALID_INPUT
    selected: str = MSG_SELECTED
    cycle_complete: str = MSG_CYCLE_COMPLETE
    topic_empty: str = MSG_TOPIC_EMPTY
    phase_start: str = MSG_PHASE_START
    researching: str = MSG_RESEARCHING
    wait: str = MSG_WAIT
    execution_error: str = MSG_EXECUTION_ERROR


class AgentConfig(BaseModel):
    """Configuration for a single agent in the UI."""

    model_config = SettingsConfigDict(frozen=True)

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

    max_steps: int = Field(alias="NEMAWASHI_MAX_STEPS", default=DEFAULT_NEMAWASHI_MAX_STEPS, description="Max iterations for consensus")
    tolerance: float = Field(alias="NEMAWASHI_TOLERANCE", default=DEFAULT_NEMAWASHI_TOLERANCE, description="Convergence tolerance")
    nomikai_boost: float = Field(alias="NEMAWASHI_NOMIKAI_BOOST", default=DEFAULT_NEMAWASHI_BOOST, description="Boost factor from Nomikai")
    nomikai_reduction: float = Field(alias="NEMAWASHI_NOMIKAI_REDUCTION", default=DEFAULT_NEMAWASHI_REDUCTION, description="Stubbornness reduction from Nomikai")


class V0Config(BaseSettings):
    """Configuration for v0.dev integration."""

    retry_max: int = Field(alias="V0_RETRY_MAX", default=DEFAULT_V0_RETRY_MAX, description="Max retries for API calls")
    retry_backoff: float = Field(alias="V0_RETRY_BACKOFF", default=DEFAULT_V0_RETRY_BACKOFF, description="Exponential backoff factor")


class SimulationConfig(BaseSettings):
    """Configuration for the Pyxel Simulation UI."""

    width: int = Field(default=DEFAULT_WIDTH, description="Window width")
    height: int = Field(default=DEFAULT_HEIGHT, description="Window height")
    fps: int = Field(default=DEFAULT_FPS, description="Frames per second")
    title: str = Field(default=MSG_SIM_TITLE, description="Window title")
    bg_color: int = Field(default=COLOR_BG, description="Background color")
    text_color: int = Field(default=COLOR_TEXT, description="Text color")

    chars_per_line: int = Field(default=DEFAULT_CHARS_PER_LINE, description="Characters per line in dialogue")
    line_height: int = Field(default=DEFAULT_LINE_HEIGHT, description="Line height in pixels")
    dialogue_x: int = Field(default=DEFAULT_DIALOGUE_X, description="Dialogue box X position")
    dialogue_y: int = Field(default=DEFAULT_DIALOGUE_Y, description="Dialogue box Y position")
    max_y: int = Field(default=DEFAULT_MAX_Y, description="Max Y for scrolling")
    waiting_msg: str = Field(default=MSG_WAITING_FOR_DEBATE, description="Message when waiting")

    console_sleep: float = Field(default=DEFAULT_CONSOLE_SLEEP, description="Sleep time for console fallback")
    max_turns: int = Field(default=DEFAULT_MAX_TURNS, description="Max turns in simulation")

    # Explicit fields for individual agents to allow env var overrides
    agent_new_emp: AgentConfig = Field(
        default_factory=lambda: AgentConfig(
            role="New Employee", label="NewEmp", color=COLOR_NEW_EMP, **AGENT_POS_NEW_EMP
        ),
        description="Configuration for New Employee Agent"
    )
    agent_finance: AgentConfig = Field(
        default_factory=lambda: AgentConfig(
            role="Finance Manager", label="Finance", color=COLOR_FINANCE, **AGENT_POS_FINANCE
        ),
        description="Configuration for Finance Agent"
    )
    agent_sales: AgentConfig = Field(
        default_factory=lambda: AgentConfig(
            role="Sales Manager", label="Sales", color=COLOR_SALES, **AGENT_POS_SALES
        ),
        description="Configuration for Sales Agent"
    )
    agent_cpo: AgentConfig = Field(
        default_factory=lambda: AgentConfig(
            role="CPO", label="CPO", color=COLOR_CPO, **AGENT_POS_CPO
        ),
        description="Configuration for CPO Agent"
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


class Settings(BaseSettings):
    """Configuration settings for the application."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="forbid")

    openai_api_key: SecretStr | None = Field(alias="OPENAI_API_KEY", default=None, description="OpenAI API Key")
    tavily_api_key: SecretStr | None = Field(alias="TAVILY_API_KEY", default=None, description="Tavily Search API Key")
    v0_api_key: SecretStr | None = Field(alias="V0_API_KEY", default=None, description="V0.dev API Key")
    v0_api_url: str = Field(alias="V0_API_URL", default=DEFAULT_V0_API_URL, description="V0.dev API URL")

    llm_model: str = Field(alias="LLM_MODEL", default="gpt-4o", description="LLM Model name")

    rag_persist_dir: str = Field(alias="RAG_PERSIST_DIR", default="./vector_store", description="Directory for RAG index")
    rag_chunk_size: int = Field(alias="RAG_CHUNK_SIZE", default=DEFAULT_RAG_CHUNK_SIZE, description="Chunk size for RAG")
    rag_max_document_length: int = Field(alias="RAG_MAX_DOC_LENGTH", default=DEFAULT_RAG_MAX_DOC_LENGTH, description="Max document length")
    rag_max_query_length: int = Field(alias="RAG_MAX_QUERY_LENGTH", default=DEFAULT_RAG_MAX_QUERY_LENGTH, description="Max query length")
    rag_max_index_size_mb: int = Field(alias="RAG_MAX_INDEX_SIZE_MB", default=DEFAULT_RAG_MAX_INDEX_SIZE_MB, description="Max index size in MB")
    rag_allowed_paths: list[str] = Field(default_factory=lambda: ["data", "vector_store", "tests"], description="Allowed directories for RAG")
    rag_rate_limit_interval: float = Field(alias="RAG_RATE_LIMIT_INTERVAL", default=0.1, description="Min interval between RAG calls in seconds")
    rag_scan_depth_limit: int = Field(alias="RAG_SCAN_DEPTH_LIMIT", default=10, description="Max recursion depth for directory scanning")
    rag_batch_size: int = Field(alias="RAG_BATCH_SIZE", default=DEFAULT_RAG_BATCH_SIZE, description="Batch size for RAG ingestion")

    feature_chunk_size: int = Field(alias="FEATURE_CHUNK_SIZE", default=DEFAULT_FEATURE_CHUNK_SIZE, description="Chunk size for feature extraction")

    circuit_breaker_fail_max: int = Field(alias="CB_FAIL_MAX", default=DEFAULT_CB_FAIL_MAX, description="Circuit breaker fail threshold")
    circuit_breaker_reset_timeout: int = Field(alias="CB_RESET_TIMEOUT", default=DEFAULT_CB_RESET_TIMEOUT, description="Circuit breaker reset timeout")

    iterator_safety_limit: int = Field(alias="ITERATOR_SAFETY_LIMIT", default=DEFAULT_ITERATOR_SAFETY_LIMIT, description="Max items for iterators")

    search_max_results: int = Field(alias="SEARCH_MAX_RESULTS", default=5, description="Max search results")
    search_depth: str = Field(alias="SEARCH_DEPTH", default="advanced", description="Search depth (basic/advanced)")
    search_query_template: str = Field(
        alias="SEARCH_QUERY_TEMPLATE",
        default="emerging business trends and painful problems in {topic}",
        description="Template for search queries"
    )

    log_level: str = Field(alias="LOG_LEVEL", default="INFO", description="Logging level")
    ui_page_size: int = Field(alias="UI_PAGE_SIZE", default=DEFAULT_PAGE_SIZE, description="Page size for UI")

    # Nested configurations - Use Field to allow Pydantic to manage them
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    errors: ErrorMessages = Field(default_factory=ErrorMessages)
    ui: UIConfig = Field(default_factory=UIConfig)
    simulation: SimulationConfig = Field(default_factory=SimulationConfig)
    nemawashi: NemawashiConfig = Field(default_factory=NemawashiConfig)
    v0: V0Config = Field(default_factory=V0Config)

    def model_post_init(self, __context: object) -> None:
        """Validate API keys on initialization."""
        super().model_post_init(__context)
        self.validate_api_keys()

    def validate_api_keys(self) -> Self:
        """Validate API keys are present and have correct format."""
        if not self.openai_api_key:
            raise ValueError(ERR_CONFIG_MISSING_OPENAI_KEY)
        ConfigValidators.validate_openai_key(self.openai_api_key)

        if not self.tavily_api_key:
            raise ValueError(ERR_CONFIG_MISSING_TAVILY_KEY)
        ConfigValidators.validate_tavily_key(self.tavily_api_key)

        return self

    def rotate_keys(self) -> None:
        """Placeholder for key rotation."""


@lru_cache
def get_settings() -> Settings:
    """Load and cache settings."""
    return Settings()
