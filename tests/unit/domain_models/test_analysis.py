import pytest
from pydantic import ValidationError

from src.domain_models.analysis import AlternativeAnalysis, AlternativeTool


def test_alternative_tool() -> None:
    tool = AlternativeTool(name="Excel", financial_cost="Low", time_cost="High", ux_friction="High")
    assert tool.name == "Excel"

    with pytest.raises(ValidationError):
        AlternativeTool(name="A", financial_cost="Low", time_cost="High", ux_friction="High")


def test_alternative_analysis() -> None:
    tool1 = AlternativeTool(
        name="Excel", financial_cost="Low", time_cost="High", ux_friction="High"
    )
    tool2 = AlternativeTool(
        name="Notion", financial_cost="Medium", time_cost="Medium", ux_friction="Medium"
    )
    tool3 = AlternativeTool(
        name="Airtable", financial_cost="High", time_cost="Low", ux_friction="Low"
    )
    analysis = AlternativeAnalysis(
        current_alternatives=[tool1, tool2, tool3],
        switching_cost="Learning curve",
        ten_x_value="Automated insights and collaboration",
    )
    assert analysis.switching_cost == "Learning curve"

    with pytest.raises(ValidationError):
        AlternativeAnalysis(
            current_alternatives=[],
            switching_cost="Learning curve",
            ten_x_value="Automated insights",
        )
