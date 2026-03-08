import pytest
from pydantic import ValidationError

from src.domain_models.vpc import CustomerProfile, ValueMap, ValuePropositionCanvas


def test_customer_profile_valid() -> None:
    profile = CustomerProfile(
        customer_jobs=["Organize data"],
        pains=["Manual data entry takes too long"],
        gains=["Save time", "Reduce errors"],
    )
    assert "Organize data" in profile.customer_jobs


def test_customer_profile_invalid() -> None:
    with pytest.raises(ValidationError):
        CustomerProfile(
            customer_jobs=[],  # invalid length
            pains=["Manual data entry takes too long"],
            gains=["Save time", "Reduce errors"],
        )


def test_value_map_valid() -> None:
    vmap = ValueMap(
        products_and_services=["Data Automation SaaS"],
        pain_relievers=["Automates data entry"],
        gain_creators=["Saves 2 hours a day"],
    )
    assert "Data Automation SaaS" in vmap.products_and_services


def test_value_proposition_canvas_valid() -> None:
    profile = CustomerProfile(
        customer_jobs=["Organize data"],
        pains=["Manual data entry takes too long"],
        gains=["Save time"],
    )
    vmap = ValueMap(
        products_and_services=["Data Automation SaaS"],
        pain_relievers=["Automates data entry"],
        gain_creators=["Saves 2 hours a day"],
    )
    vpc = ValuePropositionCanvas(
        profile=profile,
        map=vmap,
        fit_evaluation="The automation SaaS directly addresses the manual data entry pain.",
    )
    assert vpc.fit_evaluation.startswith("The automation SaaS")


def test_vpc_invalid() -> None:
    with pytest.raises(ValidationError):
        ValuePropositionCanvas(
            profile=None,
            map=None,
            fit_evaluation="Short",  # too short
        )
