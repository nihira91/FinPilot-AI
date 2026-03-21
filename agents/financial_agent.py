# ─────────────────────────────────────────────────────────────────────────────
# financial_agent.py — Financial Analyst Agent
#
# PURPOSE : Analyse financial data using Pandas and RAG pipeline,
#           then interpret results using Gemini LLM.
#
# HOW ORCHESTRATOR USES THIS:
#   from agents.financial_agent import run
#   result = run("What is our Q3 profit performance?")
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


def detect_cost_columns(df: pd.DataFrame) -> list:
    """
    Automatically detect columns that contain cost/expense data.
    Looks for numeric columns with 'cost', 'expense', 'spending' in name.
    """
    cost_keywords = ['cost', 'expense', 'spending', 'amount']
    cost_cols = []
    
    for col in df.columns:
        if df[col].dtype in ['float64', 'int64']:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in cost_keywords):
                cost_cols.append(col)
    
    return cost_cols


def compute_detailed_metrics(df: pd.DataFrame, column_mapping: dict = None) -> dict:
    """
    Compute comprehensive financial metrics from a DataFrame.
    Handles multiple cost types, budget vs actual, and monthly trends.
    
    Args:
        df: DataFrame with financial data
        column_mapping: Dict mapping specific columns to use
    """
    metrics = {}
    
    # 1. Traditional metrics if mapped
    if column_mapping is None:
        column_mapping = {}
    
    revenue_col = column_mapping.get("revenue")
    if revenue_col and revenue_col in df.columns:
        metrics["total_revenue"] = float(df[revenue_col].sum())
    
    cogs_col = column_mapping.get("cogs")
    if cogs_col and cogs_col in df.columns:
        metrics["total_cogs"] = float(df[cogs_col].sum())
    
    expenses_col = column_mapping.get("expenses")
    if expenses_col and expenses_col in df.columns:
        metrics["total_expenses"] = float(df[expenses_col].sum())
    
    # 2. Auto-detect and sum all cost columns
    cost_cols = detect_cost_columns(df)
    if cost_cols:
        metrics["cost_breakdown"] = {}
        total_costs = 0
        for col in cost_cols:
            col_sum = float(df[col].sum())
            metrics["cost_breakdown"][col] = col_sum
            total_costs += col_sum
        metrics["total_cost_sum"] = total_costs
    
    # 3. Budget vs Actual analysis
    if "Budget/Actual" in df.columns or "Type" in df.columns or "Category" in df.columns:
        budget_actual_col = next((col for col in ["Budget/Actual", "Type", "Category"] if col in df.columns), None)
        if budget_actual_col:
            budget_data = df[df[budget_actual_col].str.lower() == "budget"]
            actual_data = df[df[budget_actual_col].str.lower() == "actual"]
            
            if not budget_data.empty and not actual_data.empty:
                numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
                budget_total = budget_data[numeric_cols].sum().sum()
                actual_total = actual_data[numeric_cols].sum().sum()
                variance = actual_total - budget_total
                variance_pct = (variance / budget_total * 100) if budget_total != 0 else 0
                
                metrics["budget_vs_actual"] = {
                    "budget_total": float(budget_total),
                    "actual_total": float(actual_total),
                    "variance": float(variance),
                    "variance_percentage": float(variance_pct)
                }
    
    # 4. Monthly trend if there's a Month/Date column
    month_col = next((col for col in df.columns if col.lower() in ['month', 'date', 'period']), None)
    if month_col:
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
        monthly_totals = df.groupby(month_col)[numeric_cols].sum().sum(axis=1)
        metrics["monthly_trend"] = {
            "months": list(monthly_totals.index),
            "totals": [float(x) for x in monthly_totals.values],
            "average_monthly": float(monthly_totals.mean()),
            "highest_month": str(monthly_totals.idxmax()),
            "lowest_month": str(monthly_totals.idxmin())
        }
    
    # 5. Calculate gross profit and net income if revenue available
    if "total_revenue" in metrics:
        total_expenses_sum = metrics.get("total_cost_sum", metrics.get("total_expenses", 0))
        metrics["gross_profit"] = float(metrics["total_revenue"] - total_expenses_sum)
        metrics["net_income"] = metrics["gross_profit"]
    
    return metrics


def compute_metrics(df: pd.DataFrame, column_mapping: dict = None) -> dict:
    """
    Backward compatible wrapper that uses detailed metrics computation.
    
    Args:
        df: DataFrame with financial data
        column_mapping: Dict mapping metric names to column names
    """
    detailed = compute_detailed_metrics(df, column_mapping=column_mapping)
    
    # Return simplified version for backward compatibility
    simple = {
        "total_revenue": detailed.get("total_revenue", 0.0),
        "total_cogs": detailed.get("total_cogs", 0.0),
        "total_expenses": detailed.get("total_cost_sum", detailed.get("total_expenses", 0.0)),
        "gross_profit": detailed.get("gross_profit", 0.0),
        "net_income": detailed.get("net_income", 0.0),
    }
    
    # Add detailed info if available
    if "cost_breakdown" in detailed:
        simple["cost_breakdown"] = detailed["cost_breakdown"]
    if "budget_vs_actual" in detailed:
        simple["budget_vs_actual"] = detailed["budget_vs_actual"]
    if "monthly_trend" in detailed:
        simple["monthly_trend"] = detailed["monthly_trend"]
    
    return simple


