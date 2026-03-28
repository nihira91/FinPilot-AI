"""Backward-compatible facade for the Sales Analyst agent.

This module keeps the original import path stable while the implementation
is split into focused modules under agents/sales_agent_core/.
"""

from agents.sales_agent_core import (
    CHART_INTENT_KEYWORDS,
    MODEL_ID,
    VISUALIZATION_AVAILABLE,
    call_gemini,
    compute_trends,
    detect_chart_intent,
    detect_sales_column,
    parse_month_flexible,
    run,
    safe_format_value,
    validate_response,
)

__all__ = [
    "MODEL_ID",
    "CHART_INTENT_KEYWORDS",
    "VISUALIZATION_AVAILABLE",
    "detect_chart_intent",
    "safe_format_value",
    "validate_response",
    "call_gemini",
    "parse_month_flexible",
    "detect_sales_column",
    "compute_trends",
    "run",
]
