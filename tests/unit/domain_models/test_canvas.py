import pytest
from pydantic import ValidationError

from src.domain_models.canvas import CustomerProfile, ValueMap, ValuePropositionCanvas


def test_customer_profile() -> None:
    profile = CustomerProfile(
        customer_jobs=["Organize meetings", "Set agenda", "Invite guests"],
        pains=["Too many emails", "Double bookings", "Time zones"],
        gains=["Save time", "Clear schedule", "Happy team"],
    )
    assert profile.customer_jobs == ["Organize meetings", "Set agenda", "Invite guests"]

    with pytest.raises(ValidationError):
        CustomerProfile(customer_jobs=[], pains=["Too many emails"], gains=["Save time"])


def test_value_map() -> None:
    vmap = ValueMap(
        products_and_services=["Scheduling app", "Calendar integration", "Reminder system"],
        pain_relievers=["Automated booking", "Conflict resolution", "Timezone conversion"],
        gain_creators=["1-click sync", "Analytics dashboard", "Team view"],
    )
    assert vmap.products_and_services == [
        "Scheduling app",
        "Calendar integration",
        "Reminder system",
    ]

    with pytest.raises(ValidationError):
        ValueMap(
            products_and_services=[],
            pain_relievers=["Automated booking", "Conflict resolution", "Timezone conversion"],
            gain_creators=["1-click sync", "Analytics dashboard", "Team view"],
        )


def test_value_proposition_canvas() -> None:
    profile = CustomerProfile(
        customer_jobs=["Organize meetings", "Set agenda", "Invite guests"],
        pains=["Too many emails", "Double bookings", "Time zones"],
        gains=["Save time", "Clear schedule", "Happy team"],
    )
    vmap = ValueMap(
        products_and_services=["Scheduling app", "Calendar integration", "Reminder system"],
        pain_relievers=["Automated booking", "Conflict resolution", "Timezone conversion"],
        gain_creators=["1-click sync", "Analytics dashboard", "Team view"],
    )
    vpc = ValuePropositionCanvas(
        customer_profile=profile,
        value_map=vmap,
        fit_evaluation="The scheduling app perfectly relieves the pain of too many emails.",
    )
    assert vpc.fit_evaluation.startswith("The scheduling")

    with pytest.raises(ValidationError):
        ValuePropositionCanvas(customer_profile=profile, value_map=vmap, fit_evaluation="No")
