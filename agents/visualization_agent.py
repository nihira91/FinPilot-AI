# ─────────────────────────────────────────────────────────────────────────────
# agents/visualization_agent.py — Interactive Chart & Graph Generation
# ─────────────────────────────────────────────────────────────────────────────

import json
import pandas as pd
from utils.chart_builder import (
    create_time_series_chart, create_bar_chart, create_pie_chart,
    create_comparison_bars, clean_numeric_data,
    extract_financial_metrics, extract_sales_metrics
)
from utils.visualization_helpers import (
    prepare_chart_data, get_chart_type_suggestion, format_metric_title
)


def run(agent_response: dict, chart_type: str = "auto", query: str = "") -> dict:
    """
    Visualization Agent - Creates interactive Plotly charts from agent analysis.
    
    Called by Orchestrator when user requests visualization.
    
    Args:
        agent_response: Dict from financial/sales agent with analysis results
        chart_type: 'line', 'bar', 'pie', 'auto' (let agent decide)
        query: Original user query for context
    
    Returns:
        {
            "agent": "Visualization Agent",
            "agent_domain": "Data Visualization",
            "response": "Chart generation summary",
            "charts": [
                {
                    "title": "Revenue Trend",
                    "chart_type": "line",
                    "plotly_json": {...},  # Plotly figure JSON for Streamlit
                    "metric_name": "total_revenue"
                },
                ...
            ],
            "source_agent": "Financial Analyst" or "Sales Analyst",
            "source_domain": "financial_reports" or "sales_reports",
            "data_source": "Visualization (Charts)"
        }
    """
    
    print(f"\n[Visualization Agent] Processing visualization request (chart_type: {chart_type})")
    print(f"[Visualization Agent] Source agent: {agent_response.get('agent', 'Unknown')}")
    
    # Extract agent info
    source_agent = agent_response.get("agent", "Unknown Agent")
    source_domain = agent_response.get("agent_domain", "")
    
    # Prepare chartable data - extract metrics/data from response
    chartable_metrics = extract_chartable_data(agent_response, chart_type)
    
    if not chartable_metrics:
        print("[Visualization Agent] No chartable data found in response")
        return {
            "agent": "Visualization Agent",
            "agent_domain": "Data Visualization",
            "response": f"Could not extract chartable data from {source_agent} response. "
                        f"The analysis may not contain quantitative metrics suitable for visualization.",
            "charts": [],
            "source_agent": source_agent,
            "source_domain": source_domain,
            "data_source": "No Data",
            "confidence": "LOW"
        }
    
    print(f"[Visualization Agent] Found {len(chartable_metrics)} chartable metrics")
    
    # Create charts
    charts = []
    for metric in chartable_metrics:
        try:
            chart_fig = create_chart_for_metric(metric, chart_type)
            if chart_fig is not None:
                chart_json = chart_fig.to_json()
                charts.append({
                    "title": metric["title"],
                    "chart_type": metric.get("suggested_chart_type", "auto"),
                    "plotly_json": chart_json,
                    "metric_name": metric.get("metric_name", "Unknown"),
                    "data_summary": str(metric["data"])[:200]  # Preview of data
                })
                print(f"[Visualization Agent] ✓ Created {metric['suggested_chart_type']} chart: {metric['title']}")
        except Exception as e:
            print(f"[Visualization Agent] ✗ Failed to create chart for {metric['title']}: {str(e)}")
            continue
    
    if not charts:
        return {
            "agent": "Visualization Agent",
            "agent_domain": "Data Visualization",
            "response": "Chart generation failed for all metrics. Data may be insufficient for visualization.",
            "charts": [],
            "source_agent": source_agent,
            "source_domain": source_domain,
            "data_source": "Error",
            "confidence": "LOW"
        }
    
    # Build summary
    summary = f"✓ Generated {len(charts)} interactive charts from {source_agent} analysis:\n"
    summary += "\n".join([f"  • {c['title']} ({c['chart_type']})" for c in charts])
    
    print(f"[Visualization Agent] Successfully created {len(charts)} charts")
    
    return {
        "agent": "Visualization Agent",
        "agent_domain": "Data Visualization & Analytics",
        "response": summary,
        "charts": charts,
        "source_agent": source_agent,
        "source_domain": source_domain,
        "data_source": "Interactive Charts (Plotly)",
        "confidence": "HIGH" if len(charts) > 0 else "MEDIUM",
        "chart_count": len(charts)
    }


