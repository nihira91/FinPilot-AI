
import os
import warnings
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types
from rag.pipeline import rag_query, format_context
from utils.forecasting import forecast_revenue, forecast_summary_text

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


def check_if_forecast_requested(query: str) -> bool:
    """
    Check if user is asking for forecast/prediction.
    Returns True if forecast-related keywords detected.
    """
    forecast_keywords = [
        'forecast', 'predict', 'projection', 'future',
        'next quarter', 'next month', 'next period', 'next year',
        'trend', 'growth rate', 'expected', 'estimate'
    ]
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in forecast_keywords)


def validate_response_against_metrics(response: str, metrics: dict, query: str = "") -> str:
    """
    Validate that LLM response doesn't introduce hallucinated data.
    Ensures only computed metrics are used.
    """
    if not metrics or not response:
        return response
    
    hallucination_warnings = []
    
    # If no metrics were computed but response claims specific numbers
    has_numeric_metrics = any(isinstance(v, (int, float)) and v > 0 for v in metrics.values())
    
    if not has_numeric_metrics:
        if any(keyword in response.lower() for keyword in ['$', 'revenue', 'profit', 'expenses', 'costs', 'income']):
            hallucination_warnings.append("\n⚠️ WARNING: Financial numbers claimed but no CSV metrics were computed. Using document knowledge only.")
    
    # Check if forecast is being included when not requested
    if "forecast" in response.lower() and not check_if_forecast_requested(query):
        hallucination_warnings.append("\n⚠️ NOTE: Forecast mentioned but not requested. Forecast only requested by user.")
    
    if hallucination_warnings:
        return response + "\n" + "".join(hallucination_warnings)
    
    return response


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
    Handles dataset columns like quarter/revenue/cogs/gross_profit/operating_expenses.

    Args:
        df: DataFrame with financial data
        column_mapping: Dict mapping specific columns to use
    """
    metrics = {}

    if df is None or df.empty:
        return {"error": "No financial data available"}

    df = df.copy()
    if column_mapping is None:
        column_mapping = {}

    # Slow-fallback: infer standard financial columns
    revenue_col = column_mapping.get("revenue", None)
    if revenue_col is None:
        for candidate in ["revenue", "sales_amount", "total_revenue"]:
            if candidate in df.columns:
                revenue_col = candidate
                break

    cogs_col = column_mapping.get("cogs", None)
    if cogs_col is None:
        for candidate in ["cogs", "cost_of_goods_sold", "costs"]:
            if candidate in df.columns:
                cogs_col = candidate
                break

    operating_expenses_col = column_mapping.get("operating_expenses", None)
    if operating_expenses_col is None:
        for candidate in ["operating_expenses", "op_expenses", "opex"]:
            if candidate in df.columns:
                operating_expenses_col = candidate
                break

    marketing_col = column_mapping.get("marketing_spend", None)
    if marketing_col is None and "marketing_spend" in df.columns:
        marketing_col = "marketing_spend"

    rd_col = column_mapping.get("rd_expense", None)
    if rd_col is None and "rd_expense" in df.columns:
        rd_col = "rd_expense"

    net_income_col = column_mapping.get("net_income", None)
    if net_income_col is None and "net_income" in df.columns:
        net_income_col = "net_income"

    profit_margin_col = column_mapping.get("profit_margin", None)
    if profit_margin_col is None and "profit_margin" in df.columns:
        profit_margin_col = "profit_margin"

    employee_col = column_mapping.get("employee_count", None)
    if employee_col is None and "employee_count" in df.columns:
        employee_col = "employee_count"

    # Safe numeric conversion for all known financial columns
    num_cols = [revenue_col, cogs_col, operating_expenses_col, marketing_col, rd_col, net_income_col, profit_margin_col, employee_col]
    for col in set([c for c in num_cols if c is not None]):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Core revenue/costs metrics
    if revenue_col and revenue_col in df.columns:
        revenue = df[revenue_col].dropna()
        if not revenue.empty:
            metrics["total_revenue"] = float(revenue.sum())
            metrics["average_revenue"] = float(revenue.mean())
            metrics["revenue_count"] = int(revenue.count())

    if cogs_col and cogs_col in df.columns:
        cogs = df[cogs_col].dropna()
        if not cogs.empty:
            metrics["total_cogs"] = float(cogs.sum())
            metrics["average_cogs"] = float(cogs.mean())

    if operating_expenses_col and operating_expenses_col in df.columns:
        opex = df[operating_expenses_col].dropna()
        if not opex.empty:
            metrics["total_operating_expenses"] = float(opex.sum())
            metrics["average_operating_expenses"] = float(opex.mean())

    if marketing_col and marketing_col in df.columns:
        mar = df[marketing_col].dropna()
        if not mar.empty:
            metrics["total_marketing_spend"] = float(mar.sum())

    if rd_col and rd_col in df.columns:
        rnd = df[rd_col].dropna()
        if not rnd.empty:
            metrics["total_rd_expense"] = float(rnd.sum())

    if net_income_col and net_income_col in df.columns:
        ni = df[net_income_col].dropna()
        if not ni.empty:
            metrics["total_net_income"] = float(ni.sum())
            metrics["average_net_income"] = float(ni.mean())

    # Gross profit: use input if present, else compute revenue - cogs
    if "gross_profit" in df.columns:
        gp = pd.to_numeric(df["gross_profit"], errors="coerce").dropna()
        if not gp.empty:
            metrics["total_gross_profit"] = float(gp.sum())
            metrics["average_gross_profit"] = float(gp.mean())
    elif "total_revenue" in metrics and "total_cogs" in metrics:
        metrics["total_gross_profit"] = float(metrics["total_revenue"] - metrics["total_cogs"])

    # net income fallback if missing
    if "total_net_income" not in metrics and "total_revenue" in metrics and "total_operating_expenses" in metrics:
        metrics["total_net_income"] = float(metrics["total_revenue"] - metrics["total_operating_expenses"] - metrics.get("total_cogs", 0))

    # profit margin calculations
    if profit_margin_col and profit_margin_col in df.columns:
        pm = df[profit_margin_col].dropna()
        if not pm.empty:
            metrics["average_profit_margin_pct"] = float(pm.mean())
    elif "total_gross_profit" in metrics and "total_revenue" in metrics and metrics["total_revenue"] != 0:
        metrics["calculated_profit_margin_pct"] = float((metrics["total_gross_profit"] / metrics["total_revenue"]) * 100)

    # per employee metrics
    if employee_col and employee_col in df.columns and "total_revenue" in metrics:
        emp = df[employee_col].dropna()
        if not emp.empty and emp.sum() != 0:
            metrics["revenue_per_employee"] = float(metrics["total_revenue"] / emp.mean())
            if "total_net_income" in metrics:
                metrics["net_income_per_employee"] = float(metrics["total_net_income"] / emp.mean())

    # trend by quarter if exists
    quarter_col = column_mapping.get("quarter", None)
    if quarter_col is None:
        for qcol in ["quarter", "period", "month", "date"]:
            if qcol in df.columns:
                quarter_col = qcol
                break

    if quarter_col and quarter_col in df.columns and "total_revenue" in metrics:
        try:
            grouped = df.groupby(quarter_col)[revenue_col].sum()
            metrics["quarterly_revenue"] = {str(k): float(v) for k, v in grouped.items()}
            if len(grouped) >= 2:
                first = grouped.iloc[0]
                last = grouped.iloc[-1]
                metrics["quarter_over_quarter_growth_pct"] = float(((last - first)/abs(first) * 100) if first != 0 else 0)
        except Exception:
            pass

    # 2. Auto-detect and sum all cost columns
    cost_cols = detect_cost_columns(df)
    if cost_cols:
        metrics["cost_breakdown"] = {}
        total_costs = 0
        for col in cost_cols:
            total = float(df[col].sum())
            metrics["cost_breakdown"][col] = total
            total_costs += total
        metrics["total_cost_sum"] = total_costs

    # 3. Optional budget vs actual analysis remains
    if "Budget/Actual" in df.columns or "Type" in df.columns or "Category" in df.columns:
        budget_actual_col = next((col for col in ["Budget/Actual", "Type", "Category"] if col in df.columns), None)
        if budget_actual_col is not None:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                budget_data = df[df[budget_actual_col].astype(str).str.lower() == "budget"]
                actual_data = df[df[budget_actual_col].astype(str).str.lower() == "actual"]

            numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
            if not budget_data.empty and not actual_data.empty and len(numeric_cols) > 0:
                budget_total = budget_data[numeric_cols].sum().sum()
                actual_total = actual_data[numeric_cols].sum().sum()
                variance = float(actual_total - budget_total)
                variance_pct = float((variance / budget_total * 100) if budget_total != 0 else 0)

                metrics["budget_vs_actual"] = {
                    "budget_total": float(budget_total),
                    "actual_total": float(actual_total),
                    "variance": variance,
                    "variance_percentage": variance_pct
                }

    # 4. Date-based trends if available
    date_col = next((col for col in df.columns if col.lower() in ['quarter', 'month', 'date', 'period']), None)
    if date_col and revenue_col in df.columns:
        try:
            if date_col in ['month', 'date']:
                freq = 'M'
            else:
                freq = None

            by_date = df.groupby(date_col)[revenue_col].sum()
            metrics["time_series_revenue"] = {str(k): float(v) for k, v in by_date.items()}
            metrics["revenue_trend_slope"] = float(np.polyfit(np.arange(len(by_date)), by_date.values, 1)[0]) if len(by_date) > 1 else 0.0
        except Exception:
            pass

    # 5. Column-level summary for all columns
    metrics["column_summary"] = {}
    for col in df.columns:
        summary = {
            "dtype": str(df[col].dtype),
            "missing_count": int(df[col].isna().sum()),
            "unique_count": int(df[col].nunique(dropna=True))
        }
        if pd.api.types.is_numeric_dtype(df[col]):
            num = pd.to_numeric(df[col], errors='coerce').dropna()
            if not num.empty:
                summary.update({
                    "total": float(num.sum()),
                    "mean": float(num.mean()),
                    "median": float(num.median()),
                    "std": float(num.std(ddof=0)),
                    "min": float(num.min()),
                    "max": float(num.max())
                })
        else:
            top = df[col].dropna().astype(str).value_counts().head(5)
            summary["top_values"] = [{"value": int(v) if v.isdigit() else v, "count": int(c)} for v, c in top.items()]

        metrics["column_summary"][col] = summary

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


def run(query: str, df: pd.DataFrame = None, column_mapping: dict = None, forecast_column: str = None, model_type: str = "polynomial") -> dict:
    """
    Main entry point for Financial Analyst Agent.
    Called by Orchestrator whenever financial analysis is needed.

    Args:
        query : question from Orchestrator
        df    : optional DataFrame with financial data
        column_mapping : dict mapping {"revenue": col_name, "cogs": col_name, "expenses": col_name}
        forecast_column : specific column to forecast (auto-detected if None)
        model_type : which forecasting model to use ("polynomial", "exponential")

    Returns:
        {
          "agent"    : "Financial Analyst",
          "query"    : original query,
          "metrics"  : computed financial metrics,
          "forecast_data": ML forecast data,
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

    # Step 1: Check if CSV data provided FIRST (takes absolute priority)
    has_csv_data = df is not None and not df.empty
    print(f"[Financial Agent] CSV data available: {has_csv_data}")

    # Step 2: ONLY retrieve RAG if NO CSV data is provided
    # This prevents stale ChromaDB data from interfering with fresh uploads
    context = "No document context - CSV data is primary source."
    chunks = []
    
    if not has_csv_data:
        # Only use RAG if no CSV data provided
        print(f"[Financial Agent] No CSV data. Attempting RAG retrieval...")
        try:
            chunks = rag_query("financial_reports", query, top_k=5)
            context = format_context(chunks) if chunks else "No document context available."
        except Exception as e:
            print(f"[Financial Agent] RAG query error: {str(e)}")
            context = "No document context available."
    else:
        print(f"[Financial Agent] CSV data provided. Skipping RAG to avoid stale data interference.")
    
    context = str(context)  # Force to string

    # Step 3: Pandas analysis - compute metrics from CSV if provided
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

    # Step 3: Revenue Forecast (ONLY if user requests it)
    forecast_text = ""
    forecast_data = None
    should_forecast = check_if_forecast_requested(query)
    
    if should_forecast and df is not None and not df.empty:
        try:
            print(f"[Financial Agent] User requested forecast. Attempting forecast for column: {forecast_column}")
            print(f"[Financial Agent] Using model: {model_type}")
            
            forecast_data = forecast_revenue(df, periods=4, column_to_forecast=forecast_column, model_type=model_type)
            
            if "error" in forecast_data:
                print(f"[Financial Agent] Forecast error: {forecast_data['error']}")
                forecast_text = f"Forecast note: {forecast_data['error']}"
            else:
                forecast_text = forecast_summary_text(forecast_data)
                print(f"[Financial Agent] Forecast successful - accuracy: {forecast_data.get('accuracy')}%")
        except Exception as e:
            print(f"[Financial Agent] Exception computing forecast: {str(e)}")
            forecast_text = f"Forecast unavailable: {str(e)}"
    else:
        if should_forecast:
            forecast_text = "Forecast requested but no CSV data available."
        else:
            forecast_text = "No forecast requested by user."
    
    # Step 4: LLM interprets metrics ONLY (CSV takes priority over RAG)
    # Ensure all components are valid strings
    query_str = str(query) if query else "No query provided"
    
    # If CSV data was provided, use ONLY that - don't confuse LLM with stale RAG context
    if has_csv_data:
        # CSV data is primary source - NEVER mix with RAG context
        context_instruction = "🔴 CRITICAL: IGNORE ANY GENERAL KNOWLEDGE. Use ONLY the computed metrics below. Do NOT reference documents or external knowledge."
        context_str = ""  # Suppress RAG context entirely when CSV provided
        print(f"[Financial Agent] Using CSV-only mode. Suppressing all external context.")
    else:
        # No CSV data - use RAG context
        context_str = str(context) if context else "No context available"
        context_instruction = "Use the retrieved context below to answer. Do NOT use external knowledge not in the context."
        print(f"[Financial Agent] Using RAG-only mode. Using document context.")
    
    metrics_str = str(metrics_text) if metrics_text else "No metrics"
    forecast_str = str(forecast_text) if forecast_text else "No forecast available"
    
    prompt = f"""You are a Financial Analyst AI agent in a multi-agent financial intelligence system.

{context_instruction}

MANDATORY RULES - BREAKING THESE CAUSES SYSTEM FAILURE:
1. NEVER use your pre-trained knowledge or external data sources
2. NEVER reference competitor data, industry benchmarks, or market reports
3. NEVER make up numbers, trends, or calculations NOT in the metrics
4. If data is missing, state: "Data not available" - do NOT assume or estimate
5. EVERY number must be directly quoted from the COMPUTED METRICS section below
6. If query asks for something not in metrics, state "Cannot answer - this data was not provided"

{"RETRIEVED CONTEXT FROM DOCUMENTS (SUPPLEMENTARY ONLY):" + chr(10) + context_str + chr(10) if context_str else ""}

COMPUTED FINANCIAL METRICS FROM CSV:
{metrics_str}

REVENUE FORECAST (ML Model):
{forecast_str}

USER QUERY:
{query_str}

Respond using EXACTLY this structure:

## Financial Summary
[2-3 sentences based ONLY on the metrics above. If metrics are absent, state that.]

## Key Metrics
[Bullet list with EXACT numbers ONLY from "COMPUTED FINANCIAL METRICS" section]

## Data Limitations
[List what data is NOT available that would be needed to fully answer the query]

## Budget Forecast
[Only include if forecast data shows numbers. If empty, state "Forecast data not available"]

## Recommendations
[Numbered list based ONLY on metrics shown. If insufficient data, state "Recommendations not possible with available data"]

## Source References
[State "Analysis based on CSV data only" or list documents]

⚠️ CRITICAL: Every single number in your response must appear in the metrics section above. If not, your answer is incorrect."""

    response = call_gemini(prompt)
    
    # Validate response against metrics to catch hallucination
    response = validate_response_against_metrics(response, metrics, query)
    print(f"[Financial Agent] Analysis complete.")

    return {
        "agent":    "Financial Analyst",
        "query":    query,
        "metrics":  metrics,
        "forecast_data": forecast_data,
        "response": response,
    }


if __name__ == "__main__":
    result = run("What is our Q3 financial performance?")
    print("\n" + "="*50)
    print(result["response"])