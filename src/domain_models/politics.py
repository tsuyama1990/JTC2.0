from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.core.constants import (
    ERR_MATRIX_SHAPE,
    ERR_MATRIX_VALUES,
    ERR_STAKEHOLDER_MISMATCH,
)


class Stakeholder(BaseModel):
    """Represents a key stakeholder in the Nemawashi process."""

    name: str = Field(..., min_length=1, max_length=100)
    initial_support: float = Field(..., ge=0.0, le=1.0)
    stubbornness: float = Field(..., ge=0.0, le=1.0)

    model_config = ConfigDict(extra="forbid")


class InfluenceNetwork(BaseModel):
    """Represents the influence graph between stakeholders."""

    stakeholders: list[Stakeholder]
    matrix: list[list[float]]  # Adjacency matrix (stochastic)

    model_config = ConfigDict(extra="forbid")

    @field_validator("matrix")
    @classmethod
    def validate_matrix_values(cls, v: list[list[float]]) -> list[list[float]]:
        """Ensure all values are between 0 and 1."""
        for row in v:
            for val in row:
                if not (0.0 <= val <= 1.0):
                    raise ValueError(ERR_MATRIX_VALUES)
        return v

    @model_validator(mode="after")
    def validate_dimensions(self) -> Self:
        """Ensure matrix is square and matches stakeholder count."""
        n = len(self.stakeholders)
        if len(self.matrix) != n:
            raise ValueError(ERR_STAKEHOLDER_MISMATCH)

        for row in self.matrix:
            if len(row) != n:
                raise ValueError(ERR_MATRIX_SHAPE)
        return self
