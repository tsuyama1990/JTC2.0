from typing import TYPE_CHECKING

from src.core.config import get_settings

if TYPE_CHECKING:
    from src.domain_models.state import GlobalState


import re
from typing import Any

from src.core.constants import (
    ERR_MATRIX_SHAPE,
    ERR_MATRIX_STOCHASTICITY,
    ERR_MATRIX_VALUES,
    ERR_STAKEHOLDER_MISMATCH,
)


class CommonValidators:
    @staticmethod
    def validate_dense_matrix(matrix: list[list[float]], n: int, tol: float) -> None:
        if len(matrix) != n:
            raise ValueError(ERR_STAKEHOLDER_MISMATCH)
        for row in matrix:
            if len(row) != n:
                raise ValueError(ERR_MATRIX_SHAPE)
            for val in row:
                if not (0.0 <= val <= 1.0):
                    raise ValueError(ERR_MATRIX_VALUES)
            row_sum = sum(row)
            if not (1.0 - tol <= row_sum <= 1.0 + tol):
                raise ValueError(ERR_MATRIX_STOCHASTICITY)

    @staticmethod
    def validate_sparse_matrix(matrix: Any, n: int, tol: float) -> None:
        row_sums = [0.0] * n
        for entry in matrix:
            row, col, val = getattr(entry, "row", 0), getattr(entry, "col", 0), getattr(entry, "val", 0.0)
            if not (0 <= row < n) or not (0 <= col < n):
                raise ValueError(ERR_MATRIX_SHAPE)
            row_sums[row] += val
        for s in row_sums:
            if not (1.0 - tol <= s <= 1.0 + tol):
                raise ValueError(ERR_MATRIX_STOCHASTICITY)

    @staticmethod
    def validate_matrix(matrix: Any, num_stakeholders: int) -> None:
        """Validate influence network matrix (dense or sparse)."""
        TOLERANCE = 1e-6
        if isinstance(matrix, list) and matrix and isinstance(matrix[0], list):
            CommonValidators.validate_dense_matrix(matrix, num_stakeholders, TOLERANCE)
        else:
            CommonValidators.validate_sparse_matrix(matrix, num_stakeholders, TOLERANCE)

    @staticmethod
    def validate_metrics_dict(v: dict[str, Any]) -> dict[str, float]:
        from src.core.config import get_settings

        settings = get_settings()

        if len(v) > settings.validation.max_custom_metrics:
            msg = settings.errors.too_many_metrics.format(
                limit=settings.validation.max_custom_metrics
            )
            raise ValueError(msg)

        for key, value in v.items():
            if not key.isidentifier():
                msg = settings.errors.invalid_metric_key.format(key=key)
                raise ValueError(msg)
            if not isinstance(value, (int, float)):
                msg = f"Metric value for {key} must be numeric."
                raise TypeError(msg)
            if value < settings.validation.min_metric_value:
                msg = f"Metric value for {key} must be >= {settings.validation.min_metric_value}."
                raise ValueError(msg)

        return v

    @staticmethod
    def validate_alphanumeric_list(v: list[str], max_item_length: int = 50) -> list[str]:
        """Validate string lists against alphanumeric constraints to prevent injection/malformed input."""
        pattern = re.compile(r"^[a-zA-Z0-9\s\-_]+$")
        for comp in v:
            if len(comp) > max_item_length:
                msg = f"Item too long: {comp}"
                raise ValueError(msg)
            if not pattern.match(comp):
                msg = f"Invalid format: {comp}. Must be alphanumeric/safe chars only."
                raise ValueError(msg)
        return v


class StateValidator:
    """
    Validates the GlobalState transitions and requirements.
    Separated from the state model to keep logic clean and testable.
    """

    @staticmethod
    def validate_phase_requirements(state: "GlobalState") -> "GlobalState":
        from src.domain_models.enums import Phase

        settings = get_settings()

        if state.phase == Phase.VERIFICATION and state.target_persona is None:
            raise ValueError(settings.errors.missing_persona)

        if state.phase == Phase.SOLUTION and state.mvp_definition is None:
            raise ValueError(settings.errors.missing_mvp)

        return state
