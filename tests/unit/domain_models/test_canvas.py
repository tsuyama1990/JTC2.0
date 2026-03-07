import pytest
from pydantic import ValidationError

from src.domain_models.canvas import CustomerProfile, ValueMap, ValuePropositionCanvas


def test_customer_profile() -> None:
    profile = CustomerProfile(
        customer_jobs=["Organize meetings"], pains=["Too many emails"], gains=["Save time"]
    )
    assert profile.customer_jobs == ["Organize meetings"]

    with pytest.raises(ValidationError):
        CustomerProfile(customer_jobs=[], pains=["Too many emails"], gains=["Save time"])


def test_value_map() -> None:
    vmap = ValueMap(
        products_and_services=["Scheduling app"],
        pain_relievers=["Automated booking"],
        gain_creators=["1-click sync"],
    )
    assert vmap.products_and_services == ["Scheduling app"]

    with pytest.raises(ValidationError):
        ValueMap(
            products_and_services=[],
            pain_relievers=["Automated booking"],
            gain_creators=["1-click sync"],
        )


def test_value_proposition_canvas() -> None:
    profile = CustomerProfile(
        customer_jobs=["Organize meetings"], pains=["Too many emails"], gains=["Save time"]
    )
    vmap = ValueMap(
        products_and_services=["Scheduling app"],
        pain_relievers=["Automated booking"],
        gain_creators=["1-click sync"],
    )
    vpc = ValuePropositionCanvas(
        customer_profile=profile,
        value_map=vmap,
        fit_evaluation="The scheduling app perfectly relieves the pain of too many emails.",
    )
    assert vpc.fit_evaluation.startswith("The scheduling")

    with pytest.raises(ValidationError):
        ValuePropositionCanvas(customer_profile=profile, value_map=vmap, fit_evaluation="No")
