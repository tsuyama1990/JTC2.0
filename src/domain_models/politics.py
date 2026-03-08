from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.core.config import get_settings


class Stakeholder(BaseModel):
    """Represents a key stakeholder in the Nemawashi process."""

    name: str = Field(
        ...,
        min_length=get_settings().validation.min_title_length,
        max_length=get_settings().validation.max_title_length,
    )
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

    stakeholders: list[Stakeholder] = Field(
        ..., min_length=get_settings().validation.min_list_length
    )
    # Use Union for matrix: can be dense (list of lists) or sparse (list of entries)
    matrix: list[list[float]] | list[SparseMatrixEntry]

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validate_all_matrix(self) -> Self:
        from src.domain_models.validators import CommonValidators

        CommonValidators.validate_matrix(self.matrix, len(self.stakeholders))
        return self
