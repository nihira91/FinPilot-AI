

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


def compute_detailed_trends(df: pd.DataFrame, column_mapping: dict = None) -> dict:
    """
    Compute comprehensive sales trends with auto-detection of sales columns.
    Handles dataset schema with month/product/region/sales_amount/units_sold etc.
    """
    trends = {}

    if df is None or df.empty:
        return {"error": "No sales data available"}

    if column_mapping is None:
        column_mapping = {}

    # Detect primary numbers
    sales_col = column_mapping.get("sales", None)
    candidates = ["sales_amount", "sales", "revenue", "amount"]
    if sales_col is None:
        sales_col = next((c for c in candidates if c in df.columns), None)

    if sales_col is None:
        detected = detect_sales_columns(df)
        if detected:
            sales_col = detected[0]
        else:
            return {"error": "No sales/revenue columns found"}

    # Ensure numeric and handle non-numeric safely
    df = df.copy()
    df[sales_col] = pd.to_numeric(df[sales_col], errors="coerce")
    sales_series = df[sales_col].dropna()

    if sales_series.empty:
        return {"error": f"Sales column '{sales_col}' has no numeric values"}

    trends["primary_metric"] = sales_col
    trends["count"] = int(sales_series.size)
    trends["mean"] = float(sales_series.mean())
    trends["median"] = float(sales_series.median())
    trends["std"] = float(sales_series.std(ddof=0))
    trends["min"] = float(sales_series.min())
    trends["max"] = float(sales_series.max())
    trends["total"] = float(sales_series.sum())

    # Period trend using month/date if available
    period_col = column_mapping.get("period", None)
    if period_col is None:
        for option in ["month", "date", "period"]:
            if option in df.columns:
                period_col = option
                break

    if period_col in df.columns:
        try:
            df[period_col + "__parsed"] = pd.to_datetime(df[period_col], errors="coerce")
            if df[period_col + "__parsed"].notna().any():
                growth_frame = df.dropna(subset=[period_col + "__parsed", sales_col])
                growth_frame = growth_frame.sort_values(period_col + "__parsed")
                if not growth_frame.empty:
                    first_val = pd.to_numeric(growth_frame[sales_col], errors="coerce").iloc[0]
                    last_val = pd.to_numeric(growth_frame[sales_col], errors="coerce").iloc[-1]
                    trends["period_growth_rate"] = float((last_val - first_val) / max(abs(first_val), 1e-9))
                    trends["period_growth_percent"] = float(trends["period_growth_rate"] * 100)
                    # monthly breakdown
                    by_period = growth_frame.groupby(growth_frame[period_col + "__parsed"].dt.to_period("M"))[sales_col].agg(["sum", "mean", "count"])
                    trends["period_breakdown"] = {str(idx): {"total": float(r["sum"]), "average": float(r["mean"]), "count": int(r["count"])} for idx, r in by_period.iterrows()}
                    trends["best_period"] = str(by_period["sum"].idxmax())
                    trends["worst_period"] = str(by_period["sum"].idxmin())
        except Exception:
            pass

    # Numeric columns by strategy
    units_col = column_mapping.get("units", "units_sold")
    if units_col in df.columns:
        df[units_col] = pd.to_numeric(df[units_col], errors="coerce")
        units_series = df[units_col].dropna()
        if not units_series.empty:
            trends["units_sold_total"] = float(units_series.sum())
            trends["units_sold_mean"] = float(units_series.mean())

    if "total" in trends and trends.get("units_sold_total", 0) > 0:
        trends["revenue_per_unit"] = float(trends["total"] / trends["units_sold_total"])

    new_clients_col = column_mapping.get("new_clients", "new_clients")
    if new_clients_col in df.columns:
        df[new_clients_col] = pd.to_numeric(df[new_clients_col], errors="coerce")
        nc = df[new_clients_col].dropna()
        if not nc.empty:
            trends["new_clients_total"] = int(nc.sum())
            trends["new_clients_mean"] = float(nc.mean())

    churned_col = column_mapping.get("churned_clients", "churned_clients")
    if churned_col in df.columns:
        df[churned_col] = pd.to_numeric(df[churned_col], errors="coerce")
        cc = df[churned_col].dropna()
        if not cc.empty:
            trends["churned_clients_total"] = int(cc.sum())
            trends["churned_clients_mean"] = float(cc.mean())

    if "avg_deal_size" in df.columns:
        ds = pd.to_numeric(df["avg_deal_size"], errors="coerce").dropna()
        if not ds.empty:
            trends["average_deal_size"] = float(ds.mean())
    elif "revenue_per_unit" in trends:
        trends["average_deal_size"] = float(trends["revenue_per_unit"])

    if "sales_growth_pct" in df.columns:
        pct = pd.to_numeric(df["sales_growth_pct"], errors="coerce").dropna()
        if not pct.empty:
            trends["sales_growth_pct_mean"] = float(pct.mean())
            trends["sales_growth_pct_median"] = float(pct.median())

    # Regression and forecast
    try:
        x = np.arange(sales_series.size)
        coeffs = np.polyfit(x, sales_series.values, 1)
        slope, intercept = coeffs[0], coeffs[1]
        trends["slope"] = float(slope)
        trends["intercept"] = float(intercept)
        trends["next_period_prediction"] = float(slope * sales_series.size + intercept)

        y_pred = slope * x + intercept
        ss_res = np.sum((sales_series.values - y_pred) ** 2)
        ss_tot = np.sum((sales_series.values - sales_series.mean()) ** 2)
        trends["forecast_confidence"] = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0
    except Exception:
        trends["slope"] = None
        trends["intercept"] = None
        trends["next_period_prediction"] = None
        trends["forecast_confidence"] = 0.0

    # Add additional sales columns summary
    all_sales_cols = detect_sales_columns(df)
    if len(all_sales_cols) > 1:
        trends["all_sales_columns"] = {}
        for col in all_sales_cols:
            if col != sales_col:
                cnum = pd.to_numeric(df[col], errors="coerce").dropna()
                if not cnum.empty:
                    trends["all_sales_columns"][col] = {"total": float(cnum.sum()), "average": float(cnum.mean())}

    # Add full column-level diagnostics (all columns considered)
    trends["column_summary"] = {}
    for col in df.columns:
        col_info = {
            "dtype": str(df[col].dtype),
            "missing": int(df[col].isna().sum()),
            "unique": int(df[col].nunique(dropna=True)),
        }
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric = pd.to_numeric(df[col], errors="coerce").dropna()
            if not numeric.empty:
                col_info.update({
                    "mean": float(numeric.mean()),
                    "median": float(numeric.median()),
                    "std": float(numeric.std(ddof=0)),
                    "min": float(numeric.min()),
                    "max": float(numeric.max()),
                    "sum": float(numeric.sum()),
                })
        else:
            top = df[col].dropna().astype(str).value_counts().head(5)
            col_info["top_values"] = [{"value": idx, "count": int(cnt)} for idx, cnt in top.items()]

        trends["column_summary"][col] = col_info

    return trends


