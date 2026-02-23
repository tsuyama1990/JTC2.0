from src.domain_models.politics import InfluenceNetwork, Stakeholder
from src.ui.nemawashi_view import NemawashiView


def test_nemawashi_view() -> None:
    s1 = Stakeholder(name="A", initial_support=0.5, stubbornness=0.5)
    s2 = Stakeholder(name="B", initial_support=0.5, stubbornness=0.5)
    matrix = [[0.5, 0.5], [0.5, 0.5]]
    net = InfluenceNetwork(stakeholders=[s1, s2], matrix=matrix)

    view = NemawashiView.render_network(net)
    assert "Nemawashi Map:" in view
    assert "From -> To" in view
    # Check simple presence
    assert "A" in view
    assert "B" in view


def test_nemawashi_view_empty() -> None:
    net = InfluenceNetwork(stakeholders=[], matrix=[])
    view = NemawashiView.render_network(net)
    assert view == "No stakeholders."
