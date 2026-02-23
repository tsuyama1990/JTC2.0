import time

from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.simulation import DialogueMessage, Role
from src.domain_models.state import GlobalState


def test_uat_simulation_debate_flow() -> None:
    """
    UAT-C02-01: Verify debate flow structure.
    Simulate the sequence of a debate and verify state updates.
    """
    # 1. Setup
    idea = LeanCanvas(
        id=0,
        title="Test Idea",
        problem="Problem statement must be three words.",
        solution="Solution statement must be three words.",
        customer_segments="Customers segment description.",
        unique_value_prop="Unique value proposition description.",
    )
    state = GlobalState(
        topic="Test Topic",
        selected_idea=idea,
        simulation_active=True
    )

    # 2. Simulate New Employee Pitch
    pitch_msg = DialogueMessage(
        role=Role.NEW_EMPLOYEE,
        content="Here is my idea...",
        timestamp=time.time()
    )
    state.debate_history.append(pitch_msg)

    assert len(state.debate_history) == 1
    msg1: DialogueMessage = state.debate_history[-1]
    assert msg1.role == Role.NEW_EMPLOYEE

    # 3. Simulate Finance Critique
    finance_msg = DialogueMessage(
        role=Role.FINANCE,
        content="Too expensive!",
        timestamp=time.time()
    )
    state.debate_history.append(finance_msg)

    assert len(state.debate_history) == 2
    msg2: DialogueMessage = state.debate_history[-1]
    assert msg2.role == Role.FINANCE

    # 4. Simulate Defense
    defense_msg = DialogueMessage(
        role=Role.NEW_EMPLOYEE,
        content="But it's worth it!",
        timestamp=time.time()
    )
    state.debate_history.append(defense_msg)

    assert len(state.debate_history) == 3
    msg3: DialogueMessage = state.debate_history[-1]
    assert msg3.role == Role.NEW_EMPLOYEE
