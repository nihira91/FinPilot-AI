# ─────────────────────────────────────────────────────────────────────────────
# sales_agent.py — Sales & Data Scientist Agent
#
# PURPOSE : Analyse sales trends using Pandas/NumPy and RAG pipeline,
#           then interpret results using Gemini LLM.
#
# HOW ORCHESTRATOR USES THIS:
#   from agents.sales_agent import run
#   result = run("What are our sales trends?")
# ─────────────────────────────────────────────────────────────────────────────

import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types
from rag.pipeline import rag_query, format_context

load_dotenv()

MODEL_ID = "gemini-2.5-flash"


def safe_format_value(val):
    """Safely convert values to string, handling None and special types."""
    if val is None:
        return "N/A"
    if isinstance(val, (int, float)):
        if val == int(val):
            return f"{int(val):,}"
        return f"{val:,.2f}"
    if isinstance(val, bool):
        return str(val)
    return str(val)


def call_gemini(prompt: str, max_tokens: int = 8192) -> str:
    token = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=token)
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=max_tokens,
        )
    )
    return response.text.strip()


def detect_sales_columns(df: pd.DataFrame) -> list:
    """
    Automatically detect columns that contain sales/revenue data.
    """
    sales_keywords = ['sales', 'revenue', 'amount', 'volume', 'quantity']
    sales_cols = []
    
    for col in df.columns:
        if df[col].dtype in ['float64', 'int64']:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in sales_keywords):
                sales_cols.append(col)
    
    return sales_cols


def compute_detailed_trends(df: pd.DataFrame, column_mapping: dict = None) -> dict:
    """
    Compute comprehensive sales trends with auto-detection of sales columns.
    """
    trends = {}
    
    if column_mapping is None:
        column_mapping = {}
    
    sales_col = column_mapping.get("sales", "sales")
    
    if sales_col not in df.columns:
        detected = detect_sales_columns(df)
        if detected:
            sales_col = detected[0]
        else:
            return {"error": "No sales/revenue columns found"}
    
    series = df[sales_col].astype(float)
    trends["primary_metric"] = sales_col
    trends["count"] = int(series.size)
    trends["mean"] = float(series.mean())
    trends["median"] = float(series.median())
    trends["std"] = float(series.std())
    trends["min"] = float(series.min())
    trends["max"] = float(series.max())
    trends["total"] = float(series.sum())
    
    if series.size >= 2:
        first_val = series.iloc[0]
        last_val = series.iloc[-1]
        growth = (last_val - first_val) / max(abs(first_val), 1e-9)
        trends["period_growth_rate"] = float(growth)
        trends["period_growth_percent"] = float(growth * 100)
    
    try:
        x = np.arange(series.size)
        coeffs = np.polyfit(x, series.values, 1)
        slope, intercept = coeffs[0], coeffs[1]
        trends["slope"] = float(slope)
        trends["intercept"] = float(intercept)
        trends["next_period_prediction"] = float(slope * series.size + intercept)
        
        y_pred = slope * x + intercept
        ss_res = np.sum((series.values - y_pred) ** 2)
        ss_tot = np.sum((series.values - series.mean()) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        trends["forecast_confidence"] = float(r_squared)
    except Exception:
        trends["slope"] = None
        trends["intercept"] = None
        trends["next_period_prediction"] = None
    
    other_sales_cols = detect_sales_columns(df)
    if len(other_sales_cols) > 1:
        trends["all_sales_columns"] = {}
        for col in other_sales_cols:
            if col != sales_col:
                col_sum = float(df[col].sum())
                col_mean = float(df[col].mean())
                trends["all_sales_columns"][col] = {
                    "total": col_sum,
                    "average": col_mean
                }
    
    period_col = next((col for col in df.columns if col.lower() in ['month', 'date', 'period', 'region', 'category']), None)
    if period_col and period_col != sales_col:
        period_data = df.groupby(period_col)[sales_col].agg(['sum', 'mean', 'count'])
        trends["period_breakdown"] = {}
        for period, row in period_data.iterrows():
            trends["period_breakdown"][str(period)] = {
                "total": float(row['sum']),
                "average": float(row['mean']),
                "count": int(row['count'])
            }
        trends["best_period"] = str(period_data['sum'].idxmax())
        trends["worst_period"] = str(period_data['sum'].idxmin())
    
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
[2-3 sentence overview of sales performance]

## Trend Analysis
[Bullet list of growth, decline, anomaly patterns]

## Key Correlations
[How sales relate to external factors]

## Data-Driven Recommendations
[Numbered list of specific actions]

## Source References
[List of documents used]"""

    response = call_gemini(prompt)
    print(f"[Sales Agent] Analysis complete.")

    return {
        "agent":    "Sales Data Scientist",
        "query":    query,
        "metrics":  trends,
        "response": response,
    }


if __name__ == "__main__":
    result = run("What are our sales trends this year?")
    print("\n" + "="*50)
    print(result["response"])