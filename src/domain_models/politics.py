from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class MatrixShapeError(ValueError):
    """Raised when the matrix shape is invalid."""


class MatrixStochasticityError(ValueError):
    """Raised when the matrix rows do not sum to 1.0."""


class MatrixValuesError(ValueError):
    """Raised when matrix values are out of bounds."""


class StakeholderMismatchError(ValueError):
    """Raised when the matrix dimensions do not match the number of stakeholders."""


class Stakeholder(BaseModel):
    """
    Represents a key stakeholder in the Nemawashi process.
    Contains their name, initial support, and stubbornness for the DeGroot model.
    """

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


class DenseInfluenceNetwork(BaseModel):
    """Represents the influence graph between stakeholders using a dense matrix."""

    stakeholders: list[Stakeholder] = Field(..., min_length=1)
    matrix: list[list[float]]

    model_config = ConfigDict(extra="forbid")

    @field_validator("matrix")
    @classmethod
    def validate_matrix_values(cls, v: list[list[float]]) -> list[list[float]]:
        """Ensure all values are between 0 and 1."""
        for row in v:
            for val in row:
                if not (0.0 <= val <= 1.0):
                    msg = f"Matrix value {val} is out of bounds [0.0, 1.0]."
                    raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_dimensions(self) -> Self:
        """Ensure matrix is square and matches stakeholder count."""
        n = len(self.stakeholders)

        if len(self.matrix) != n:
            msg = "Matrix row count must match stakeholder count"
            raise StakeholderMismatchError(msg)

        for row in self.matrix:
            if len(row) != n:
                msg = "Matrix must be square"
                raise MatrixShapeError(msg)

        return self

    @model_validator(mode="after")
    def validate_stochasticity(self) -> Self:
        """Ensure rows sum to 1.0 (approximately)."""
        TOLERANCE = 1e-6

        for row in self.matrix:
            row_sum = sum(row)
            if not (1.0 - TOLERANCE <= row_sum <= 1.0 + TOLERANCE):
                msg = "Influence matrix rows must sum to 1.0"
                raise MatrixStochasticityError(msg)

        return self


class SparseInfluenceNetwork(BaseModel):
    """Represents the influence graph between stakeholders using a sparse matrix."""

    stakeholders: list[Stakeholder] = Field(..., min_length=1)
    matrix: list[SparseMatrixEntry]

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_dimensions(self) -> Self:
        """Ensure matrix dimensions match stakeholder count."""
        n = len(self.stakeholders)

        for entry in self.matrix:
            if not (0 <= entry.row < n) or not (0 <= entry.col < n):
                msg = "Sparse entry indices must be within stakeholder count"
                raise MatrixShapeError(msg)

        return self

    @model_validator(mode="after")
    def validate_stochasticity(self) -> Self:
        """Ensure rows sum to 1.0 (approximately)."""
        n = len(self.stakeholders)
        TOLERANCE = 1e-6

        row_sums = [0.0] * n
        for entry in self.matrix:
            row_sums[entry.row] += entry.val

        for s in row_sums:
            if not (1.0 - TOLERANCE <= s <= 1.0 + TOLERANCE):
                msg = "Influence matrix rows must sum to 1.0"
                raise MatrixStochasticityError(msg)

        return self


InfluenceNetwork = DenseInfluenceNetwork | SparseInfluenceNetwork
