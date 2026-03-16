import typing
from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.validators import ConfigValidators


class ValidationConfig(BaseSettings):
    """Validation constraints for domain models."""

    min_title_length: int = Field(description="Minimum length for titles")
    max_title_length: int = Field(description="Maximum length for titles")
    min_content_length: int = Field(description="Minimum length for content blocks")
    max_content_length: int = Field(description="Maximum length for content blocks")

    min_list_length: int = Field(description="Minimum items in lists")
    max_list_length: int = Field(description="Maximum items in lists")

    max_custom_metrics: int = Field(description="Maximum custom metrics allowed")
    min_metric_value: float = Field(description="Minimum value for metrics")
    max_percentage_value: float = Field(description="Maximum percentage value")


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
    invalid_api_key_format: str = "Invalid API key format: {key_name}."
    api_key_empty: str = "{key_name} cannot be empty or whitespace-only."
    api_key_too_short: str = "{key_name} is too short."
    api_key_too_long: str = "{key_name} is too long."
    api_key_invalid_prefix: str = "{key_name} must start with '{prefix}'."
    api_key_invalid_chars: str = "{key_name} contains invalid characters."


class UIConfig(BaseSettings):
    """UI Strings and Configuration."""

    page_size: int = Field(
        alias="UI_PAGE_SIZE",
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
    max_stakeholders: int = Field(
        alias="NEMAWASHI_MAX_STAKEHOLDERS",
        description="Maximum allowed stakeholders in influence network",
    )
    """Configuration for Nemawashi Consensus Building."""

    max_steps: int = Field(
        alias="NEMAWASHI_MAX_STEPS",
        description="Max iterations for consensus",
    )
    tolerance: float = Field(
        alias="NEMAWASHI_TOLERANCE",
        description="Convergence tolerance",
    )
    nomikai_boost: float = Field(
        alias="NEMAWASHI_NOMIKAI_BOOST",
        description="Boost factor from Nomikai",
    )
    nomikai_reduction: float = Field(
        alias="NEMAWASHI_NOMIKAI_REDUCTION",
        description="Stubbornness reduction from Nomikai",
    )


class FileConfig(BaseSettings):
    """Configuration for FileService operations."""

    max_workers: int = Field(
        alias="FILE_MAX_WORKERS",
        description="Max thread pool workers for async file operations",
    )
    output_directory: str = Field(
        alias="OUTPUT_DIR", description="Directory to save final artifacts"
    )


class GraphConfig(BaseSettings):
    """Configuration for LangGraph workflow execution."""

    interrupt_points: list[str] = Field(
        alias="GRAPH_INTERRUPT_POINTS",
        description="List of node names where the graph should interrupt execution for HITL",
    )


class V0Config(BaseSettings):
    """Configuration for v0.dev integration."""

    retry_max: int = Field(alias="V0_RETRY_MAX", description="Max retries for API calls")
    retry_backoff: float = Field(
        alias="V0_RETRY_BACKOFF",
        description="Exponential backoff factor",
    )


class TurnSequenceItem(BaseModel):
    node_name: str
    role: str
    description: str


class SimulationConfig(BaseSettings):
    """Configuration for the Pyxel Simulation UI."""

    width: int = Field(alias="SIMULATION_WIDTH", description="Window width")
    height: int = Field(alias="SIMULATION_HEIGHT", description="Window height")
    fps: int = Field(alias="SIMULATION_FPS", description="Frames per second")
    title: str = Field(alias="SIMULATION_TITLE", description="Window title")
    bg_color: int = Field(alias="COLOR_BG", description="Background color")
    text_color: int = Field(alias="COLOR_TEXT", description="Text color")

    chars_per_line: int = Field(
        alias="SIMULATION_CHARS_PER_LINE", description="Characters per line in dialogue"
    )
    line_height: int = Field(alias="SIMULATION_LINE_HEIGHT", description="Line height in pixels")
    dialogue_x: int = Field(alias="SIMULATION_DIALOGUE_X", description="Dialogue box X position")
    dialogue_y: int = Field(alias="SIMULATION_DIALOGUE_Y", description="Dialogue box Y position")
    max_y: int = Field(alias="SIMULATION_MAX_Y", description="Max Y for scrolling")
    waiting_msg: str = Field(alias="SIMULATION_WAITING_MSG", description="Message when waiting")

    turn_sequence_str: str = Field(
        alias="SIMULATION_TURN_SEQUENCE",
        description="List of simulation steps defining the turn sequence as a JSON string.",
    )

    @property
    def turn_sequence(self) -> list[dict[str, str]]:
        import json

        parsed = json.loads(self.turn_sequence_str)
        # Validate against schema
        validated = [TurnSequenceItem(**item) for item in parsed]
        return [v.model_dump() for v in validated]

    console_sleep: float = Field(
        alias="SIMULATION_CONSOLE_SLEEP", description="Sleep time for console fallback"
    )
    max_turns: int = Field(alias="SIMULATION_MAX_TURNS", description="Max turns in simulation")

    # Explicit fields for individual agents to allow env var overrides
    agent_new_emp_pos: dict[str, int] = Field(
        default_factory=lambda: {"x": 10, "y": 20, "w": 10, "h": 10, "text_x": 0, "text_y": 0},
        alias="AGENT_POS_NEW_EMP",
        description="New Employee Agent layout settings",
    )
    agent_new_emp_color: int = Field(alias="COLOR_NEW_EMP", description="New Employee Agent Color")

    agent_finance_pos: dict[str, int] = Field(
        default_factory=lambda: {"x": 50, "y": 20, "w": 10, "h": 10, "text_x": 0, "text_y": 0},
        alias="AGENT_POS_FINANCE",
        description="Finance Agent layout settings",
    )
    agent_finance_color: int = Field(alias="COLOR_FINANCE", description="Finance Agent Color")

    agent_sales_pos: dict[str, int] = Field(
        default_factory=lambda: {"x": 90, "y": 20, "w": 10, "h": 10, "text_x": 0, "text_y": 0},
        alias="AGENT_POS_SALES",
        description="Sales Agent layout settings",
    )
    agent_sales_color: int = Field(alias="COLOR_SALES", description="Sales Agent Color")

    agent_cpo_pos: dict[str, int] = Field(
        default_factory=lambda: {"x": 130, "y": 20, "w": 10, "h": 10, "text_x": 0, "text_y": 0},
        alias="AGENT_POS_CPO",
        description="CPO Agent layout settings",
    )
    agent_cpo_color: int = Field(alias="COLOR_CPO", description="CPO Agent Color")

    @property
    def agent_new_emp(self) -> AgentConfig:
        return AgentConfig(
            role="New Employee",
            label="NewEmp",
            color=self.agent_new_emp_color,
            **self.agent_new_emp_pos,
        )

    @property
    def agent_finance(self) -> AgentConfig:
        return AgentConfig(
            role="Finance Manager",
            label="Finance",
            color=self.agent_finance_color,
            **self.agent_finance_pos,
        )

    @property
    def agent_sales(self) -> AgentConfig:
        return AgentConfig(
            role="Sales Manager",
            label="Sales",
            color=self.agent_sales_color,
            **self.agent_sales_pos,
        )

    @property
    def agent_cpo(self) -> AgentConfig:
        return AgentConfig(
            role="CPO", label="CPO", color=self.agent_cpo_color, **self.agent_cpo_pos
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
        description="Minimum ROI for approval",
    )
    default_cac: float = Field(alias="DEFAULT_CAC", description="Fallback CAC")
    default_arpu: float = Field(alias="DEFAULT_ARPU", description="Fallback ARPU")
    default_churn: float = Field(alias="DEFAULT_CHURN", description="Fallback Churn Rate")
    max_llm_response_size: int = Field(
        alias="MAX_LLM_RESPONSE_SIZE",
        description="Max bytes for LLM JSON response",
    )
    max_content_multiplier: int = Field(
        alias="MAX_CONTENT_MULTIPLIER",
        description="Multiplier applied to max_llm_response_size for validations",
    )
    output_path: str = Field(alias="RINGI_SHO_PATH", description="Path for Ringi-sho output")
    search_query_template: str = Field(
        alias="GOV_SEARCH_QUERY_TEMPLATE",
        description="Template for financial search",
    )
    max_search_result_size: int = Field(
        alias="MAX_SEARCH_RESULT_SIZE",
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

    model_config = SettingsConfigDict(env_file_encoding="utf-8", extra="forbid")

    # Explicitly enforce required keys without defaults
    openai_api_key: SecretStr = Field(alias="OPENAI_API_KEY", description="OpenAI API Key")
    tavily_api_key: SecretStr = Field(alias="TAVILY_API_KEY", description="Tavily Search API Key")
    v0_api_key: SecretStr | None = Field(alias="V0_API_KEY", description="V0.dev API Key")

    @field_validator("openai_api_key", mode="before")
    @classmethod
    def validate_openai_key_before(cls, v: str | SecretStr) -> SecretStr:
        secret_str = v if isinstance(v, SecretStr) else SecretStr(str(v))
        try:
            ConfigValidators.validate_openai_key(secret_str)
        except Exception as e:
            base_msg = ErrorMessages().invalid_api_key_format.format(key_name="OpenAI API Key")
            msg = f"{base_msg} {e}"
            raise ValueError(msg) from e
        return secret_str

    @field_validator("tavily_api_key", mode="before")
    @classmethod
    def validate_tavily_key_before(cls, v: str | SecretStr) -> SecretStr:
        secret_str = v if isinstance(v, SecretStr) else SecretStr(str(v))
        try:
            ConfigValidators.validate_tavily_key(secret_str)
        except Exception as e:
            base_msg = ErrorMessages().invalid_api_key_format.format(key_name="Tavily API Key")
            msg = f"{base_msg} {e}"
            raise ValueError(msg) from e
        return secret_str

    @field_validator("v0_api_key", mode="before")
    @classmethod
    def validate_v0_api_key_before(cls, v: str | SecretStr | None) -> SecretStr | None:
        if v is None:
            return None
        secret_str = v if isinstance(v, SecretStr) else SecretStr(str(v))
        if not secret_str.get_secret_value():
            return None
        try:
            ConfigValidators.validate_v0_key(secret_str)
        except Exception as e:
            base_msg = ErrorMessages().invalid_api_key_format.format(key_name="v0.dev API Key")
            msg = f"{base_msg} {e}"
            raise ValueError(msg) from e
        return secret_str

    v0_api_url: str = Field(
        alias="V0_API_URL",
        description="V0.dev API URL",
    )

    @field_validator("v0_api_url")
    @classmethod
    def validate_v0_url(cls, v: str) -> str:
        from urllib.parse import urlparse

        parsed = urlparse(v)
        if parsed.scheme != "https":
            msg = "V0 API URL must use HTTPS."
            raise ValueError(msg)
        if not parsed.netloc:
            msg = "V0 API URL must contain a valid domain."
            raise ValueError(msg)
        return v

    llm_model: str = Field(alias="LLM_MODEL", description="LLM Model name")

    rag_persist_dir: str = Field(alias="RAG_PERSIST_DIR", description="Directory for RAG index")

    @field_validator("rag_persist_dir")
    @classmethod
    def validate_rag_persist_dir(cls, v: str) -> str:
        from pathlib import Path

        try:
            resolved = Path(v).resolve()
            if "\x00" in str(resolved):
                msg = "Path contains null bytes."
                raise ValueError(msg)  # noqa: TRY301
            # Basic validation to ensure it doesn't traverse to root unexpectedly
            if str(resolved) == "/" or str(resolved) == "C:\\":
                msg = "RAG persist dir cannot be root directory."
                raise ValueError(msg)  # noqa: TRY301
        except Exception as e:
            msg = f"Invalid RAG persist directory: {e}"
            raise ValueError(msg) from e
        return v

    rag_chunk_size: int = Field(alias="RAG_CHUNK_SIZE", description="Chunk size for RAG")
    rag_max_document_length: int = Field(
        alias="RAG_MAX_DOC_LENGTH",
        description="Max document length",
    )
    rag_max_query_length: int = Field(
        alias="RAG_MAX_QUERY_LENGTH",
        description="Max query length",
    )
    rag_max_index_size_mb: int = Field(
        alias="RAG_MAX_INDEX_SIZE_MB",
        description="Max index size in MB",
    )
    rag_allowed_paths: str | list[str] = Field(
        alias="RAG_ALLOWED_PATHS",
        description="Allowed directories for RAG",
    )
    rag_rate_limit_interval: float = Field(
        alias="RAG_RATE_LIMIT_INTERVAL",
        description="Min interval between RAG calls in seconds",
    )
    rag_scan_depth_limit: int = Field(
        alias="RAG_SCAN_DEPTH_LIMIT",
        description="Max recursion depth for directory scanning",
    )

    @field_validator("rag_allowed_paths", mode="before")
    @classmethod
    def parse_allowed_paths(cls, v: str | list[str]) -> list[str]:
        paths = [p.strip() for p in v.split(",")] if isinstance(v, str) else v
        valid_paths = []
        for p in paths:
            if not p:
                continue
            if "\x00" in str(p) or ".." in str(p):
                msg = "Directory traversal or null byte detected in RAG allowed paths."
                raise ValueError(msg)
            valid_paths.append(p)
        if not valid_paths:
            msg = "RAG allowed paths cannot be empty."
            raise ValueError(msg)
        return valid_paths

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
        description="Batch size for RAG ingestion",
    )
    rag_query_timeout: float = Field(
        alias="RAG_QUERY_TIMEOUT", description="Timeout for RAG queries in seconds"
    )

    feature_chunk_size: int = Field(
        alias="FEATURE_CHUNK_SIZE",
        description="Chunk size for feature extraction",
    )

    circuit_breaker_fail_max: int = Field(
        alias="CB_FAIL_MAX",
        description="Circuit breaker fail threshold",
    )
    circuit_breaker_reset_timeout: int = Field(
        alias="CB_RESET_TIMEOUT",
        description="Circuit breaker reset timeout",
    )

    @field_validator("circuit_breaker_fail_max")
    @classmethod
    def validate_circuit_breaker_fail_max(cls, v: int) -> int:
        if not (1 <= v <= 100):
            msg = "circuit_breaker_fail_max must be between 1 and 100."
            raise ValueError(msg)
        return v

    @field_validator("circuit_breaker_reset_timeout")
    @classmethod
    def validate_circuit_breaker_reset_timeout(cls, v: int) -> int:
        if not (10 <= v <= 3600):
            msg = "circuit_breaker_reset_timeout must be between 10 and 3600."
            raise ValueError(msg)
        return v

    iterator_safety_limit: int = Field(
        alias="ITERATOR_SAFETY_LIMIT",
        description="Max items for iterators",
    )

    search_max_results: int = Field(alias="SEARCH_MAX_RESULTS", description="Max search results")
    search_depth: str = Field(alias="SEARCH_DEPTH", description="Search depth (basic/advanced)")
    search_query_template: str = Field(
        alias="SEARCH_QUERY_TEMPLATE",
        description="Template for search queries",
    )

    @field_validator("search_query_template")
    @classmethod
    def validate_search_template(cls, v: str) -> str:
        if "{topic}" not in v:
            msg = "search_query_template must contain {topic} placeholder."
            raise ValueError(msg)
        return v

    log_level: str = Field(
        alias="LOG_LEVEL",
        description="Logging level",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
    )
    ui_page_size: int = Field(alias="UI_PAGE_SIZE", description="Page size for UI", ge=1, le=100)

    # Nested configurations - Use Field to allow Pydantic to manage them
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    errors: ErrorMessages = Field(default_factory=ErrorMessages)
    ui: UIConfig = Field(default_factory=UIConfig)
    simulation: SimulationConfig = Field(default_factory=SimulationConfig)
    nemawashi: NemawashiConfig = Field(default_factory=NemawashiConfig)
    v0: V0Config = Field(default_factory=V0Config)
    governance: GovernanceConfig = Field(default_factory=GovernanceConfig)
    file_service: FileConfig = Field(default_factory=FileConfig)
    graph: GraphConfig = Field(default_factory=GraphConfig)


# Global settings state override
_settings_override_state: dict[str, "typing.Any"] = {"override": None}


def set_settings_override(settings: Settings | None) -> None:
    _settings_override_state["override"] = settings


@lru_cache
def get_settings() -> Settings:
    """
    Load and cache settings with a robust startup pre-validation fallback.
    Prevents ungraceful crashes by catching Pydantic ValidationErrors for missing
    required environment variables and outputting a clean summary before exit.
    """
    if _settings_override_state["override"]:
        return _settings_override_state["override"]  # type: ignore[no-any-return]

    import sys

    from pydantic import ValidationError

    try:
        return Settings()
    except ValidationError as e:
        # Don't use standard logger yet as it might not be configured
        print("\n" + "=" * 60)  # noqa: T201
        print("CRITICAL CONFIGURATION ERROR: Missing or Invalid Environment Variables")  # noqa: T201
        print("=" * 60)  # noqa: T201
        for err in e.errors():
            field_path = ".".join([str(loc) for loc in err["loc"]])
            msg = err["msg"]
            print(f"- {field_path}: {msg}")  # noqa: T201
        print("\nPlease check your .env file and ensure all required variables are set.")  # noqa: T201
        print("=" * 60 + "\n")  # noqa: T201

        # Allow tests to catch this by strictly throwing it when pytest is running
        import os

        if "PYTEST_CURRENT_TEST" in os.environ or "pytest" in sys.modules:
            raise

        sys.exit(1)
