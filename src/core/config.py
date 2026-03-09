import threading

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.constants import (
    DEFAULT_ARPU,
    DEFAULT_CAC,
    DEFAULT_CB_FAIL_MAX,
    DEFAULT_CB_RESET_TIMEOUT,
    DEFAULT_CHARS_PER_LINE,
    DEFAULT_CHURN,
    DEFAULT_CONSOLE_SLEEP,
    DEFAULT_DIALOGUE_X,
    DEFAULT_DIALOGUE_Y,
    DEFAULT_FEATURE_CHUNK_SIZE,
    DEFAULT_FPS,
    DEFAULT_HEIGHT,
    DEFAULT_ITERATOR_SAFETY_LIMIT,
    DEFAULT_LINE_HEIGHT,
    DEFAULT_MAX_CONTENT_LENGTH,
    DEFAULT_MAX_CUSTOM_METRICS,
    DEFAULT_MAX_FILES,
    DEFAULT_MAX_LIST_LENGTH,
    DEFAULT_MAX_LLM_RESPONSE_SIZE,
    DEFAULT_MAX_PERCENTAGE_VALUE,
    DEFAULT_MAX_SEARCH_RESULT_SIZE,
    DEFAULT_MAX_TITLE_LENGTH,
    DEFAULT_MAX_TURNS,
    DEFAULT_MAX_Y,
    DEFAULT_MIN_CONTENT_LENGTH,
    DEFAULT_MIN_LIST_LENGTH,
    DEFAULT_MIN_METRIC_VALUE,
    DEFAULT_MIN_ROI_THRESHOLD,
    DEFAULT_MIN_TITLE_LENGTH,
    DEFAULT_NEMAWASHI_BOOST,
    DEFAULT_NEMAWASHI_MAX_STEPS,
    DEFAULT_NEMAWASHI_REDUCTION,
    DEFAULT_NEMAWASHI_TOLERANCE,
    DEFAULT_PAGE_SIZE,
    DEFAULT_RAG_CHUNK_SIZE,
    DEFAULT_RAG_MAX_DOC_LENGTH,
    DEFAULT_RAG_MAX_INDEX_SIZE_MB,
    DEFAULT_RAG_MAX_QUERY_LENGTH,
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
from src.core.interfaces import IConfigValidator
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

    min_title_length: int = Field(
        default=DEFAULT_MIN_TITLE_LENGTH, description="Minimum length for titles"
    )
    max_title_length: int = Field(
        default=DEFAULT_MAX_TITLE_LENGTH, description="Maximum length for titles"
    )
    min_content_length: int = Field(
        default=DEFAULT_MIN_CONTENT_LENGTH, description="Minimum length for content blocks"
    )
    max_content_length: int = Field(
        default=DEFAULT_MAX_CONTENT_LENGTH, description="Maximum length for content blocks"
    )

    min_list_length: int = Field(
        default=DEFAULT_MIN_LIST_LENGTH, description="Minimum items in lists"
    )
    max_list_length: int = Field(
        default=DEFAULT_MAX_LIST_LENGTH, description="Maximum items in lists"
    )

    max_custom_metrics: int = Field(
        default=DEFAULT_MAX_CUSTOM_METRICS, description="Maximum custom metrics allowed"
    )
    min_metric_value: float = Field(
        default=DEFAULT_MIN_METRIC_VALUE, description="Minimum value for metrics"
    )
    max_percentage_value: float = Field(
        default=DEFAULT_MAX_PERCENTAGE_VALUE, description="Maximum percentage value"
    )


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

    page_size: int = Field(
        alias="UI_PAGE_SIZE",
        default=DEFAULT_PAGE_SIZE,
        description="Number of items per page in UI",
    )

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


class AgentConfig(BaseSettings):
    """Configuration for a single agent in the UI."""

    model_config = SettingsConfigDict(frozen=True)

    role: str = Field(..., description="Role name of the agent")
    label: str = Field(..., description="Short label for UI")
    color: int = Field(..., description="Color code for the agent")
    x: int = Field(..., description="X position", ge=0, le=800)
    y: int = Field(..., description="Y position", ge=0, le=800)
    w: int = Field(..., description="Width", ge=10, le=800)
    h: int = Field(..., description="Height", ge=10, le=800)
    text_x: int = Field(..., description="Text X pos", ge=0, le=800)
    text_y: int = Field(..., description="Text Y pos", ge=0, le=800)

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
        default=DEFAULT_NEMAWASHI_MAX_STEPS,
        description="Max iterations for consensus",
    )
    tolerance: float = Field(
        alias="NEMAWASHI_TOLERANCE",
        default=DEFAULT_NEMAWASHI_TOLERANCE,
        description="Convergence tolerance",
    )
    nomikai_boost: float = Field(
        alias="NEMAWASHI_NOMIKAI_BOOST",
        default=DEFAULT_NEMAWASHI_BOOST,
        description="Boost factor from Nomikai",
    )
    nomikai_reduction: float = Field(
        alias="NEMAWASHI_NOMIKAI_REDUCTION",
        default=DEFAULT_NEMAWASHI_REDUCTION,
        description="Stubbornness reduction from Nomikai",
    )
    timeout: float = Field(
        alias="NEMAWASHI_TIMEOUT",
        default=10.0,
        description="Timeout for consensus calculation in seconds",
    )


