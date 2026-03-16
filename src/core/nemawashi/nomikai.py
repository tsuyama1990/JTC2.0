import logging

from src.core.config import NemawashiConfig, get_settings
from src.core.exceptions import ValidationError
from src.domain_models.politics import (
    DenseInfluenceNetwork,
    InfluenceNetwork,
    SparseInfluenceNetwork,
)

logger = logging.getLogger(__name__)


class SimulationService:
    """
    Simulates 'Nomikai' events (informal gatherings) to influence opinion dynamics.
    """

    def __init__(self, settings: NemawashiConfig | None = None) -> None:
        self.settings = settings or get_settings().nemawashi

    def run_nomikai(self, network: InfluenceNetwork, target_name: str) -> InfluenceNetwork:  # noqa: C901, PLR0912, PLR0915
        """
        Simulate a 'Nomikai' event to boost support and reduce stubbornness.
        Returns a NEW InfluenceNetwork (immutable).
        """
        if not target_name or not isinstance(target_name, str):
            msg = "Target name must be a non-empty string."
            raise ValidationError(msg)

        if len(network.stakeholders) > 10000:
            msg = f"Network size {len(network.stakeholders)} exceeds limit of 10,000 stakeholders."
            raise ValidationError(msg)

        target_idx = -1
        for i, s in enumerate(network.stakeholders):
            if s.name == target_name:
                target_idx = i
                break

        if target_idx == -1:
            msg = f"Target {target_name} not found."
            raise ValidationError(msg)

        # 1. Boost Support (compute new values without mutating)
        current_supp = network.stakeholders[target_idx].initial_support
        boost = self.settings.nomikai_boost
        new_supp = min(1.0, current_supp + (1.0 - current_supp) * boost)

        new_stakeholders = [s.model_copy() for s in network.stakeholders]
        new_stakeholders[target_idx].initial_support = new_supp

        # 2. Reduce Stubbornness (Self-weight) and redistribute
        reduction = self.settings.nomikai_reduction

        if isinstance(network, DenseInfluenceNetwork):
            new_matrix_dense = [row[:] for row in network.matrix]
            row = new_matrix_dense[target_idx]
            old_self = row[target_idx]

            if reduction > old_self:
                msg = f"Reduction {reduction} exceeds current self-weight {old_self}"
                raise ValidationError(msg)

            new_self = max(0.0, old_self - reduction)
            diff = old_self - new_self
            n = len(row)
            if n > 1:
                add_per_person = diff / (n - 1)
                for j in range(n):
                    if j == target_idx:
                        row[j] = new_self
                    else:
                        val = row[j] + add_per_person
                        row[j] = min(1.0, max(0.0, val))

            new_stakeholders[target_idx].stubbornness = new_matrix_dense[target_idx][target_idx]
            return DenseInfluenceNetwork(stakeholders=new_stakeholders, matrix=new_matrix_dense)

        new_matrix_sparse = [e.model_copy() for e in network.matrix]
        self_entry = next(
            (e for e in new_matrix_sparse if e.row == target_idx and e.col == target_idx), None
        )

        if self_entry:
            old_self = self_entry.val
            if reduction > old_self:
                msg = f"Reduction {reduction} exceeds current self-weight {old_self}"
                raise ValidationError(msg)

            new_self = max(0.0, old_self - reduction)
            diff = old_self - new_self
            self_entry.val = new_self

            row_entries = [
                e for e in new_matrix_sparse if e.row == target_idx and e.col != target_idx
            ]
            if row_entries:
                add_per_person = diff / len(row_entries)
                for e in row_entries:
                    val = e.val + add_per_person
                    e.val = min(1.0, max(0.0, val))
            else:
                self_entry.val = old_self
                logger.warning(
                    f"Cannot reduce stubbornness for {target_idx} in sparse mode: no other outgoing edges."
                )
            new_stakeholders[target_idx].stubbornness = self_entry.val
        else:
            new_stakeholders[target_idx].stubbornness = 1.0

        return SparseInfluenceNetwork(stakeholders=new_stakeholders, matrix=new_matrix_sparse)
