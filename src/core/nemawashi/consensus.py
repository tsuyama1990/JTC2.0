import logging
from typing import cast

import numpy as np
from scipy.sparse import coo_matrix, csr_matrix, spmatrix

from src.core.config import NemawashiConfig, get_settings
from src.core.exceptions import ValidationError
from src.domain_models.politics import InfluenceNetwork, SparseMatrixEntry

logger = logging.getLogger(__name__)


class ConsensusEngine:
    """
    Handles the core mathematical consensus building (French-DeGroot Model).
    """

    def __init__(self, settings: NemawashiConfig | None = None) -> None:
        """
        Initialize the Consensus Engine.

        Args:
            settings: Configuration settings for Nemawashi. If None, loads from global settings.
        """
        self.settings = settings or get_settings().nemawashi

    def _build_sparse_matrix(self, network: InfluenceNetwork, n: int) -> csr_matrix:
        """
        Construct a CSR matrix from the network data efficiently.
        Uses generators to avoid large intermediate lists.

        Args:
            network: The influence network domain model.
            n: Number of stakeholders (dimension).

        Returns:
            A sparse CSR matrix representing the influence graph.

        Raises:
            ValidationError: If matrix construction fails.
        """
        if not network.matrix:
            return csr_matrix((n, n), dtype=float)

        # Check if input is dense (list of lists)
        if isinstance(network.matrix[0], list):
            try:
                # Convert dense to sparse immediately
                return csr_matrix(network.matrix, shape=(n, n), dtype=float)
            except Exception as e:
                msg = f"Failed to convert dense matrix: {e}"
                raise ValidationError(msg) from e

        # Sparse input (list of SparseMatrixEntry)
        entries = cast(list[SparseMatrixEntry], network.matrix)
        count = len(entries)

        try:
            # Create generators
            rows_gen = (e.row for e in entries)
            cols_gen = (e.col for e in entries)
            data_gen = (e.val for e in entries)

            # Efficiently create numpy arrays from generators
            rows = np.fromiter(rows_gen, dtype=int, count=count)
            cols = np.fromiter(cols_gen, dtype=int, count=count)
            data = np.fromiter(data_gen, dtype=float, count=count)

            # Create COO matrix then convert to CSR
            coo = coo_matrix((data, (rows, cols)), shape=(n, n), dtype=float)
            return coo.tocsr()

        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            msg = f"Failed to build sparse matrix: {e}"
            raise ValidationError(msg) from e

    def _validate_stochasticity(self, matrix: spmatrix) -> None:
        """
        Validate that matrix rows sum to approximately 1.0.
        Uses sparse operations where possible.

        Args:
            matrix: The sparse influence matrix.

        Raises:
            ValidationError: If any row sum deviates from 1.0 beyond tolerance.
        """
        try:
            # Calculate row sums
            # For sparse matrix, sum(axis=1) returns a dense matrix (n x 1)
            row_sums = matrix.sum(axis=1)

            # Convert to 1D array
            row_sums = row_sums.A1 if hasattr(row_sums, "A1") else np.array(row_sums).flatten()

            if not np.allclose(row_sums, 1.0, atol=1e-5):
                 # Log first few errors
                 invalid_indices = np.where(~np.isclose(row_sums, 1.0, atol=1e-5))[0]
                 logger.error(f"Matrix row sums invalid at indices: {invalid_indices[:5]}... Values: {row_sums[invalid_indices][:5]}")
                 msg = "Influence matrix rows must sum to 1.0"
                 raise ValidationError(msg)

        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            msg = f"Stochasticity check failed: {e}"
            raise ValidationError(msg) from e

    def calculate_consensus(self, network: InfluenceNetwork) -> list[float]:
        """
        Run the DeGroot model to calculate final opinion distribution.
        Always uses sparse matrices (CSR) for memory efficiency.

        Args:
            network: The influence network containing stakeholders and weights.

        Returns:
            A list of final opinion values (0.0 to 1.0) for each stakeholder.
        """
        n = len(network.stakeholders)
        if n == 0:
            return []

        # Convert opinions to numpy array
        opinions = np.array([s.initial_support for s in network.stakeholders], dtype=float)

        # Build Sparse Matrix
        try:
            matrix_op = self._build_sparse_matrix(network, n)
        except Exception as e:
             if isinstance(e, ValidationError):
                 raise
             raise ValidationError(str(e)) from e

        # Validate
        self._validate_stochasticity(matrix_op)

        max_steps = self.settings.max_steps
        tolerance = self.settings.tolerance

        current_ops = opinions

        for _ in range(max_steps):
            # Sparse Matrix-Vector Multiplication
            # matrix_op is CSR matrix
            next_ops = matrix_op.dot(current_ops)

            if np.allclose(current_ops, next_ops, atol=tolerance):
                logger.info("Consensus converged.")
                return cast(list[float], next_ops.tolist())
            current_ops = next_ops

        return cast(list[float], current_ops.tolist())
