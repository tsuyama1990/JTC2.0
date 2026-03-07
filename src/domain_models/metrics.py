"""
Defines the Metrics domain models.

These models encapsulate the Key Performance Indicators (KPIs) used to evaluate
the success of the startup idea, including AARRR (Pirate Metrics) and
detailed simulation scores (Planning, Communication, etc.).
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.core.config import get_settings
from src.core.constants import DESC_METRICS_AARRR, DESC_METRICS_CUSTOM


class AARRR(BaseModel):
    """
    Pirate Metrics: Acquisition, Activation, Retention, Revenue, Referral.
    """

    model_config = ConfigDict(extra="forbid")

    acquisition: float = Field(
        0.0,
        ge=get_settings().validation.min_metric_value,
        description="Acquisition metric",
    )
    activation: float = Field(
        0.0,
        ge=get_settings().validation.min_metric_value,
        description="Activation metric",
    )
    retention: float = Field(
        0.0,
        ge=get_settings().validation.min_metric_value,
        le=get_settings().validation.max_percentage_value,
        description="Retention percentage",
    )
    revenue: float = Field(
        0.0,
        ge=get_settings().validation.min_metric_value,
        description="Revenue metric",
    )
    referral: float = Field(
        0.0,
        ge=get_settings().validation.min_metric_value,
        description="Referral metric",
    )


class DetailedMetrics(BaseModel):
    """
    Detailed metrics for the simulation phase.

    Tracks the quality of the agent interactions and the startup plan.
    """

    model_config = ConfigDict(extra="forbid")

    planning_score: float = Field(0.0, description="Score for planning quality")
    communication_score: float = Field(0.0, description="Score for communication effectiveness")
    tool_selection_quality: float = Field(0.0, description="Score for appropriate tool usage")
    action_completion: float = Field(0.0, description="Score for action completion rate")
    cognitive_load: float = Field(0.0, description="Score for cognitive load management")


class Financials(BaseModel):
    """
    Financial projections and viability metrics.
    """

    model_config = ConfigDict(extra="forbid")

    cac: float = Field(0.0, description="Customer Acquisition Cost")
    ltv: float = Field(0.0, description="Lifetime Value")
    payback_months: float = Field(0.0, description="Months to recover CAC")
    roi: float = Field(0.0, description="Return on Investment (LTV/CAC ratio)")

    def run_sensitivity_analysis(
        self, cac_variance: float = 0.2, ltv_variance: float = 0.2
    ) -> dict[str, float]:
        """Runs basic sensitivity analysis returning optimistic and pessimistic ROIs."""
        opt_cac = max(0.01, self.cac * (1 - cac_variance))
        pes_cac = self.cac * (1 + cac_variance)
        opt_ltv = self.ltv * (1 + ltv_variance)
        pes_ltv = self.ltv * (1 - ltv_variance)

        return {
            "optimistic_roi": opt_ltv / opt_cac,
            "pessimistic_roi": pes_ltv / pes_cac,
        }


class FinancialEstimates(BaseModel):
    """
    Structured response for LLM financial estimation.
    """

    model_config = ConfigDict(extra="forbid")

    cac: float = Field(..., gt=0.0, description="Estimated CAC")
    arpu: float = Field(..., gt=0.0, description="Estimated ARPU")
    churn_rate: float = Field(..., ge=0.0, le=1.0, description="Estimated monthly churn rate")


class Metrics(BaseModel):
    """
    Aggregates all metrics (AARRR, Detailed, Custom, and Financials).
    """

    model_config = ConfigDict(extra="forbid")

    aarrr: AARRR = Field(default_factory=AARRR, description=DESC_METRICS_AARRR)
    detailed: DetailedMetrics = Field(
        default_factory=DetailedMetrics, description="Detailed simulation metrics"
    )
    financials: Financials = Field(default_factory=Financials, description="Financial projections")
    custom_metrics: dict[str, float] = Field(default_factory=dict, description=DESC_METRICS_CUSTOM)

    @field_validator("custom_metrics")
    @classmethod
    def validate_custom_metrics(cls, v: dict[str, Any]) -> dict[str, float]:
        """Validate custom metrics keys, values, and limit."""
        from src.domain_models.validators import CommonValidators

        return CommonValidators.validate_metrics_dict(v)


class RingiSho(BaseModel):
    """
    Formal approval document (Ringi-sho).
    """

    model_config = ConfigDict(extra="forbid")

    title: str = Field(
        ...,
        min_length=get_settings().validation.min_title_length,
        description="Title of the proposal",
    )
    executive_summary: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="Executive summary",
    )
    financial_projection: Financials = Field(..., description="Financial projections")
    risks: list[str] = Field(
        default_factory=list,
        min_length=get_settings().validation.min_list_length,
        description="List of identified risks",
    )
    approval_status: str = Field(
        "Draft", pattern="^(Draft|Approved|Rejected)$", description="Approval status"
    )

    def generate_document_preview(self) -> str:
        """Generate a text-based preview of the Ringi-Sho document."""
        return (
            f"=== {self.title} ===\n"
            f"Status: {self.approval_status}\n\n"
            f"Summary:\n{self.executive_summary}\n\n"
            f"Financials:\n"
            f"- CAC: ${self.financial_projection.cac:.2f}\n"
            f"- LTV: ${self.financial_projection.ltv:.2f}\n"
            f"- ROI: {self.financial_projection.roi:.2f}x\n"
        )
