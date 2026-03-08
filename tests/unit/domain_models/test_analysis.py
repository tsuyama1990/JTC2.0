import pytest
from pydantic import ValidationError

from src.domain_models.analysis import AlternativeAnalysis, AlternativeTool


def test_alternative_tool_valid() -> None:
    tool = AlternativeTool(
        name="Excel",
        financial_cost="$10/month",
        time_cost="2 hours a day",
        ux_friction="Very high friction due to manual data entry",
    )
    assert tool.name == "Excel"


def test_alternative_tool_invalid() -> None:
    with pytest.raises(ValidationError):
        AlternativeTool(
            name="",  # invalid, min_length=1
            financial_cost="$10/month",
            time_cost="2 hours a day",
            ux_friction="Very high friction",
        )


def test_alternative_analysis_valid() -> None:
    tool = AlternativeTool(
        name="Excel",
        financial_cost="$10/month",
        time_cost="2 hours a day",
        ux_friction="Very high friction",
    )
    analysis = AlternativeAnalysis(
        current_alternatives=[tool],
        switching_cost="High switching cost since all employees use Excel currently.",
        ten_x_value="Automates data entry, reducing a 2 hour task to 2 minutes.",
    )
    assert analysis.ten_x_value.startswith("Automates")


def test_alternative_analysis_invalid() -> None:
    with pytest.raises(ValidationError):
        AlternativeAnalysis(
            current_alternatives=[],  # invalid length
            switching_cost="High cost",
            ten_x_value="10x Value",
        )
