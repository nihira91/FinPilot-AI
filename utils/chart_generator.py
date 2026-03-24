import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Color Palette (FinPilot theme) ────────────────────────
GOLD       = "#C9A84C"
GOLD_LIGHT = "#E8C97A"
NAVY       = "#0D1117"
GREEN      = "#2ECC71"
RED        = "#E74C3C"
BLUE       = "#3498DB"
MUTED      = "#7A8899"

LAYOUT = dict(
    paper_bgcolor = "rgba(0,0,0,0)",
    plot_bgcolor  = "rgba(0,0,0,0)",
    font          = dict(color="#F0EAD6", family="DM Sans"),
    margin        = dict(l=20, r=20, t=40, b=20),
    legend        = dict(
        bgcolor     = "rgba(0,0,0,0)",
        bordercolor = "rgba(201,168,76,0.2)",
        borderwidth = 1
    )
)


# ── Financial Charts ──────────────────────────────────────

def revenue_vs_expenses_bar(df: pd.DataFrame):
    """Bar chart — Revenue vs Expenses per quarter"""
    if df is None or df.empty:
        return None
        
    fig = go.Figure()

    fig.add_trace(go.Bar(
        name   = "Revenue",
        x      = df["quarter"] if "quarter" in df.columns else df.index,
        y      = df["revenue"] if "revenue" in df.columns else df.get("total_revenue", []),
        marker_color = GOLD,
    ))
    fig.add_trace(go.Bar(
        name   = "Expenses",
        x      = df["quarter"] if "quarter" in df.columns else df.index,
        y      = df["expenses"] if "expenses" in df.columns else df.get("total_expenses", []),
        marker_color = RED,
        opacity      = 0.8,
    ))

    fig.update_layout(
        **LAYOUT,
        title      = "Revenue vs Expenses",
        barmode    = "group",
        xaxis      = dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis      = dict(gridcolor="rgba(255,255,255,0.05)"),
        height     = 400,
    )
    return fig


def net_income_trend(df: pd.DataFrame):
    """Line chart — Net Income trend"""
    if df is None or df.empty:
        return None
        
    net_income_col = "net_income" if "net_income" in df.columns else None
    if net_income_col is None:
        return None
        
    colors = [GREEN if v >= 0 else RED for v in df[net_income_col]]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x    = df["quarter"] if "quarter" in df.columns else df.index,
        y    = df[net_income_col],
        mode = "lines+markers",
        line = dict(color=GREEN, width=2.5),
        marker = dict(
            color = colors,
            size  = 8,
            line  = dict(color=NAVY, width=1)
        ),
        fill      = "tozeroy",
        fillcolor = "rgba(46,204,113,0.08)",
        name      = "Net Income"
    ))

    fig.update_layout(
        **LAYOUT,
        title  = "Net Income Trend",
        xaxis  = dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis  = dict(gridcolor="rgba(255,255,255,0.05)"),
        height = 400,
    )
    return fig


def expense_breakdown_pie(df: pd.DataFrame):
    """Pie chart — Expense vs Profit breakdown"""
    if df is None or df.empty:
        return None
        
    exp_col = "expenses" if "expenses" in df.columns else "total_expenses"
    income_col = "net_income"
    
    if exp_col not in df.columns or income_col not in df.columns:
        return None
        
    total_exp    = df[exp_col].sum()
    total_income = df[income_col].sum()

    fig = go.Figure(go.Pie(
        labels    = ["Expenses", "Net Income"],
        values    = [total_exp, total_income],
        hole      = 0.5,
        marker    = dict(colors=[RED, GREEN]),
        textfont  = dict(color="#F0EAD6"),
    ))

    fig.update_layout(
        **LAYOUT,
        title = "Expense vs Profit Split",
        height = 400,
    )
    return fig


def profit_margin_gauge(df: pd.DataFrame):
    """Gauge chart — Profit margin"""
    if df is None or df.empty:
        return None
        
    rev_col = "revenue" if "revenue" in df.columns else "total_revenue"
    income_col = "net_income"
    
    if rev_col not in df.columns or income_col not in df.columns:
        return None
        
    margin = (df[income_col].sum() / df[rev_col].sum()) * 100

    color = GREEN if margin > 20 else GOLD if margin > 10 else RED

    fig = go.Figure(go.Indicator(
        mode  = "gauge+number+delta",
        value = margin,
        title = dict(
            text = "Profit Margin %",
            font = dict(color="#F0EAD6", size=14)
        ),
        number = dict(suffix="%", font=dict(color=color, size=28)),
        gauge  = dict(
            axis      = dict(range=[0, 50], tickcolor="#7A8899"),
            bar       = dict(color=color),
            bgcolor   = "rgba(255,255,255,0.05)",
            bordercolor = "rgba(201,168,76,0.2)",
            steps     = [
                dict(range=[0, 10],  color="rgba(231,76,60,0.1)"),
                dict(range=[10, 20], color="rgba(201,168,76,0.1)"),
                dict(range=[20, 50], color="rgba(46,204,113,0.1)"),
            ],
            threshold = dict(
                line  = dict(color=GOLD, width=2),
                value = 20
            )
        )
    ))

    fig.update_layout(**LAYOUT, height=250)
    return fig


# ── Sales Charts ──────────────────────────────────────────

