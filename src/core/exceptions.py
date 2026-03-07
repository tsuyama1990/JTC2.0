class AppError(Exception):
    """Base exception for the application."""


class ConfigurationError(AppError):
    """Raised when there is a configuration error."""


class NetworkError(AppError):
    """Raised when there is a network or external service error."""


class ValidationError(AppError):
    """Raised when data validation fails."""


class CalculationError(AppError):
    """Raised when a mathematical calculation fails."""


class V0GenerationError(AppError):
    """Raised when v0.dev generation fails."""
