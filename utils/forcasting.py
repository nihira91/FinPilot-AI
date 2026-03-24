# utils/forecasting.py

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import mean_absolute_error
import plotly.graph_objects as go

# ── Color Theme ───────────────────────────────────────────
GOLD       = "#C9A84C"
GOLD_LIGHT = "#E8C97A"
GREEN      = "#2ECC71"
RED        = "#E74C3C"
BLUE       = "#3498DB"
MUTED      = "#7A8899"

LAYOUT = dict(
    paper_bgcolor = "rgba(0,0,0,0)",
    plot_bgcolor  = "rgba(0,0,0,0)",
    font          = dict(color="#F0EAD6", family="DM Sans"),
    margin        = dict(l=20, r=20, t=40, b=20),
)


def forecast_revenue(df: pd.DataFrame, periods: int = 4) -> dict:
    """
    Forecast future revenue using Polynomial Regression.
    
    Args:
        df      : DataFrame with 'revenue' column
        periods : How many future periods to predict
    
    Returns:
        dict with predictions, model accuracy, growth rate
    """
    
    if "revenue" not in df.columns:
        return {"error": "Revenue column not found in CSV"}
    
    if len(df) < 3:
        return {"error": "Need at least 3 data points for forecasting"}

    # ── Prepare Data ──────────────────────────────────────
    X = np.array(range(len(df))).reshape(-1, 1)
    y = df["revenue"].values

    # ── Polynomial Regression (degree 2) ──────────────────
    poly    = PolynomialFeatures(degree=2)
    X_poly  = poly.fit_transform(X)

    model = LinearRegression()
    model.fit(X_poly, y)

    # ── Accuracy ──────────────────────────────────────────
    y_pred = model.predict(X_poly)
    mae    = mean_absolute_error(y, y_pred)
    accuracy = max(0, 100 - (mae / y.mean() * 100))

    # ── Future Predictions ────────────────────────────────
    future_X      = np.array(
        range(len(df), len(df) + periods)
    ).reshape(-1, 1)
    future_X_poly = poly.transform(future_X)
    predictions   = model.predict(future_X_poly)

    # ── Growth Rate ───────────────────────────────────────
    last_actual  = y[-1]
    last_predict = predictions[-1]
    growth_rate  = ((last_predict - last_actual) / last_actual) * 100

    # ── Period Labels ─────────────────────────────────────
    if "quarter" in df.columns:
        last_label  = df["quarter"].iloc[-1]
        period_type = "Q"
    elif "month" in df.columns:
        last_label  = df["month"].iloc[-1]
        period_type = "Month"
    else:
        last_label  = f"Period {len(df)}"
        period_type = "Period"

    future_labels = [
        f"Forecast {period_type}{i+1}"
        for i in range(periods)
    ]

    return {
        "predictions":    predictions.tolist(),
        "future_labels":  future_labels,
        "accuracy":       round(accuracy, 1),
        "growth_rate":    round(growth_rate, 1),
        "mae":            round(mae, 2),
        "last_actual":    round(float(last_actual), 2),
        "next_predicted": round(float(predictions[0]), 2),
    }


def forecast_chart(df: pd.DataFrame, forecast_result: dict):
    """
    Create Plotly chart showing actual + forecasted revenue.
    """
    if "error" in forecast_result:
        return None

    # ── Labels ────────────────────────────────────────────
    if "quarter" in df.columns:
        actual_labels = df["quarter"].tolist()
    elif "month" in df.columns:
        actual_labels = df["month"].tolist()
    else:
        actual_labels = [f"Period {i+1}" for i in range(len(df))]

    future_labels = forecast_result["future_labels"]
    predictions   = forecast_result["predictions"]

    fig = go.Figure()

    # ── Actual Revenue Line ───────────────────────────────
    fig.add_trace(go.Scatter(
        x    = actual_labels,
        y    = df["revenue"].tolist(),
        mode = "lines+markers",
        name = "Actual Revenue",
        line = dict(color=GOLD, width=2.5),
        marker = dict(
            color = GOLD_LIGHT,
            size  = 8,
            line  = dict(color="#080C10", width=1)
        ),
        fill      = "tozeroy",
        fillcolor = "rgba(201,168,76,0.08)",
    ))

    # ── Forecast Line ─────────────────────────────────────
    # Connect last actual to first forecast
    connect_x = [actual_labels[-1]] + future_labels
    connect_y = [df["revenue"].iloc[-1]] + predictions

    fig.add_trace(go.Scatter(
        x    = connect_x,
        y    = connect_y,
        mode = "lines+markers",
        name = "Forecasted Revenue",
        line = dict(
            color = GREEN,
            width = 2.5,
            dash  = "dot"
        ),
        marker = dict(
            color  = GREEN,
            size   = 8,
            symbol = "diamond",
            line   = dict(color="#080C10", width=1)
        ),
        fill      = "tozeroy",
        fillcolor = "rgba(46,204,113,0.05)",
    ))

    # ── Vertical Divider ──────────────────────────────────
    fig.add_vline(
        x          = actual_labels[-1],
        line_width = 1.5,
        line_dash  = "dash",
        line_color = "rgba(201,168,76,0.4)",
        annotation_text = "Forecast Start",
        annotation_font_color = GOLD,
        annotation_font_size  = 10,
    )

    fig.update_layout(
        **LAYOUT,
        title  = "Revenue Forecast",
        xaxis  = dict(
            gridcolor  = "rgba(255,255,255,0.05)",
            tickangle  = -30,
        ),
        yaxis  = dict(
            gridcolor  = "rgba(255,255,255,0.05)",
            tickprefix = "₹",
        ),
        legend = dict(
            bgcolor     = "rgba(0,0,0,0)",
            bordercolor = "rgba(201,168,76,0.2)",
            borderwidth = 1,
        ),
        hovermode = "x unified",
    )

    return fig


def forecast_summary_text(forecast_result: dict) -> str:
    """
    Generate text summary of forecast for LLM context.
    """
    if "error" in forecast_result:
        return f"Forecasting error: {forecast_result['error']}"

    predictions = forecast_result["predictions"]
    labels      = forecast_result["future_labels"]
    growth      = forecast_result["growth_rate"]
    accuracy    = forecast_result["accuracy"]
    next_val    = forecast_result["next_predicted"]
    last_actual = forecast_result["last_actual"]

    trend = "upward 📈" if growth > 0 else "downward 📉"

    lines = [
        f"REVENUE FORECAST ANALYSIS:",
        f"Model Accuracy: {accuracy}%",
        f"Last Actual Revenue: ₹{last_actual:,.0f}",
        f"Next Period Prediction: ₹{next_val:,.0f}",
        f"Overall Trend: {trend} ({growth:+.1f}%)",
        f"",
        f"Period-wise Predictions:",
    ]
    for label, pred in zip(labels, predictions):
        lines.append(f"  {label}: ₹{pred:,.0f}")

    return "\n".join(lines)