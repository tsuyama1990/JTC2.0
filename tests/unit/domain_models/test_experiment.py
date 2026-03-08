import pytest
from pydantic import ValidationError

from src.domain_models.experiment import ExperimentPlan, MetricTarget


def test_metric_target_valid() -> None:
    metric = MetricTarget(
        metric_name="Conversion Rate",
        target_value=0.15,
        measurement_method="Google Analytics goal tracking",
    )
    assert metric.metric_name == "Conversion Rate"


def test_metric_target_invalid() -> None:
    with pytest.raises(ValidationError):
        MetricTarget(
            metric_name="",  # min_length=1
            target_value=0.15,
            measurement_method="Short",  # min_length=10
        )


def test_experiment_plan_valid() -> None:
    metrics = [
        MetricTarget(
            metric_name="Aquisition",
            target_value=1000,
            measurement_method="Unique visitors tracking via plausible",
        ),
        MetricTarget(
            metric_name="Activation",
            target_value=0.1,
            measurement_method="Sign ups via plausible conversions",
        ),
        MetricTarget(
            metric_name="Retention",
            target_value=0.2,
            measurement_method="Return visitors to dashboard",
        ),
        MetricTarget(
            metric_name="Revenue",
            target_value=10,
            measurement_method="Upgrades to paid plan",
        ),
        MetricTarget(
            metric_name="Referral",
            target_value=0.05,
            measurement_method="Invite link usage",
        ),
    ]
    plan = ExperimentPlan(
        riskiest_assumption="Users will trust AI to categorize their confidential data",
        experiment_type="Landing Page Smoke Test",
        acquisition_channel="LinkedIn Ads",
        aarrr_metrics=metrics,
        pivot_condition="If conversion rate is below 5%, pivot to a less sensitive data domain.",
    )
    assert plan.experiment_type == "Landing Page Smoke Test"


def test_experiment_plan_invalid() -> None:
    with pytest.raises(ValidationError):
        ExperimentPlan(
            riskiest_assumption="Users will trust AI to categorize their confidential data",
            experiment_type="Landing Page Smoke Test",
            acquisition_channel="LinkedIn Ads",
            aarrr_metrics=[],  # must be 5 items
            pivot_condition="If conversion rate is below 5%, pivot to a less sensitive data domain.",
        )
