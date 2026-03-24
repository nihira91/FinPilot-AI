# ─────────────────────────────────────────────────────────────────────────────
# utils/visualization_helpers.py — Visualization Utilities
# ─────────────────────────────────────────────────────────────────────────────

import re


# Keywords that trigger visualization
VISUALIZATION_KEYWORDS = {
    "chart": ["chart", "diagram", "graph", "visual", "display", "show"],
    "specific_type": {
        "line": ["line chart", "trend", "timeline", "time series"],
        "bar": ["bar chart", "comparison", "breakdown", "vs", "versus"],
        "pie": ["pie chart", "distribution", "percentage", "share", "split"],
        "all": ["visualize", "plot", "graph", "show me", "draw", "illustrate"]
    }
}


def detect_visualization_request(query: str) -> tuple:
    """
    Detect if user is asking for visualization.
    Returns (wants_visualization: bool, chart_type: str)
    
    chart_type can be: 'line', 'bar', 'pie', 'auto' (let agent decide)
    """
    query_lower = query.lower()
    
    # Check for explicit chart type requests
    for chart_type, keywords in VISUALIZATION_KEYWORDS["specific_type"].items():
        if chart_type != "all":
            if any(kw in query_lower for kw in keywords):
                return True, chart_type
    
    # Check for general visualization keywords
    all_keywords = VISUALIZATION_KEYWORDS["specific_type"]["all"]
    if any(kw in query_lower for kw in all_keywords):
        return True, "auto"
    
    # Check for chart in general keywords
    general_keywords = VISUALIZATION_KEYWORDS["chart"]
    if any(kw in query_lower for kw in general_keywords):
        return True, "auto"
    
    return False, None


def get_chart_type_suggestion(query: str, agent_domain: str) -> str:
    """
    Suggest chart type based on query and agent domain.
    
    Args:
        query: User's query
        agent_domain: Agent that produced the analysis (financial, sales, etc)
    
    Returns:
        Suggested chart type: 'line', 'bar', 'pie', 'comparison'
    """
    query_lower = query.lower()
    
    # User specified a chart type
    if "line" in query_lower or "trend" in query_lower:
        return "line"
    if "bar" in query_lower or "comparison" in query_lower:
        return "bar"
    if "pie" in query_lower or "distribution" in query_lower:
        return "pie"
    
    # Domain-based suggestions
    if "financial" in agent_domain.lower():
        # Financial data often benefits from time series
        if "trend" in query_lower or "forecast" in query_lower:
            return "line"
        if "breakdown" in query_lower or "cost" in query_lower:
            return "bar"
        if "allocation" in query_lower or "share" in query_lower:
            return "pie"
        return "line"  # Default for financial
    
    if "sales" in agent_domain.lower():
        if "region" in query_lower or "product" in query_lower:
            return "bar"
        if "trend" in query_lower or "growth" in query_lower:
            return "line"
        if "mix" in query_lower or "share" in query_lower:
            return "pie"
        return "bar"  # Default for sales
    
    return "auto"


def format_metric_for_chart(key: str, value, agent_domain: str = None) -> dict:
    """
    Format a metric key-value pair into chart-ready format.
    
    Args:
        key: Metric name
        value: Metric value (can be dict, list, or scalar)
        agent_domain: Agent domain for context
    
    Returns:
        Dict with 'title', 'data', 'suggested_chart_type'
    """
    chart_suggestion = "auto"
    
    # Timeline/trend data
    if isinstance(value, dict) and len(value) > 2:
        chart_suggestion = "line"
        data = {"dates": list(value.keys()), "values": list(value.values())}
    
    # Breakdown data
    elif isinstance(value, dict):
        chart_suggestion = "pie" if len(value) <= 5 else "bar"
        data = value
    
    # List data
    elif isinstance(value, (list, tuple)):
        chart_suggestion = "bar"
        data = {"values": value, "labels": [f"Item {i+1}" for i in range(len(value))]}
    
    # Scalar value
    else:
        data = {str(key): float(value) if isinstance(value, (int, float)) else 0}
        chart_suggestion = "bar"
    
    return {
        "title": format_metric_title(key),
        "data": data,
        "suggested_chart_type": chart_suggestion,
        "metric_name": key
    }


def format_metric_title(metric_name: str) -> str:
    """
    Convert metric name to readable title.
    'total_revenue' -> 'Total Revenue'
    'cost_breakdown' -> 'Cost Breakdown'
    """
    # Replace underscores with spaces
    title = metric_name.replace("_", " ")
    # Capitalize each word
    title = " ".join(word.capitalize() for word in title.split())
    return title


def prepare_chart_data(response_data: dict, chart_type: str = "auto") -> list:
    """
    Extract all chartable metrics from agent response.
    
    Args:
        response_data: Dict from financial/sales agent with analysis results
        chart_type: Specific chart type requested ('line', 'bar', 'pie', 'auto')
    
    Returns:
        List of dicts with chartable data: [{title, data, chart_type}, ...]
    """
    chartable_metrics = []
    
    # Common numeric keys to visualize
    NUMERIC_KEYS = [
        'total_revenue', 'total_expenses', 'net_income', 'profit',
        'total_cogs', 'gross_profit', 'growth_rate', 'conversion_rate',
        'cost_breakdown', 'sales_by_region', 'sales_by_product',
        'monthly_sales', 'quarterly_revenue', 'time_series_revenue',
        'budget_vs_actual', 'total_cost_sum'
    ]
    
    # Extract metrics from response
    for key in NUMERIC_KEYS:
        if key in response_data:
            value = response_data[key]
            if value is not None and (isinstance(value, (int, float, dict, list)) and value):
                metric_data = format_metric_for_chart(key, value, response_data.get("agent_domain", ""))
                
                # Override chart type if specified
                if chart_type != "auto":
                    metric_data["suggested_chart_type"] = chart_type
                
                chartable_metrics.append(metric_data)
    
    return chartable_metrics


def is_data_chartable(data) -> bool:
    """
    Check if data can be visualized as a chart.
    """
    if isinstance(data, (int, float)):
        return True
    if isinstance(data, dict) and len(data) > 0:
        return True
    if isinstance(data, (list, tuple)) and len(data) > 0:
        return True
    return False