def sales_trend_line(df: pd.DataFrame):
    """Line chart — Sales over time"""
    if df is None or df.empty:
        return None
        
    if "sales" not in df.columns:
        return None
        
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x    = df["month"] if "month" in df.columns else df.index,
        y    = df["sales"],
        mode = "lines+markers",
        line = dict(color=GOLD, width=2.5),
        marker = dict(
            color = GOLD_LIGHT,
            size  = 7,
            line  = dict(color=NAVY, width=1)
        ),
        fill      = "tozeroy",
        fillcolor = "rgba(201,168,76,0.08)",
        name      = "Sales"
    ))

    fig.update_layout(
        **LAYOUT,
        title  = "Sales Trend",
        xaxis  = dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis  = dict(gridcolor="rgba(255,255,255,0.05)"),
        height = 400,
    )
    return fig


def region_sales_bar(df: pd.DataFrame):
    """Bar chart — Sales by region"""
    if df is None or df.empty:
        return None
        
    if "region" not in df.columns or "sales" not in df.columns:
        return None

    region_data = df.groupby("region")["sales"].sum().reset_index()

    fig = px.bar(
        region_data,
        x     = "region",
        y     = "sales",
        color = "sales",
        color_continuous_scale = [[0, RED], [0.5, GOLD], [1, GREEN]],
        title = "Sales by Region"
    )
    fig.update_layout(**LAYOUT, height=400)
    fig.update_coloraxes(showscale=False)
    return fig


def product_performance_pie(df: pd.DataFrame):
    """Pie chart — Product performance"""
    if df is None or df.empty:
        return None
        
    if "product" not in df.columns or "sales" not in df.columns:
        return None

    product_data = df.groupby("product")["sales"].sum().reset_index()

    fig = go.Figure(go.Pie(
        labels   = product_data["product"],
        values   = product_data["sales"],
        hole     = 0.4,
        marker   = dict(colors=[GOLD, BLUE, GREEN, RED]),
        textfont = dict(color="#F0EAD6"),
    ))
    fig.update_layout(**LAYOUT, title="Product Performance", height=400)
    return fig


def sales_growth_indicator(df: pd.DataFrame):
    """Growth rate indicator"""
    if df is None or df.empty or len(df) < 2:
        return None
        
    if "sales" not in df.columns:
        return None

    first = df["sales"].iloc[0]
    last  = df["sales"].iloc[-1]
    growth = ((last - first) / first) * 100 if first != 0 else 0

    color = GREEN if growth > 0 else RED

    fig = go.Figure(go.Indicator(
        mode  = "number+delta",
        value = last,
        title = dict(
            text = "Latest Sales",
            font = dict(color="#F0EAD6", size=14)
        ),
        number = dict(
            font   = dict(color=color, size=32),
            prefix = "₹"
        ),
        delta  = dict(
            reference = first,
            valueformat = ".1f",
            suffix    = "%",
            relative  = True,
            font      = dict(size=14),
            increasing  = dict(color=GREEN),
            decreasing  = dict(color=RED),
        )
    ))
    fig.update_layout(**LAYOUT, height=200)
    return fig


# ── Generic Dict-to-Chart Converter ────────────────────────

def create_breakdown_pie(data_dict: dict, title: str = "Distribution"):
    """Create pie chart from dict of {category: value}"""
    if not data_dict:
        return None
        
    labels = list(data_dict.keys())
    values = list(data_dict.values())
    
    # Filter out non-numeric values
    filtered_labels = []
    filtered_values = []
    for lbl, val in zip(labels, values):
        try:
            numeric_val = float(val)
            if numeric_val > 0:
                filtered_labels.append(str(lbl))
                filtered_values.append(numeric_val)
        except (ValueError, TypeError):
            continue
    
    if not filtered_values:
        return None
        
    fig = go.Figure(go.Pie(
        labels = filtered_labels,
        values = filtered_values,
        marker = dict(colors=[GOLD, BLUE, GREEN, RED]),
        textfont = dict(color="#F0EAD6"),
    ))
    
    fig.update_layout(
        **LAYOUT,
        title = title,
        height = 400,
    )
    return fig


def create_category_bar(data_dict: dict, title: str = "Comparison"):
    """Create bar chart from dict of {category: value}"""
    if not data_dict:
        return None
        
    labels = []
    values = []
    
    for key, val in data_dict.items():
        labels.append(str(key))
        try:
            values.append(float(val))
        except (ValueError, TypeError):
            values.append(0)
    
    fig = go.Figure(data=[
        go.Bar(
            x = labels,
            y = values,
            marker = dict(color=GOLD),
            text = values,
            textposition = 'auto',
        )
    ])
    
    fig.update_layout(
        **LAYOUT,
        title = title,
        xaxis_title = "Category",
        yaxis_title = "Value",
        height = 400,
    )
    return fig


def create_timeseries_line(data_dict: dict, title: str = "Trend"):
    """Create line chart from dict of {date/period: value}"""
    if not data_dict:
        return None
        
    dates = list(data_dict.keys())
    values = []
    
    for val in data_dict.values():
        try:
            values.append(float(val))
        except (ValueError, TypeError):
            values.append(0)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x = dates,
        y = values,
        mode = "lines+markers",
        line = dict(color=GOLD, width=2.5),
        marker = dict(
            color = GOLD_LIGHT,
            size = 7,
            line = dict(color=NAVY, width=1)
        ),
        fill = "tozeroy",
        fillcolor = "rgba(201,168,76,0.08)",
        name = "Value"
    ))
    
    fig.update_layout(
        **LAYOUT,
        title = title,
        xaxis_title = "Period",
        yaxis_title = "Value",
        xaxis = dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis = dict(gridcolor="rgba(255,255,255,0.05)"),
        height = 400,
    )
    return fig