def compute_trends(df: pd.DataFrame, column_mapping: dict = None) -> dict:
    """
    Backward compatible wrapper using detailed trends computation.
    """
    detailed = compute_detailed_trends(df, column_mapping=column_mapping)
    
    if "error" in detailed:
        return detailed
    
    simple = {
        "count": detailed.get("count", 0),
        "mean": detailed.get("mean", 0),
        "median": detailed.get("median", 0),
        "std": detailed.get("std", 0),
        "total": detailed.get("total", 0),
    }
    
    if "period_growth_rate" in detailed:
        simple["simple_growth_rate"] = detailed["period_growth_rate"]
    if "next_period_prediction" in detailed:
        simple["next_prediction"] = detailed["next_period_prediction"]
    if "slope" in detailed:
        simple["slope"] = detailed["slope"]
    if "intercept" in detailed:
        simple["intercept"] = detailed["intercept"]
    
    if "all_sales_columns" in detailed:
        simple["sales_breakdown"] = detailed["all_sales_columns"]
    if "period_breakdown" in detailed:
        simple["period_breakdown"] = detailed["period_breakdown"]
    
    return simple


def run(query: str, df: pd.DataFrame = None, column_mapping: dict = None) -> dict:
    """
    Main entry point for Sales & Data Scientist Agent.
    Called by Orchestrator whenever sales analysis is needed.

    Args:
        query : question from Orchestrator
        df    : optional DataFrame with sales data
        column_mapping : dict mapping {"sales": col_name}

    Returns:
        {
          "agent"    : "Sales Data Scientist",
          "query"    : original query,
          "metrics"  : computed sales metrics,
          "response" : LLM full analysis
        }
    """
    # ── Ensure query is valid string ──
    if query is None:
        raise ValueError("Query is None in Sales Agent")
    query = str(query).strip()
    
    if not query:
        raise ValueError("Query is empty in Sales Agent")
    
    print(f"\n[Sales Agent] Query received: {query}")

    # Step 1: RAG retrieval from sales_reports collection
    try:
        chunks  = rag_query("sales_reports", query, top_k=5)
    except Exception as e:
        print(f"[Sales Agent] RAG query error: {str(e)}")
        chunks = []
    
    context = format_context(chunks) if chunks else "No document context available."
    
    # Ensure context is a valid string
    if not context or context is None:
        context = "No document context available."
    context = str(context)  # Force to string

    # Step 2: Pandas trend analysis only if CSV data provided
    trends = {}
    trends_text = "No sales data provided. Analyze from documents only."
    
    if df is not None and not df.empty:
        print(f"[Sales Agent] Using CSV data: {df.shape[0]} rows")
        try:
            trends = compute_trends(df, column_mapping=column_mapping)
            
            # Format trends for LLM with details
            trends_lines = []
            
            # Basic statistics
            for key in ["total", "mean", "median", "min", "max"]:
                if key in trends and isinstance(trends.get(key), (int, float)) and trends[key] != 0:
                    trends_lines.append(f"  {key.replace('_', ' ').title()}: {safe_format_value(trends[key])}")
            
            # Growth metrics
            if "simple_growth_rate" in trends and isinstance(trends.get("simple_growth_rate"), (int, float)):
                trends_lines.append(f"  Growth Rate: {trends['simple_growth_rate']*100:.1f}%")
            if "next_prediction" in trends and isinstance(trends.get("next_prediction"), (int, float)):
                trends_lines.append(f"  Next Period Prediction: {safe_format_value(trends['next_prediction'])}")
            
            # Sales breakdown by type
            if "sales_breakdown" in trends and isinstance(trends["sales_breakdown"], dict):
                trends_lines.append("\nSales Breakdown:")
                for col, data in trends["sales_breakdown"].items():
                    if isinstance(data, dict) and "total" in data:
                        trends_lines.append(f"  {col}: {safe_format_value(data['total'])}")
            
            # Period breakdown
            if "period_breakdown" in trends and isinstance(trends["period_breakdown"], dict):
                trends_lines.append("\nPeriod-wise Analysis:")
                for period, data in trends["period_breakdown"].items():
                    if isinstance(data, dict) and "total" in data:
                        trends_lines.append(f"  {period}: {safe_format_value(data['total'])}")
                if "best_period" in trends and trends["best_period"]:
                    trends_lines.append(f"  Best Period: {safe_format_value(trends['best_period'])}")
                if "worst_period" in trends and trends["worst_period"]:
                    trends_lines.append(f"  Worst Period: {safe_format_value(trends['worst_period'])}")
            
            trends_text = "\n".join(trends_lines) if trends_lines else "Trends computed from CSV data."
        except Exception as e:
            print(f"[Sales Agent] Error computing trends: {str(e)}")
            trends_text = "Trends available from CSV data."
    else:
        print("[Sales Agent] No CSV data provided. Analyzing from PDF context only.")

    # Step 3: LLM interprets RAG context + trends
    # Ensure all components are valid strings
    query_str = str(query) if query else "No query provided"
    context_str = str(context) if context else "No context available"
    trends_str = str(trends_text) if trends_text else "No trends"
    
    prompt = f"""You are a Sales Data Scientist AI agent in a
multi-agent financial intelligence system.

RETRIEVED CONTEXT FROM DOCUMENTS:
{context_str}

COMPUTED SALES METRICS:
{trends_str}

QUERY: {query_str}

Respond using EXACTLY this structure:
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

