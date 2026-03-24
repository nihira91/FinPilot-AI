# ─────────────────────────────────────────────────────────────
# sales_agent.py — Hallucination-Free Sales Agent (Production)
# ─────────────────────────────────────────────────────────────

import os
import json
import re
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
MODEL_ID = "gemini-2.5-flash"


# ─────────────────────────────────────────────────────────────
# 🔹 GEMINI CALL
# ─────────────────────────────────────────────────────────────
def call_gemini(prompt: str) -> str:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,  # LOW = less hallucination
            max_output_tokens=4096,
        )
    )
    return response.text.strip()


# ─────────────────────────────────────────────────────────────
# 🔹 FORECAST CHECK
# ─────────────────────────────────────────────────────────────
def is_forecast_query(query: str) -> bool:
    forecast_keywords = [
        "forecast", "predict", "prediction",
        "next month", "next quarter", "future"
    ]
    q = query.lower()
    return any(k in q for k in forecast_keywords)


# ─────────────────────────────────────────────────────────────
# 🔹 COLUMN DETECTION
# ─────────────────────────────────────────────────────────────
def detect_sales_column(df: pd.DataFrame) -> str:
    for col in df.columns:
        if df[col].dtype in ["int64", "float64"]:
            if any(k in col.lower() for k in ["sales", "revenue", "amount"]):
                return col
    return None


# ─────────────────────────────────────────────────────────────
# 🔹 CORE COMPUTATION (PANDAS ONLY)
# ─────────────────────────────────────────────────────────────
def compute_metrics(df: pd.DataFrame, allow_forecast=False) -> dict:
    col = detect_sales_column(df)
    if not col:
        return {"error": "No sales column found"}

    s = df[col].astype(float)

    metrics = {
        "column": col,
        "count": int(len(s)),
        "total": float(s.sum()),
        "mean": float(s.mean()),
        "median": float(s.median()),
        "min": float(s.min()),
        "max": float(s.max()),
        "std": float(s.std())
    }

    # Growth
    if len(s) >= 2:
        growth = (s.iloc[-1] - s.iloc[0]) / max(abs(s.iloc[0]), 1e-9)
        metrics["growth_rate"] = float(growth)
        metrics["growth_percent"] = float(growth * 100)

    # Forecast ONLY if explicitly requested
    if allow_forecast:
        x = np.arange(len(s))
        slope, intercept = np.polyfit(x, s.values, 1)

        next_val = slope * len(s) + intercept

        y_pred = slope * x + intercept
        ss_res = np.sum((s.values - y_pred) ** 2)
        ss_tot = np.sum((s.values - s.mean()) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        metrics["forecast"] = float(next_val)
        metrics["forecast_confidence"] = float(r2)

    # Optional grouping
    for col in df.columns:
        if col.lower() in ["month", "date", "period", "region", "category"]:
            grouped = df.groupby(col)[metrics["column"]].sum()
            metrics["grouped"] = {
                str(k): float(v) for k, v in grouped.items()
            }
            metrics["best_group"] = str(grouped.idxmax())
            metrics["worst_group"] = str(grouped.idxmin())
            break

    return metrics


# ─────────────────────────────────────────────────────────────
# 🔹 VALIDATION (STRICT)
# ─────────────────────────────────────────────────────────────
def validate_response(response: str, metrics: dict) -> str:
    allowed_numbers = set()

    def extract_numbers(val):
        return re.findall(r"\d+\.?\d*", str(val))

    for v in metrics.values():
        if isinstance(v, (int, float)):
            allowed_numbers.update(extract_numbers(v))
        elif isinstance(v, dict):
            for sub in v.values():
                allowed_numbers.update(extract_numbers(sub))

    response_numbers = re.findall(r"\d+\.?\d*", response)

    invalid = [n for n in response_numbers if n not in allowed_numbers]

    if invalid:
        return response + f"\n\n❌ INVALID NUMBERS DETECTED: {invalid}"

    return response


# ─────────────────────────────────────────────────────────────
# 🔹 MAIN RUN FUNCTION
# ─────────────────────────────────────────────────────────────
def run(query: str, df: pd.DataFrame) -> dict:

    if df is None or df.empty:
        raise ValueError("CSV data required")

    allow_forecast = is_forecast_query(query)

    metrics = compute_metrics(df, allow_forecast=allow_forecast)

    if "error" in metrics:
        return {"response": metrics["error"], "metrics": metrics}

    metrics_json = json.dumps(metrics, indent=2)

    # 🔥 STRICT PROMPT
    prompt = f"""
You are a STRICT data analyst.

You MUST ONLY use the JSON below.

DATA:
{metrics_json}

RULES:
- Do NOT invent numbers
- Do NOT estimate
- Do NOT add trends not present
- Do NOT predict unless "forecast" exists
- Every number MUST come from JSON

OUTPUT:

## Sales Summary
Brief factual summary

## Key Metrics
- Total
- Mean
- Median
- Min / Max

## Insights
Only direct observations

## Limitations
Mention missing data if needed
"""

    response = call_gemini(prompt)

    # 🔥 VALIDATION
    response = validate_response(response, metrics)

    return {
        "agent": "Sales Analyst",
        "query": query,
        "metrics": metrics,
        "response": response
    }

