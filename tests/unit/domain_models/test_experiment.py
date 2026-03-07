import pytest
from pydantic import ValidationError

from src.domain_models.experiment import ExperimentPlan, MetricTarget


def test_metric_target() -> None:
    target = MetricTarget(
        metric_name="Signup Rate", target_value=0.1, measurement_method="Google Analytics"
    )
    assert target.metric_name == "Signup Rate"

    with pytest.raises(ValidationError):
        MetricTarget(metric_name="S", target_value=0.1, measurement_method="GA")


def test_experiment_plan() -> None:
    target1 = MetricTarget(
        metric_name="Signup Rate", target_value=0.1, measurement_method="Google Analytics"
    )
    target2 = MetricTarget(metric_name="Retention", target_value=0.5, measurement_method="Mixpanel")
    target3 = MetricTarget(
        metric_name="Referral", target_value=1.5, measurement_method="Viral loops"
    )
    plan = ExperimentPlan(
        riskiest_assumption="Users will pay for this",
        experiment_type="A/B Test",
        acquisition_channel="Facebook Ads",
        aarrr_metrics=[target1, target2, target3],
        pivot_conditions="If signup rate is less than 5%",
    )
    assert plan.experiment_type == "A/B Test"

    with pytest.raises(ValidationError):
        ExperimentPlan(
            riskiest_assumption="Too short",
            experiment_type="A/B",
            acquisition_channel="FB",
            aarrr_metrics=[],
            pivot_conditions="None",
        )
