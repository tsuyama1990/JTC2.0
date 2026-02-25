"""
Core logic for financial metrics calculations.
"""

import logging

logger = logging.getLogger(__name__)


def calculate_ltv(arpu: float, churn_rate: float) -> float:
    """
    Calculate Lifetime Value (LTV).

    Formula: ARPU / Churn Rate
    """
    if churn_rate <= 0.0:
        logger.warning("Churn rate is <= 0. Returning infinite LTV.")
        return float("inf")
    return arpu / churn_rate


def calculate_payback_period(cac: float, arpu: float) -> float:
    """
    Calculate Payback Period in months.

    Formula: CAC / ARPU
    """
    if arpu <= 0.0:
        logger.warning("ARPU is <= 0. Returning infinite Payback Period.")
        return float("inf")
    return cac / arpu


def calculate_roi(ltv: float, cac: float) -> float:
    """
    Calculate ROI (LTV/CAC ratio).

    Formula: LTV / CAC
    """
    if cac <= 0.0:
        logger.warning("CAC is <= 0. Returning infinite ROI.")
        return float("inf")
    return ltv / cac
