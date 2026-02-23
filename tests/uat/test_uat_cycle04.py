from src.core.nemawashi import NemawashiEngine
from src.domain_models.politics import InfluenceNetwork, Stakeholder


def test_uat_identify_key_influencer() -> None:
    # CEO (Influential), Finance (Stubborn), Sales (Follows CEO), New Employee (Follows nobody)
    s_ceo = Stakeholder(name="CEO", initial_support=0.5, stubbornness=0.8)
    s_fin = Stakeholder(name="Finance Manager", initial_support=0.2, stubbornness=0.9)
    s_sales = Stakeholder(name="Sales Manager", initial_support=0.6, stubbornness=0.2)
    s_new = Stakeholder(name="New Employee", initial_support=1.0, stubbornness=1.0)

    # Order: CEO, Finance, Sales, New
    matrix = [
        [0.8, 0.2, 0.0, 0.0],  # CEO
        [0.1, 0.9, 0.0, 0.0],  # Finance
        [0.8, 0.0, 0.2, 0.0],  # Sales
        [0.0, 0.0, 0.0, 1.0],  # New
    ]

    net = InfluenceNetwork(stakeholders=[s_ceo, s_fin, s_sales, s_new], matrix=matrix)
    engine = NemawashiEngine()

    influencers = engine.identify_influencers(net)

    # CEO affects Sales heavily. Finance affects CEO a bit.
    # CEO is likely the key influencer or Finance due to stubbornness affecting CEO.
    assert influencers[0] in ["CEO", "Finance Manager"]


def test_uat_nomikai_effect() -> None:
    # Pre-conditions: Initial consensus is "Rejected" (< 0.5).

    # Finance hates it (0.1), CEO follows Finance
    s_ceo = Stakeholder(name="CEO", initial_support=0.5, stubbornness=0.5)
    s_fin = Stakeholder(name="Finance Manager", initial_support=0.1, stubbornness=1.0)
    s_new = Stakeholder(name="New Employee", initial_support=1.0, stubbornness=1.0)

    # Order: CEO, Finance, New
    matrix = [
        [0.5, 0.5, 0.0],  # CEO
        [0.0, 1.0, 0.0],  # Finance (Stubborn, ignores everyone)
        [0.0, 0.0, 1.0],  # New
    ]

    net = InfluenceNetwork(stakeholders=[s_ceo, s_fin, s_new], matrix=matrix)
    engine = NemawashiEngine()

    # Check initial consensus
    initial_res = engine.calculate_consensus(net)
    assert initial_res["Finance Manager"] == 0.1

    # Execute run_nomikai_simulation(target="Finance Manager")
    # This increases weight of New Employee on Finance Manager
    updated_net = engine.run_nomikai(
        net, target_name="Finance Manager", influencer_name="New Employee"
    )

    # Re-run DeGroot
    final_res = engine.calculate_consensus(updated_net)

    # Finance Manager's support should increase
    assert final_res["Finance Manager"] > 0.1