def create_chart_for_metric(metric_data: dict, chart_type_override: str = "auto"):
    """
    Create appropriate Plotly chart for a metric.
    
    Args:
        metric_data: Dict with 'title', 'data', 'suggested_chart_type'
        chart_type_override: Override the suggested chart type
    
    Returns:
        Plotly Figure object or None
    """
    title = metric_data.get("title", "Chart")
    data = metric_data.get("data", {})
    suggested_type = metric_data.get("suggested_chart_type", "bar")
    
    # Use override if specified
    chart_type = chart_type_override if chart_type_override != "auto" else suggested_type
    
    # For time series data with dates, skip cleaning (dates shouldn't be converted to float)
    if chart_type != "line" or ("dates" not in data):
        # Clean data for other chart types or if no dates key
        try:
            data = clean_numeric_data(data)
        except Exception as e:
            print(f"[Visualization Agent] Data cleaning failed: {e}")
            return None
    
    if not data:
        return None
    
    try:
        # Create appropriate chart
        if chart_type == "line":
            return create_time_series_chart(data, title)
        elif chart_type == "bar":
            return create_bar_chart(data, title)
        elif chart_type == "pie":
            # Pie charts need simpler data format
            return create_pie_chart(data, title)
        elif chart_type == "comparison":
            return create_comparison_bars(data, title)
        else:
            # Default to bar
            return create_bar_chart(data, title)
    
    except Exception as e:
        print(f"[Visualization Agent] Chart creation error ({chart_type}): {e}")
        return None


def extract_chartable_data(agent_response: dict, chart_type: str = "auto") -> list:
    """
    Extract chartable metrics from agent response dict.
    Handles financial, sales, and generic responses.
    Prioritizes: time_series/trends > breakdowns > key metrics comparison.
    
    Args:
        agent_response: Dict from agent with results
        chart_type: Preferred chart type
    
    Returns:
        List of dicts with chartable metric info (max 3 charts)
    """
    chartable = []
    agent_name = agent_response.get("agent", "").lower()
    print(f"[Visualization Agent] Extracting chartable data from {agent_name}")
    
    # Priority 1: Time series and breakdowns from metrics dict (most important)
    metrics = agent_response.get("metrics", {})
    if metrics and isinstance(metrics, dict):
        print(f"[Visualization Agent] Found metrics dict with {len(metrics)} keys: {list(metrics.keys())[:5]}...")
        chartable.extend(_extract_from_metrics(metrics, chart_type))
        print(f"[Visualization Agent] Extracted {len(chartable)} charts from metrics")
    
    # Priority 2: Extract from agent-specific structured data
    initial_count = len(chartable)
    if "financial" in agent_name:
        chartable.extend(_extract_financial_data(agent_response, chart_type))
    elif "sales" in agent_name:
        chartable.extend(_extract_sales_data(agent_response, chart_type))
    
    if len(chartable) > initial_count:
        print(f"[Visualization Agent] Extracted {len(chartable) - initial_count} agent-specific charts")
    
    # Priority 3: Look for time series or breakdown keys
    trend_keys = [
        "time_series_revenue", "monthly_revenue", "quarterly_revenue",
        "monthly_sales", "sales_by_region", "sales_by_product",
        "cost_breakdown", "budget_vs_actual", "revenue_by_month",
        "sales_trend", "expense_trend", "profit_trend",
    ]
    
    initial_count = len(chartable)
    for key in trend_keys:
        if key in agent_response:
            value = agent_response[key]
            if value is not None and isinstance(value, (dict, list)):
                metric_data = _format_metric_for_chart(key, value)
                if metric_data and metric_data not in chartable:
                    chartable.append(metric_data)
    
    if len(chartable) > initial_count:
        print(f"[Visualization Agent] Extracted {len(chartable) - initial_count} trend/breakdown charts")
    
    # Priority 4: If we found nothing yet, create comparison chart of key metrics
    if not chartable:
        print("[Visualization Agent] No trends/breakdowns found, creating key metrics chart...")
        key_metrics = _create_key_metrics_chart(agent_response)
        if key_metrics:
            chartable.append(key_metrics)
            print("[Visualization Agent] ✓ Created key metrics fallback chart")
        else:
            print("[Visualization Agent] ⚠ No metrics found to visualize")
    
    # Sort by importance and limit to 3 charts
    def sort_priority(item):
        chart_type = item.get("suggested_chart_type", "bar")
        if chart_type == "line":
            return 0  # Time series first
        elif chart_type == "pie":
            return 1  # Breakdowns second
        else:
            return 2  # Bar charts last
    
    chartable.sort(key=sort_priority)
    print(f"[Visualization Agent] Final chartable data: {len(chartable)} charts")
    return chartable[:3]  # Max 3 charts