def run(query: str, df: pd.DataFrame = None, column_mapping: dict = None) -> dict:
    """
    Main entry point for Financial Analyst Agent.
    Called by Orchestrator whenever financial analysis is needed.

    Args:
        query : question from Orchestrator
        df    : optional DataFrame with financial data
        column_mapping : dict mapping {"revenue": col_name, "cogs": col_name, "expenses": col_name}

    Returns:
        {
          "agent"    : "Financial Analyst",
          "query"    : original query,
          "metrics"  : computed financial metrics,
          "response" : LLM full analysis
        }
    """
    # ── Ensure query is valid string ──
    if query is None:
        raise ValueError("Query is None in Financial Agent")
    query = str(query).strip()
    
    if not query:
        raise ValueError("Query is empty in Financial Agent")
    
    print(f"\n[Financial Agent] Query received: {query}")

    # Step 1: RAG retrieval from financial_reports collection
    try:
        chunks  = rag_query("financial_reports", query, top_k=5)
    except Exception as e:
        print(f"[Financial Agent] RAG query error: {str(e)}")
        chunks = []
    
    context = format_context(chunks) if chunks else "No document context available."
    
    # Ensure context is a valid string
    if not context or context is None:
        context = "No document context available."
    context = str(context)  # Force to string

    # Step 2: Pandas analysis only if CSV data provided
    metrics = {}
    metrics_text = "No financial data provided. Analyze from documents only."
    
    if df is not None and not df.empty:
        print(f"[Financial Agent] Using CSV data: {df.shape[0]} rows")
        try:
            metrics = compute_metrics(df, column_mapping=column_mapping)
            
            # Format metrics for LLM with details
            metrics_lines = []
            
            # Basic metrics
            for key in ["total_revenue", "total_cogs", "total_expenses", "gross_profit", "net_income"]:
                if key in metrics and isinstance(metrics.get(key), (int, float)) and metrics[key] != 0:
                    metrics_lines.append(f"  {key.replace('_', ' ').title()}: {safe_format_value(metrics[key])}")
            
            # Cost breakdown
            if "cost_breakdown" in metrics and isinstance(metrics["cost_breakdown"], dict):
                metrics_lines.append("\nCost Breakdown:")
                for cost_type, amount in metrics["cost_breakdown"].items():
                    if isinstance(amount, (int, float)) and amount != 0:
                        metrics_lines.append(f"  {cost_type}: {safe_format_value(amount)}")
            
            # Budget vs Actual
            if "budget_vs_actual" in metrics and isinstance(metrics["budget_vs_actual"], dict):
                bva = metrics["budget_vs_actual"]
                metrics_lines.append("\nBudget vs Actual:")
                if "budget_total" in bva and isinstance(bva.get("budget_total"), (int, float)):
                    metrics_lines.append(f"  Budget Total: {safe_format_value(bva['budget_total'])}")
                if "actual_total" in bva and isinstance(bva.get("actual_total"), (int, float)):
                    metrics_lines.append(f"  Actual Total: {safe_format_value(bva['actual_total'])}")
                if "variance" in bva and isinstance(bva.get("variance"), (int, float)):
                    metrics_lines.append(f"  Variance: {safe_format_value(bva['variance'])}")
            
            # Monthly trend
            if "monthly_trend" in metrics and isinstance(metrics["monthly_trend"], dict):
                trend = metrics["monthly_trend"]
                metrics_lines.append("\nMonthly Trend:")
                if "average_monthly" in trend and isinstance(trend.get("average_monthly"), (int, float)):
                    metrics_lines.append(f"  Average Monthly: {safe_format_value(trend['average_monthly'])}")
                if "highest_month" in trend and trend.get("highest_month"):
                    metrics_lines.append(f"  Highest Month: {safe_format_value(trend['highest_month'])}")
                if "lowest_month" in trend and trend.get("lowest_month"):
                    metrics_lines.append(f"  Lowest Month: {safe_format_value(trend['lowest_month'])}")
            
            metrics_text = "\n".join(metrics_lines) if metrics_lines else "Metrics computed from CSV data."
        except Exception as e:
            print(f"[Financial Agent] Error computing metrics: {str(e)}")
            metrics_text = "Metrics available from CSV data."
    else:
        print("[Financial Agent] No CSV data provided. Analyzing from PDF context only.")
        metrics = {}
        metrics_text = "No financial data provided. Analyze from documents only."

    # Step 3: LLM interprets RAG context + metrics
    # Ensure all components are valid strings
    query_str = str(query) if query else "No query provided"
    context_str = str(context) if context else "No context available"
    metrics_str = str(metrics_text) if metrics_text else "No metrics"
    
    prompt = f"""You are a Financial Analyst AI agent in a
multi-agent financial intelligence system.

RETRIEVED CONTEXT FROM DOCUMENTS:
{context_str}

COMPUTED FINANCIAL METRICS:
{metrics_str}

QUERY: {query_str}

Respond using EXACTLY this structure:
## Financial Summary
[2-3 sentence overview]

## Key Metrics
[Bullet list of important numbers]

## Budget Forecast
[Predicted revenue, expenses, profit trends]

## Recommendations
[Numbered list of specific actions]

## Source References
[List of documents used]"""

    response = call_gemini(prompt)
    print(f"[Financial Agent] Analysis complete.")

    return {
        "agent":    "Financial Analyst",
        "query":    query,
        "metrics":  metrics,
        "response": response,
    }


if __name__ == "__main__":
    result = run("What is our Q3 financial performance?")
    print("\n" + "="*50)
    print(result["response"])