class V0Config(BaseSettings):
    """Configuration for v0.dev integration."""

    retry_max: int = Field(
        alias="V0_RETRY_MAX", default=DEFAULT_V0_RETRY_MAX, description="Max retries for API calls"
    )
    retry_backoff: float = Field(
        alias="V0_RETRY_BACKOFF",
        default=DEFAULT_V0_RETRY_BACKOFF,
        description="Exponential backoff factor",
    )


class SimulationConfig(BaseSettings):
    """Configuration for the Pyxel Simulation UI."""

    width: int = Field(default=DEFAULT_WIDTH, description="Window width")
    height: int = Field(default=DEFAULT_HEIGHT, description="Window height")

    @field_validator("width", "height")
    @classmethod
    def validate_dimensions(cls, v: int) -> int:
        if v < 100 or v > 800:
            msg = "Dimensions must be between 100 and 800"
            raise ValueError(msg)
        return v
    fps: int = Field(default=DEFAULT_FPS, description="Frames per second")
    title: str = Field(default=MSG_SIM_TITLE, description="Window title")
    bg_color: int = Field(default=COLOR_BG, description="Background color")
    text_color: int = Field(default=COLOR_TEXT, description="Text color")

    chars_per_line: int = Field(
        default=DEFAULT_CHARS_PER_LINE, description="Characters per line in dialogue"
    )
    line_height: int = Field(default=DEFAULT_LINE_HEIGHT, description="Line height in pixels")
    dialogue_x: int = Field(default=DEFAULT_DIALOGUE_X, description="Dialogue box X position")
    dialogue_y: int = Field(default=DEFAULT_DIALOGUE_Y, description="Dialogue box Y position")
    max_y: int = Field(default=DEFAULT_MAX_Y, description="Max Y for scrolling")
    waiting_msg: str = Field(default=MSG_WAITING_FOR_DEBATE, description="Message when waiting")

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

    console_sleep: float = Field(
        default=DEFAULT_CONSOLE_SLEEP, description="Sleep time for console fallback"
    )
    max_turns: int = Field(default=DEFAULT_MAX_TURNS, description="Max turns in simulation")

    # Explicit fields for individual agents to allow env var overrides
    agent_new_emp: AgentConfig = Field(
        default_factory=lambda: AgentConfig(
            role="New Employee",
            label="NewEmp",
            color=COLOR_NEW_EMP,
            **AGENT_POS_NEW_EMP,  # type: ignore[arg-type]
        ),
        description="Configuration for New Employee Agent",
    )
    agent_finance: AgentConfig = Field(
        default_factory=lambda: AgentConfig(
            role="Finance Manager",
            label="Finance",
            color=COLOR_FINANCE,
            **AGENT_POS_FINANCE,  # type: ignore[arg-type]
        ),
        description="Configuration for Finance Agent",
    )
    agent_sales: AgentConfig = Field(
        default_factory=lambda: AgentConfig(
            role="Sales Manager",
            label="Sales",
            color=COLOR_SALES,
            **AGENT_POS_SALES,  # type: ignore[arg-type]
        ),
        description="Configuration for Sales Agent",
    )
    agent_cpo: AgentConfig = Field(
        default_factory=lambda: AgentConfig(
            role="CPO",
            label="CPO",
            color=COLOR_CPO,
            **AGENT_POS_CPO,  # type: ignore[arg-type]
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
        default=DEFAULT_MIN_ROI_THRESHOLD,
        description="Minimum ROI for approval",
    )
    default_cac: float = Field(alias="DEFAULT_CAC", default=DEFAULT_CAC, description="Fallback CAC")
    default_arpu: float = Field(
        alias="DEFAULT_ARPU", default=DEFAULT_ARPU, description="Fallback ARPU"
    )
    default_churn: float = Field(
        alias="DEFAULT_CHURN", default=DEFAULT_CHURN, description="Fallback Churn Rate"
    )
    max_llm_response_size: int = Field(
        alias="MAX_LLM_RESPONSE_SIZE",
        default=DEFAULT_MAX_LLM_RESPONSE_SIZE,
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
        default=DEFAULT_MAX_SEARCH_RESULT_SIZE,
        description="Max chars for search result context",
    )


class RAGConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")
    persist_dir: str = Field(default="./vector_store", description="Directory for RAG index")
    chunk_size: int = Field(default=DEFAULT_RAG_CHUNK_SIZE, description="Chunk size for RAG")
    max_transcripts: int = Field(default=50, description="Max number of transcripts to ingest")
    batch_size: int = Field(default=10, description="Batch size for transcript ingestion")
    max_document_length: int = Field(
        default=DEFAULT_RAG_MAX_DOC_LENGTH,
        description="Max document length",
    )

    @field_validator("persist_dir")
    @classmethod
    def validate_persist_dir(cls, v: str) -> str:
        import pathlib
        path = pathlib.Path(v).resolve()
        cwd = pathlib.Path.cwd().resolve()

        # In a real system you'd want a specific root directory, for now just ensure it's not trying
        # to go way up the filesystem
        try:
            path.relative_to(cwd)
        except ValueError as err:
            # Maybe they specified an absolute path like /tmp/vector_store,
            # We'll allow it as long as it's not root or obviously malicious
            if path == pathlib.Path("/"):
                msg = "persist_dir cannot be root directory"
                raise ValueError(msg) from err
        return str(path)
    max_query_length: int = Field(
        default=DEFAULT_RAG_MAX_QUERY_LENGTH,
        description="Max query length",
    )
    max_index_size_mb: int = Field(
        default=DEFAULT_RAG_MAX_INDEX_SIZE_MB,
        description="Max index size in MB",
    )
    allowed_paths: list[str] = Field(
        default_factory=lambda: ["data", "vector_store", "tests"],
        description="Allowed directories for RAG",
    )
    rate_limit_interval: float = Field(
        default=0.1,
        description="Min interval between RAG calls in seconds",
    )
    scan_depth_limit: int = Field(
        default=10,
        description="Max recursion depth for directory scanning",
    )
    max_files: int = Field(
        default=DEFAULT_MAX_FILES,
        description="Maximum files to scan",
    )
    query_timeout: float = Field(default=30.0, description="Timeout for RAG queries in seconds")


class SearchConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")
    max_results: int = Field(default=5, description="Max search results")
    depth: str = Field(default="advanced", description="Search depth (basic/advanced)")
    query_template: str = Field(
        default="emerging business trends and painful problems in {topic}",
        description="Template for search queries",
    )


class ResiliencyConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")
    circuit_breaker_fail_max: int = Field(
        default=DEFAULT_CB_FAIL_MAX, description="Circuit breaker fail threshold"
    )
    circuit_breaker_reset_timeout: int = Field(
        default=DEFAULT_CB_RESET_TIMEOUT, description="Circuit breaker reset timeout"
    )
    iterator_safety_limit: int = Field(
        default=DEFAULT_ITERATOR_SAFETY_LIMIT, description="Max items for iterators"
    )


import os  # noqa: E402


class Settings(BaseSettings):
    """Configuration settings for the application."""

    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    openai_api_key: SecretStr = Field(
        alias="OPENAI_API_KEY", description="OpenAI API Key", min_length=20
    )
    tavily_api_key: SecretStr = Field(
        alias="TAVILY_API_KEY", description="Tavily Search API Key", min_length=20
    )
    llm_model: str = Field(default="gpt-4o", description="LLM model name")


    canvas_output_dir: str = Field(
        alias="CANVAS_OUTPUT_DIR",
        default="outputs/canvas",
        description="Directory for PDF Canvas outputs",
    )

    feature_chunk_size: int = Field(
        alias="FEATURE_CHUNK_SIZE",
        default=DEFAULT_FEATURE_CHUNK_SIZE,
        description="Chunk size for feature extraction",
    )

    log_level: str = Field(alias="LOG_LEVEL", default="INFO", description="Logging level")
    ui_page_size: int = Field(
        alias="UI_PAGE_SIZE", default=DEFAULT_PAGE_SIZE, description="Page size for UI"
    )

    # Nested configurations
    rag: RAGConfig = Field(default_factory=RAGConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    resiliency: ResiliencyConfig = Field(default_factory=ResiliencyConfig)

    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    errors: ErrorMessages = Field(default_factory=ErrorMessages)
    ui: UIConfig = Field(default_factory=UIConfig)
    simulation: SimulationConfig = Field(default_factory=SimulationConfig)
    nemawashi: NemawashiConfig = Field(default_factory=NemawashiConfig)
    v0: V0Config = Field(default_factory=V0Config)
    governance: GovernanceConfig = Field(default_factory=GovernanceConfig)

class CredentialManager:
    """
    Manager specifically responsible for handling sensitive credentials securely.
    """
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def rotate_keys(self) -> None:
        """Placeholder for credential rotation logic."""


class SettingsFactory:
    """
    Factory to build Settings using an injected validator service.
    This allows fully decoupled testing and mock validations.
    """
    def __init__(self, validator: IConfigValidator | None = None) -> None:
        self.validator = validator

    def build(self) -> Settings:
        settings = Settings()
        if self.validator:
            self.validator.validate_openai_key(settings.openai_api_key)
            self.validator.validate_tavily_key(settings.tavily_api_key)
        return settings


_legacy_settings_instance: Settings | None = None
_legacy_lock = threading.Lock()

def get_settings() -> Settings:
    """Legacy singleton retriever. Left for backwards compatibility across tests."""
    global _legacy_settings_instance
    if _legacy_settings_instance is None:
        with _legacy_lock:
            if _legacy_settings_instance is None:
                from src.core.validators import ConfigValidators
                _legacy_settings_instance = SettingsFactory(validator=ConfigValidators()).build()
    return _legacy_settings_instance

def clear_settings_cache() -> None:
    """Legacy helper for testing configurations."""
    global _legacy_settings_instance
    with _legacy_lock:
        _legacy_settings_instance = None
