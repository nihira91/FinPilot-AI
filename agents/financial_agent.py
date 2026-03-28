"""Backward-compatible facade for the Financial Analyst agent.

This module keeps the original import path stable while the implementation
is split into focused modules under agents/financial_agent_core/.
"""

from agents.financial_agent_core import (
    CHART_INTENT_KEYWORDS,
    MODEL_ID,
    call_gemini,
    compute_detailed_metrics,
    compute_metrics,
    detect_chart_intent,
    detect_cost_columns,
    run,
    safe_format_value,
    validate_response_against_metrics,
)

__all__ = [
    "MODEL_ID",
    "CHART_INTENT_KEYWORDS",
    "detect_chart_intent",
    "safe_format_value",
    "call_gemini",
    "validate_response_against_metrics",
    "detect_cost_columns",
    "compute_detailed_metrics",
    "compute_metrics",
    "run",
]
