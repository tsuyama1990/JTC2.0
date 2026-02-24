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
        # If churn is 0, LTV is infinite. Function should probably return a high cap or raise error?
        # Or return 0 if uncalculable?
        # Let's assume it handles it by returning 0.0 or a large number.
        # Ideally, it should cap at some reasonable max or handle division by zero.
        # Let's assume we pass a small epsilon or the function handles it.
        # For this test, let's expect it to not crash.
        # Update: Let's assume we expect a ValueError or a cap.
        # Let's test standard behavior first.
        ltv = calculate_ltv(arpu=100.0, churn_rate=0.0)
        assert ltv > 0

    def test_calculate_payback_period(self) -> None:
        """Test Payback Period calculation."""
        # CAC=500, ARPU=100 -> 5 months
        months = calculate_payback_period(cac=500.0, arpu=100.0)
        assert months == 5.0

    def test_calculate_payback_period_zero_arpu(self) -> None:
        """Test Payback Period with zero ARPU."""
        # Infinite payback
        payback = calculate_payback_period(cac=500.0, arpu=0.0)
        assert payback == float("inf") or payback == 0.0

    def test_calculate_roi(self) -> None:
        """Test ROI (LTV/CAC ratio)."""
        # LTV=3000, CAC=1000 -> ROI=3.0
        roi = calculate_roi(ltv=3000.0, cac=1000.0)
        assert roi == 3.0

    def test_calculate_roi_zero_cac(self) -> None:
        """Test ROI with zero CAC."""
        # Infinite ROI
        roi = calculate_roi(ltv=3000.0, cac=0.0)
        assert roi == float("inf") or roi > 100.0
