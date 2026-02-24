from src.core.metrics import (
    calculate_ltv,
    calculate_payback_period,
    calculate_roi,
)


class TestMetricsLogic:
    """Test suite for financial calculations."""

    def test_calculate_ltv(self) -> None:
        """Test Lifetime Value calculation."""
        # Simple case: ARPU=100, Churn=0.05 (5%) -> LTV = 100/0.05 = 2000
        ltv = calculate_ltv(arpu=100.0, churn_rate=0.05)
        assert ltv == 2000.0

    def test_calculate_ltv_zero_churn(self) -> None:
        """Test LTV with zero churn (should cap or handle graceful)."""
        ltv = calculate_ltv(arpu=100.0, churn_rate=0.0)
        assert ltv == float("inf")

    def test_calculate_ltv_negative_values(self) -> None:
        """Test LTV with negative values (edge case)."""
        # Negative ARPU -> Negative LTV
        assert calculate_ltv(arpu=-100.0, churn_rate=0.05) == -2000.0
        # Negative Churn (should be treated as 0 or handled? implementation caps at 0 check)
        # The implementation checks if churn <= 0, returns inf.
        assert calculate_ltv(arpu=100.0, churn_rate=-0.05) == float("inf")

    def test_calculate_payback_period(self) -> None:
        """Test Payback Period calculation."""
        # CAC=500, ARPU=100 -> 5 months
        months = calculate_payback_period(cac=500.0, arpu=100.0)
        assert months == 5.0

    def test_calculate_payback_period_zero_arpu(self) -> None:
        """Test Payback Period with zero ARPU."""
        # Infinite payback
        payback = calculate_payback_period(cac=500.0, arpu=0.0)
        assert payback == float("inf")

    def test_calculate_payback_period_negative(self) -> None:
        """Test Payback Period with negative values."""
        # Negative ARPU (e.g. losing money per user) -> Infinite payback (never recover)
        assert calculate_payback_period(cac=500.0, arpu=-10.0) == float("inf")

    def test_calculate_roi(self) -> None:
        """Test ROI (LTV/CAC ratio)."""
        # LTV=3000, CAC=1000 -> ROI=3.0
        roi = calculate_roi(ltv=3000.0, cac=1000.0)
        assert roi == 3.0

    def test_calculate_roi_zero_cac(self) -> None:
        """Test ROI with zero CAC."""
        # Infinite ROI
        roi = calculate_roi(ltv=3000.0, cac=0.0)
        assert roi == float("inf")

    def test_calculate_roi_negative_cac(self) -> None:
        """Test ROI with negative CAC (should be impossible but handle gracefully)."""
        # Implementation checks if cac <= 0 -> inf
        assert calculate_roi(ltv=3000.0, cac=-100.0) == float("inf")
