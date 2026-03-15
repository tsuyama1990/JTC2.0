import os
import sys
from pathlib import Path

# Add project root to sys.path so 'src' module can be found
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import dummy env vars to avoid pydantic validation errors
from tests.conftest import DUMMY_ENV_VARS

os.environ.update(DUMMY_ENV_VARS)

import marimo

__generated_with = "0.20.4"
app = marimo.App()


@app.cell
def __():
    import marimo as mo
    import numpy as np

    from src.core.nemawashi.engine import NemawashiEngine
    from src.domain_models.politics import InfluenceNetwork, Stakeholder

    mo.md("# JTC 2.0 - Cycle 04 UAT: Nemawashi (Consensus Building)")
    return mo, InfluenceNetwork, Stakeholder, NemawashiEngine, np


@app.cell
def __(Stakeholder, InfluenceNetwork, NemawashiEngine, mo):
    mo.md("## Scenario 1: Identify Key Influencer")

    s1 = Stakeholder(name="Finance Manager", initial_support=0.2, stubbornness=0.9)
    s2 = Stakeholder(name="Sales Manager", initial_support=0.8, stubbornness=0.5)
    s3 = Stakeholder(name="CEO", initial_support=0.5, stubbornness=0.2)
    matrix = [[0.9, 0.0, 0.1], [0.5, 0.5, 0.0], [0.8, 0.0, 0.2]]
    net = InfluenceNetwork(stakeholders=[s1, s2, s3], matrix=matrix)

    engine = NemawashiEngine()
    influencers = engine.identify_influencers(net)

    assert influencers[0] == "Finance Manager", f"Expected Finance Manager, got {influencers[0]}"
    mo.md(f"**Success!** Key influencer identified as: {influencers[0]}")
    return s1, s2, s3, matrix, net, engine, influencers


@app.cell
def __(net, engine, mo):
    mo.md("## Scenario 2: The 'Nomikai' Effect")

    initial_ops = engine.calculate_consensus(net)
    initial_avg = sum(initial_ops) / len(initial_ops)

    new_net = engine.run_nomikai(net, "Finance Manager")
    final_ops = engine.calculate_consensus(new_net)
    final_avg = sum(final_ops) / len(final_ops)

    assert new_net.stakeholders[0].initial_support > 0.2, "Finance Manager support did not increase"
    assert final_avg > initial_avg, "Overall consensus did not improve"

    mo.md(
        f"**Success!** Nomikai effect verified.\nInitial consensus: {initial_avg:.2f} -> Final consensus: {final_avg:.2f}"
    )
    return initial_ops, initial_avg, new_net, final_ops, final_avg


@app.cell
def __(Stakeholder, InfluenceNetwork, engine, np, mo):
    mo.md("## Scenario 3: Opinions converge over time")

    a1 = Stakeholder(name="Agent 1", initial_support=0.1, stubbornness=0.5)
    a2 = Stakeholder(name="Agent 2", initial_support=0.5, stubbornness=0.5)
    a3 = Stakeholder(name="Agent 3", initial_support=0.9, stubbornness=0.5)

    # Everyone equally influences everyone
    mat = [[0.5, 0.25, 0.25], [0.25, 0.5, 0.25], [0.25, 0.25, 0.5]]
    converge_net = InfluenceNetwork(stakeholders=[a1, a2, a3], matrix=mat)

    initial_variance = np.var([0.1, 0.5, 0.9])

    final_ops_conv = engine.calculate_consensus(converge_net)
    final_variance = np.var(final_ops_conv)

    assert final_variance < initial_variance, "Variance did not decrease"

    mo.md(
        f"**Success!** Opinions converged. Variance went from {initial_variance:.4f} to {final_variance:.4f}"
    )
    return a1, a2, a3, mat, converge_net, initial_variance, final_ops_conv, final_variance


@app.cell
def __(Stakeholder, InfluenceNetwork, engine, mo):
    mo.md("## Scenario 4: Stubborn agents resist change")

    f1 = Stakeholder(name="Finance Manager", initial_support=0.1, stubbornness=0.9)
    s_m = Stakeholder(name="Sales Manager", initial_support=0.9, stubbornness=0.5)

    # Finance listens 90% to self, 10% to Sales
    # Sales listens 50% to self, 50% to Finance
    mat_stub = [[0.9, 0.1], [0.5, 0.5]]
    stubborn_net = InfluenceNetwork(stakeholders=[f1, s_m], matrix=mat_stub)

    from src.core.nemawashi.utils import NemawashiUtils

    matrix_op = NemawashiUtils.build_sparse_matrix(stubborn_net, 2)
    current_ops = [f1.initial_support, s_m.initial_support]

    # Run 1 step
    next_ops = matrix_op.dot(current_ops)
    change = abs(next_ops[0] - current_ops[0])

    assert change <= 0.1, f"Change was too high: {change}"

    mo.md(f"**Success!** Stubborn agent resisted change. Change per step: {change:.4f}")
    return f1, s_m, mat_stub, stubborn_net, matrix_op, current_ops, next_ops, change


if __name__ == "__main__":
    app.run()
