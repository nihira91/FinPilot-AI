# ─────────────────────────────────────────────────────────────────────────────
# utils/chart_builder.py — Plotly Chart Utilities
# ─────────────────────────────────────────────────────────────────────────────

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import json


def create_time_series_chart(data: dict, title: str = "Time Series Analysis") -> go.Figure:
    """
    Create interactive time series line chart.
    
    Args:
        data: Dict with 'dates' and 'values' keys, or dict of {label: values}
        title: Chart title
    
    Returns:
        Plotly Figure object
    """
    fig = go.Figure()
    
    if isinstance(data, dict) and ('dates' in data or 'values' in data):
        # Simple time series format
        fig.add_trace(go.Scatter(
            x=data.get('dates', list(range(len(data.get('values', []))))),
            y=data.get('values', []),
            mode='lines+markers',
            name='Value',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=8)
        ))
    else:
        # Multiple series format
        colors = px.colors.qualitative.Set2
        for idx, (label, values) in enumerate(data.items()):
            if isinstance(values, (list, tuple)):
                fig.add_trace(go.Scatter(
                    y=values,
                    mode='lines+markers',
                    name=label,
                    line=dict(color=colors[idx % len(colors)], width=2),
                    marker=dict(size=6)
                ))
    
    fig.update_layout(
        title=title,
        hovermode='x unified',
        xaxis_title='Period',
        yaxis_title='Value',
        template='plotly_white',
        height=500,
        font=dict(size=12)
    )
    return fig


def create_bar_chart(data: dict, title: str = "Comparison", orientation: str = 'v') -> go.Figure:
    """
    Create bar chart for comparisons.
    
    Args:
        data: Dict with 'labels' and 'values', or {category: value}
        title: Chart title
        orientation: 'v' for vertical, 'h' for horizontal
    
    Returns:
        Plotly Figure object
    """
    if 'labels' in data and 'values' in data:
        labels = data['labels']
        values = data['values']
    else:
        labels = list(data.keys())
        values = list(data.values())
    
    fig = go.Figure(data=[
        go.Bar(
            x=labels if orientation == 'v' else values,
            y=values if orientation == 'v' else labels,
            orientation=orientation,
            marker=dict(color='#2ca02c'),
            text=values,
            textposition='auto',
        )
    ])
    
    fig.update_layout(
        title=title,
        hovermode='closest',
        xaxis_title='Category' if orientation == 'v' else 'Value',
        yaxis_title='Value' if orientation == 'v' else 'Category',
        template='plotly_white',
        height=500,
        font=dict(size=12),
        showlegend=False
    )
    return fig


def create_pie_chart(data: dict, title: str = "Distribution") -> go.Figure:
    """
    Create pie chart for distribution analysis.
    
    Args:
        data: Dict with 'labels' and 'values', or {category: value}
        title: Chart title
    
    Returns:
        Plotly Figure object
    """
    if 'labels' in data and 'values' in data:
        labels = data['labels']
        values = data['values']
    else:
        labels = list(data.keys())
        values = list(data.values())
    
    fig = go.Figure(data=[go.Pie(labels=labels, values=values)])
    
    fig.update_layout(
        title=title,
        template='plotly_white',
        height=500,
        font=dict(size=12)
    )
    return fig


def create_comparison_bars(data: dict, title: str = "Multi-Category Comparison") -> go.Figure:
    """
    Create grouped/stacked bar chart for multiple categories.
    
    Args:
        data: Dict of {category: {subcategory: value}}
        title: Chart title
    
    Returns:
        Plotly Figure object
    """
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set2
    
    for idx, (category, subdata) in enumerate(data.items()):
        if isinstance(subdata, dict):
            labels = list(subdata.keys())
            values = list(subdata.values())
            fig.add_trace(go.Bar(
                name=category,
                x=labels,
                y=values,
                marker=dict(color=colors[idx % len(colors)])
            ))
    
    fig.update_layout(
        title=title,
        barmode='group',
        hovermode='x unified',
        xaxis_title='Category',
        yaxis_title='Value',
        template='plotly_white',
        height=500,
        font=dict(size=12)
    )
    return fig


def create_trend_analysis(df: pd.DataFrame, x_col: str, y_col: str, title: str = "Trend Analysis") -> go.Figure:
    """
    Create scatter plot with trend line.
    
    Args:
        df: DataFrame with data
        x_col: Column name for X axis
        y_col: Column name for Y axis
        title: Chart title
    
    Returns:
        Plotly Figure object
    """
    fig = px.scatter(df, x=x_col, y=y_col, title=title, trendline="ols")
    
    fig.update_layout(
        hovermode='closest',
        template='plotly_white',
        height=500,
        font=dict(size=12)
    )
    return fig


def clean_numeric_data(data) -> dict:
    """
    Clean and convert data to numeric format for charting.
    Handles both dict and DataFrame inputs.
    Preserves non-numeric keys for time series data.
    
    Args:
        data: Dict or DataFrame with mixed types
    
    Returns:
        Cleaned dict with numeric values
    """
    if isinstance(data, pd.DataFrame):
        numeric_cols = data.select_dtypes(include=['number']).columns
        return data[numeric_cols].to_dict('list')
    
    cleaned = {}
    for key, value in data.items():
        if isinstance(value, (int, float)):
            cleaned[key] = float(value)
        elif isinstance(value, str):
            try:
                cleaned[key] = float(value)
            except ValueError:
                # Keep non-numeric strings as-is (useful for categorical data)
                cleaned[key] = value
        elif isinstance(value, (list, tuple)):
            # Convert list elements to numeric
            numeric_list = []
            for v in value:
                if isinstance(v, (int, float)):
                    numeric_list.append(float(v))
                elif isinstance(v, str):
                    try:
                        numeric_list.append(float(v))
                    except ValueError:
                        numeric_list.append(v)  # Keep non-numeric strings
                else:
                    numeric_list.append(v)
            cleaned[key] = numeric_list
    
    return cleaned


def extract_financial_metrics(metrics: dict) -> dict:
    """
    Extract chartable metrics from financial analysis results.
    
    Args:
        metrics: Dict from financial agent with analysis data
    
    Returns:
        Dict ready for charting
    """
    chartable = {}
    
    # Revenue and expenses
    if "total_revenue" in metrics:
        chartable["revenue"] = metrics.get("total_revenue", 0)
    if "total_cost_sum" in metrics:
        chartable["total_costs"] = metrics.get("total_cost_sum", 0)
    if "net_income" in metrics:
        chartable["net_income"] = metrics.get("net_income", 0)
    
    # Cost breakdown if available
    if "cost_breakdown" in metrics:
        chartable["cost_details"] = metrics["cost_breakdown"]
    
    # Time series if available
    if "time_series_revenue" in metrics:
        chartable["revenue_trend"] = metrics["time_series_revenue"]
    
    return chartable


def extract_sales_metrics(metrics: dict) -> dict:
    """
    Extract chartable metrics from sales analysis results.
    
    Args:
        metrics: Dict from sales agent with analysis data
    
    Returns:
        Dict ready for charting
    """
    chartable = {}
    
    # Sales by region/category if available
    if "sales_by_region" in metrics:
        chartable["sales_by_region"] = metrics["sales_by_region"]
    if "sales_by_product" in metrics:
        chartable["sales_by_product"] = metrics["sales_by_product"]
    
    # Growth trends
    if "monthly_sales" in metrics:
        chartable["monthly_trend"] = metrics["monthly_sales"]
    if "conversion_rate" in metrics:
        chartable["conversion"] = metrics["conversion_rate"]
    
    return chartable
