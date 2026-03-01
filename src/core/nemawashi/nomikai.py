import logging
from typing import cast

from src.core.config import NemawashiConfig, get_settings
from src.core.exceptions import ValidationError
from src.domain_models.politics import InfluenceNetwork, SparseMatrixEntry

logger = logging.getLogger(__name__)


class NomikaiSimulator:
    """
    Simulates 'Nomikai' events (informal gatherings) to influence opinion dynamics.
    """

    def __init__(self, settings: NemawashiConfig | None = None) -> None:
        self.settings = settings or get_settings().nemawashi

    def run_nomikai(self, network: InfluenceNetwork, target_name: str) -> InfluenceNetwork:
        """
        Simulate a 'Nomikai' event to boost support and reduce stubbornness.
        Returns a NEW InfluenceNetwork (immutable).
        """
        # Immutable update
        new_network = network.model_copy(deep=True)

        target_idx = -1
        for i, s in enumerate(new_network.stakeholders):
            if s.name == target_name:
                target_idx = i
                break

        if target_idx == -1:
            msg = f"Target {target_name} not found."
            raise ValidationError(msg)

        # 1. Boost Support
        self._boost_support(new_network, target_idx)

        # 2. Reduce Stubbornness (Self-weight)
        self._redistribute_stubbornness(new_network, target_idx)

        return new_network

    def _boost_support(self, network: InfluenceNetwork, idx: int) -> None:
        """Increase the initial support of the stakeholder."""
        current_supp = network.stakeholders[idx].initial_support
        boost = self.settings.nomikai_boost
        new_supp = min(1.0, current_supp + (1.0 - current_supp) * boost)
        network.stakeholders[idx].initial_support = new_supp

    def _redistribute_dense(self, network: InfluenceNetwork, idx: int, reduction: float) -> None:
        matrix = cast(list[list[float]], network.matrix)
        row = matrix[idx]
        old_self = row[idx]
        new_self = max(0.0, old_self - reduction)
        diff = old_self - new_self
        n = len(row)
        if n > 1:
            add_per_person = diff / (n - 1)
            for j in range(n):
                if j == idx:
                    row[j] = new_self
                else:
                    row[j] += add_per_person

    def _redistribute_sparse(self, network: InfluenceNetwork, idx: int, reduction: float) -> None:
        entries = cast(list[SparseMatrixEntry], network.matrix)
        self_entry = next((e for e in entries if e.row == idx and e.col == idx), None)
        if self_entry:
            old_self = self_entry.val
            new_self = max(0.0, old_self - reduction)
            diff = old_self - new_self
            self_entry.val = new_self
            row_entries = [e for e in entries if e.row == idx and e.col != idx]
            if row_entries:
                add_per_person = diff / len(row_entries)
                for e in row_entries:
                    e.val += add_per_person
            else:
                self_entry.val = old_self
                logger.warning(
                    f"Cannot reduce stubbornness for {idx} in sparse mode: no other outgoing edges."
                )

    def _update_stubbornness_field(self, network: InfluenceNetwork, idx: int) -> None:
        if not network.matrix:
            return
        if isinstance(network.matrix[0], list):
            matrix = cast(list[list[float]], network.matrix)
            new_val = matrix[idx][idx]
        else:
            entries = cast(list[SparseMatrixEntry], network.matrix)
            self_entry = next((e for e in entries if e.row == idx and e.col == idx), None)
            new_val = self_entry.val if self_entry else 1.0
        network.stakeholders[idx].stubbornness = new_val

    def _redistribute_stubbornness(self, network: InfluenceNetwork, idx: int) -> None:
        """Reduce self-weight and redistribute to others."""
        reduction = self.settings.nomikai_reduction

        if not network.matrix:
            return

        if isinstance(network.matrix[0], list):
            self._redistribute_dense(network, idx, reduction)
        else:
            self._redistribute_sparse(network, idx, reduction)

        self._update_stubbornness_field(network, idx)
