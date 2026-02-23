from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.core.constants import (
    ERR_MATRIX_SHAPE,
    ERR_MATRIX_STOCHASTICITY,
    ERR_MATRIX_VALUES,
    ERR_STAKEHOLDER_MISMATCH,
)


class Stakeholder(BaseModel):
    """Represents a key stakeholder in the Nemawashi process."""

    name: str = Field(..., min_length=1, max_length=100)
    initial_support: float = Field(..., ge=0.0, le=1.0)
    stubbornness: float = Field(..., ge=0.0, le=1.0)

    model_config = ConfigDict(extra="forbid")


class SparseMatrixEntry(BaseModel):
    """Represents a non-zero entry in a sparse influence matrix."""
    row: int
    col: int
    val: float = Field(..., ge=0.0, le=1.0)

    model_config = ConfigDict(extra="forbid")


class InfluenceNetwork(BaseModel):
    """Represents the influence graph between stakeholders."""

    stakeholders: list[Stakeholder] = Field(..., min_length=1)
    # Use Union for matrix: can be dense (list of lists) or sparse (list of entries)
    matrix: list[list[float]] | list[SparseMatrixEntry]

    model_config = ConfigDict(extra="forbid")

    @field_validator("matrix")
    @classmethod
    def validate_matrix_values(cls, v: list[list[float]] | list[SparseMatrixEntry]) -> list[list[float]] | list[SparseMatrixEntry]:
        """Ensure all values are between 0 and 1."""
        if isinstance(v, list) and v and isinstance(v[0], list):
            # Dense matrix
            for row in v:  # type: ignore
                for val in row:
                    if not (0.0 <= val <= 1.0):
                        raise ValueError(ERR_MATRIX_VALUES)
        # Sparse matrix validation handled by SparseMatrixEntry validators (ge=0.0, le=1.0)
        return v

    @model_validator(mode="after")
    def validate_dimensions(self) -> Self:
        """Ensure matrix is square and matches stakeholder count."""
        n = len(self.stakeholders)

        if isinstance(self.matrix, list) and self.matrix and isinstance(self.matrix[0], list):
            # Dense matrix check
            if len(self.matrix) != n:
                raise ValueError(ERR_STAKEHOLDER_MISMATCH)

            for row in self.matrix:  # type: ignore
                if len(row) != n:
                    raise ValueError(ERR_MATRIX_SHAPE)
        elif isinstance(self.matrix, list):
             # Sparse matrix check
             # Check that row/col indices are within [0, n-1]
             for entry in self.matrix:  # type: ignore
                 if not isinstance(entry, SparseMatrixEntry):
                     continue # Should be caught by type check, but safe guard
                 if not (0 <= entry.row < n) or not (0 <= entry.col < n):
                     raise ValueError(ERR_MATRIX_SHAPE)

        return self

    @model_validator(mode="after")
    def validate_stochasticity(self) -> Self:
        """Ensure rows sum to 1.0 (approximately)."""
        n = len(self.stakeholders)

        # Use tighter tolerance for strict data integrity
        TOLERANCE = 1e-6

        if isinstance(self.matrix, list) and self.matrix and isinstance(self.matrix[0], list):
            # Dense matrix
            for row in self.matrix:  # type: ignore
                row_sum = sum(row)
                if not (1.0 - TOLERANCE <= row_sum <= 1.0 + TOLERANCE):
                    raise ValueError(ERR_MATRIX_STOCHASTICITY)
        else:
            # Sparse matrix
            # Initialize row sums
            row_sums = [0.0] * n
            for entry in self.matrix:  # type: ignore
                if isinstance(entry, SparseMatrixEntry):
                    row_sums[entry.row] += entry.val

            for s in row_sums:
                if not (1.0 - TOLERANCE <= s <= 1.0 + TOLERANCE):
                    raise ValueError(ERR_MATRIX_STOCHASTICITY)

        return self