def _create_key_metrics_chart(agent_response: dict) -> dict:
    """
    Create a fallback chart from key metrics when no trends/breakdowns exist.
    Useful for CSV analysis that produces only scalar metrics.
    """
    # Collect key metrics
    key_metrics = {}
    metric_names = [
        "total_revenue", "gross_profit", "net_income", 
        "total_expenses", "total_cogs"
    ]
    
    for name in metric_names:
        val = agent_response.get(name)
        if val and isinstance(val, (int, float)) and val != 0:
            # Clean up key name
            display_name = name.replace("_", " ").title()
            key_metrics[display_name] = float(val)
    
    if not key_metrics:
        return None
    
    return {
        "title": "Key Financial Metrics",
        "data": key_metrics,
        "suggested_chart_type": "bar",
        "metric_name": "key_metrics"
    }


def _extract_from_metrics(metrics: dict, chart_type: str = "auto") -> list:
    """
    Extract chartable data from metrics dict.
    ONLY includes dict/list data (trends, breakdowns) - skips single scalars.
    """
    chartable = []
    # Skip statistical scalar metrics - only include dict/list data
    skip_keys = {"count", "mean", "median", "std", "total", "sum", "average", "min", "max"}
    
    for key, value in metrics.items():
        key_lower = key.lower()
        # Skip statistical metrics and scalar values
        if key_lower in skip_keys or not isinstance(value, (dict, list)):
            continue
        
        if isinstance(value, (dict, list)) and value:
            metric_data = _format_metric_for_chart(key, value)
            if metric_data:
                chartable.append(metric_data)
    
    return chartable


def _extract_financial_data(response: dict, chart_type: str = "auto") -> list:
    """Extract financial-specific chartable data."""
    chartable = []
    fin_keys = ["total_revenue", "total_expenses", "net_income", "costs", "profit_margin"]
    
    for key in fin_keys:
        if key in response:
            value = response[key]
            if value:
                metric_data = _format_metric_for_chart(key, value)
                if metric_data:
                    chartable.append(metric_data)
    
    return chartable


def _extract_sales_data(response: dict, chart_type: str = "auto") -> list:
    """Extract sales-specific chartable data."""
    chartable = []
    sales_keys = ["sales_by_region", "sales_by_product", "monthly_sales", "growth_rate"]
    
    for key in sales_keys:
        if key in response:
            value = response[key]
            if value:
                metric_data = _format_metric_for_chart(key, value)
                if metric_data:
                    chartable.append(metric_data)
    
    return chartable


def _format_metric_for_chart(key: str, value, chart_type: str = "auto") -> dict:
    """
    Format a metric key-value pair into chart-ready format.
    Returns None for scalar values (not visualizable).
    Handles nested structures like period_breakdown with {period: {total: X, average: Y}}
    """
    # Skip scalar values - only visualize trends/breakdowns
    if isinstance(value, (int, float)):
        return None
    
    chart_suggestion = "auto"
    
    # Timeline/trend data (many items) - INCLUDING nested period structures
    if isinstance(value, dict) and len(value) > 2:
        # Check if this is a nested period structure with {period: {total: X, ...}}
        first_val = next(iter(value.values())) if value else None
        
        if isinstance(first_val, dict) and "total" in first_val:
            # Extract total values from nested structure
            chart_suggestion = "line"
            dates = []
            totals = []
            for period, metrics in value.items():
                dates.append(str(period))
                total = metrics.get("total", 0)
                if isinstance(total, (int, float)):
                    totals.append(float(total))
                else:
                    totals.append(0)
            data = {"dates": dates, "values": totals}
        else:
            # Regular dict with numeric values
            chart_suggestion = "line"
            numeric_values = []
            for v in value.values():
                if isinstance(v, (int, float)):
                    numeric_values.append(float(v))
                elif isinstance(v, str):
                    try:
                        numeric_values.append(float(v))
                    except ValueError:
                        numeric_values.append(0)
                else:
                    numeric_values.append(0)
            data = {"dates": list(value.keys()), "values": numeric_values}
    
    # Breakdown data (few items)
    elif isinstance(value, dict):
        if len(value) == 0:
            return None  # Empty data
        chart_suggestion = "pie" if len(value) <= 5 else "bar"
        data = value
    
    # List/tuple data
    elif isinstance(value, (list, tuple)):
        if len(value) == 0:
            return None  # Empty list
        chart_suggestion = "bar"
        data = {"values": value, "labels": [f"Item {i+1}" for i in range(len(value))]}
    
    else:
        # Unknown type - not visualizable
        return None
    
    return {
        "title": format_metric_title(key),
        "data": data,
        "suggested_chart_type": chart_suggestion,
        "metric_name": key
    }

