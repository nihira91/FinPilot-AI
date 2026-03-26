
import os
import warnings
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types
from rag.pipeline import rag_query, format_context
from rag.vector_store import query_with_domain_filter

load_dotenv()

MODEL_ID = "gemini-2.5-flash"

# Try importing visualization - optional feature
try:
    from utils.chart_generator import create_breakdown_pie, create_category_bar, create_timeseries_line
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False


CHART_INTENT_KEYWORDS = {
    "cost": [
        "cost", "expense", "breakdown", "split", "distribution", "composition",
        "cost breakdown", "expense breakdown", "cost split", "where money goes",
        "proportion", "allocation", "spending"
    ],
    "trend": [
        "trend", "period", "quarter", "time", "over time", "temporal", "when",
        "time-series", "quarterly", "trajectory", "evolution", "pattern",
        "growth", "forecast", "progression", "movement"
    ]
}

def detect_chart_intent(query: str) -> str:
    """Detect chart intent from query using semantic keywords."""
    query_lower = query.lower()
    for intent, keywords in CHART_INTENT_KEYWORDS.items():
        if any(kw in query_lower for kw in keywords):
            print(f"[Financial Agent] Chart intent detected: {intent}")
            return intent
    return "default"


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
        pass
    
    context = str(context)  # Force to string

    # Step 3: Pandas analysis - compute metrics from CSV if provided
    metrics = {}
    metrics_text = "No financial data provided. Analyze from documents only."
    
    if df is not None and not df.empty:
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
            
            # Add column metadata
            metrics_lines.append("\n📊 AVAILABLE DATA STRUCTURE:")
            metrics_lines.append(f"  Total Rows: {df.shape[0]}")
            metrics_lines.append(f"  Total Columns: {df.shape[1]}")
            metrics_lines.append(f"  Column Names: {', '.join(df.columns.tolist())}")
            
            # Detect date range if date column exists
            date_cols = [col for col in df.columns if col.lower() in ['date', 'month', 'quarter', 'period']]
            if date_cols:
                date_col = date_cols[0]
                try:
                    df_temp = df.copy()
                    # Use explicit format for month column (Jan-22 = Jan 2022)
                    if date_col.lower() == 'month':
                        df_temp[date_col] = pd.to_datetime(df_temp[date_col], format="%b-%y", errors='coerce')
                    else:
                        df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors='coerce')
                    
                    # Filter out invalid dates
                    valid_dates = df_temp[date_col].dropna()
                    if not valid_dates.empty:
                        date_range_min = valid_dates.min()
                        date_range_max = valid_dates.max()
                        # Double-check they're valid before using strftime
                        if pd.notna(date_range_min) and pd.notna(date_range_max):
                            try:
                                metrics_lines.append(f"  Data Range: {date_range_min.strftime('%b-%Y')} to {date_range_max.strftime('%b-%Y')}")
                            except Exception as date_err:
                                print(f"[Financial Agent] Date formatting error: {date_err}")
                except Exception as e:
                    print(f"[Financial Agent] Date range detection error: {e}")
            
            # List categorical columns and their values
            categorical_cols = [col for col in df.columns if df[col].dtype == 'object']
            if categorical_cols:
                metrics_lines.append(f"  Categories Available: {', '.join(categorical_cols)}")
            
            metrics_text = "\n".join(metrics_lines) if metrics_lines else "Metrics computed from CSV data."
        except Exception as e:
            print(f"[Financial Agent] Error computing metrics: {str(e)}")
            metrics_text = "Metrics available from CSV data."
    else:
        metrics = {}
        metrics_text = "No financial data provided."

    # Step 3: LLM interprets metrics ONLY (CSV takes priority over RAG)
    # Ensure all components are valid strings
    query_str = str(query) if query else "No query provided"
    
    # If CSV data was provided, use ONLY that - don't confuse LLM with stale RAG context
    if has_csv_data:
        # CSV data is primary source - suppress external context to prevent hallucination
        context_str = ""  # Suppress RAG context entirely when CSV provided
        print(f"[Financial Agent] Using CSV-only mode. Suppressing external context to ensure data accuracy.")
        data_source = "CSV"
    else:
        # No CSV data - use domain-filtered RAG context
        try:
            filtered_chunks, domain_relevance = query_with_domain_filter(
                "financial_reports", query, domain="financial", top_k=10
            )
            context = format_context(filtered_chunks) if filtered_chunks else ""
            context_str = str(context) if context else "No context available"
            context_instruction = "Use the retrieved financial context below to answer. Do NOT use external knowledge not in the context."
            print(f"[Financial Agent] Using RAG-only mode with domain filtering (relevance: {domain_relevance:.2%}).")
            data_source = "RAG Documents (Domain-Filtered)" if filtered_chunks else "RAG (No Docs)"
        except Exception as e:
            print(f"[Financial Agent] Domain filtering failed: {e}. Using basic RAG.")
            context_str = ""
            context_instruction = "Use only explicit facts from the context."
            data_source = "RAG (Fallback)"
    
    metrics_str = str(metrics_text) if metrics_text else "No metrics"
    
    prompt = f"""You are a Financial Analyst providing comprehensive financial analysis and strategic recommendations to business leadership.

When CSV data is provided, it is the primary authoritative source for all numerical claims. Ensure all figures reference the metrics provided below. For document-based analysis, use only the information explicitly contained in the retrieved context.

FINANCIAL METRICS & DATA STRUCTURE:
{metrics_str}

{"SUPPLEMENTARY CONTEXT FROM DOCUMENTS:" + chr(10) + context_str + chr(10) if context_str else ""}

USER QUERY:
{query_str}

ANALYSIS FRAMEWORK:
1. Address the specific question directly with confidence based on available data
2. Support all numerical claims with explicit references to the computed metrics above
3. Provide context and business interpretation of the figures
4. Clearly distinguish between what data shows and what cannot be determined from available information
5. Format your response professionally for executive consumption

RESPONSE STRUCTURE:
- Lead with a direct answer to the question
- Present key supporting metrics with clear attribution
- Provide analytical interpretation and business implications
- Note any material data gaps relevant to a complete answer
- Offer data-driven insights and recommendations where applicable

Quality Standards:
- Every numerical claim must be traceable to the metrics provided
- Avoid speculation or external knowledge not explicitly in the data
- Use precise, professional language appropriate for financial stakeholders
- Focus on actionable insights, not data limitations

Deliver a comprehensive, data-backed response that directly addresses the user's question."""

    response = call_gemini(prompt)
    
    # Validate response against metrics to catch hallucination
    response = validate_response_against_metrics(response, metrics, query)
    response = call_llm(system_prompt, user_message)
    visualization = None
    if VISUALIZATION_AVAILABLE and df is not None and not df.empty:
        try:
            print(f"[Financial Agent] Generating visualization from query: {query}")
            
            # Detect chart intent from query (semantic)
            chart_intent = detect_chart_intent(query)
            
            # Detect revenue column
            revenue_col = None
            for candidate in ["revenue", "sales_amount", "total_revenue"]:
                if candidate in df.columns:
                    revenue_col = candidate
                    break
            
            if not revenue_col:
                print(f"[Financial Agent] Could not detect revenue column for visualization")
                visualization = None
            else:
                # Generate chart based on intent
                if chart_intent == "cost" and "total_cogs" in metrics and "total_expenses" in metrics:
                    cost_data = {
                        "COGS": metrics.get("total_cogs", 0),
                        "Operating Expenses": metrics.get("total_expenses", 0)
                    }
                    visualization = create_breakdown_pie(cost_data, title="Cost Breakdown")
                    print(f"[Financial Agent] Cost breakdown visualization created")
                
                elif chart_intent in ["trend", "default"]:
                    # Look for date column
                    date_col = None
                    for candidate in ["quarter", "month", "period"]:
                        if candidate in df.columns:
                            date_col = candidate
                            break
                    
                    if date_col:
                        period_revenue = df.groupby(date_col)[revenue_col].sum().to_dict()
                        visualization = create_timeseries_line(period_revenue, title="Revenue Trend")
                        print(f"[Financial Agent] Revenue trend visualization created")
                    else:
                        # Fallback to costs if available
                        if "total_cogs" in metrics and "total_expenses" in metrics:
                            cost_data = {
                                "COGS": metrics.get("total_cogs", 0),
                                "Operating Expenses": metrics.get("total_expenses", 0)
                            }
                            visualization = create_breakdown_pie(cost_data, title="Cost Breakdown")
                            print(f"[Financial Agent] Cost visualization created")
                        else:
                            revenue_data = {revenue_col: float(df[revenue_col].sum())}
                            visualization = create_category_bar(revenue_data, title="Total Revenue")
                            print(f"[Financial Agent] Default revenue visualization created")
                
                # Fallback: Try to detect period data
                if not visualization:
                    date_col = None
                    for candidate in ["quarter", "month", "period"]:
                        if candidate in df.columns:
                            date_col = candidate
                            break
                    
                    if date_col:
                        period_revenue = df.groupby(date_col)[revenue_col].sum().to_dict()
                        visualization = create_timeseries_line(period_revenue, title="Revenue Trend")
                        print(f"[Financial Agent] Revenue trend visualization created")
                    elif "total_cogs" in metrics:
                        cost_data = {
                            "COGS": metrics.get("total_cogs", 0),
                            "Operating Expenses": metrics.get("total_expenses", 0)
                        }
                        visualization = create_breakdown_pie(cost_data, title="Cost Breakdown")
                        print(f"[Financial Agent] Cost breakdown visualization created")
                    else:
                        revenue_data = {revenue_col: float(df[revenue_col].sum())}
                        visualization = create_category_bar(revenue_data, title="Total Revenue")
                        print(f"[Financial Agent] Default visualization created")
        
        except Exception as e:
            print(f"[Financial Agent] Visualization error: {str(e)}")
            import traceback
            traceback.print_exc()

    return {
        "agent": "Financial Analyst",
        "agent_domain": "Financial Performance Analysis",
        "query": query,
        "metrics": metrics,
        "response": response,
        "data_source": data_source,
        "confidence": "HIGH" if metrics else "MEDIUM",
        "visualization": visualization,
    }


if __name__ == "__main__":
    result = run("What is our Q3 financial performance?")
    print("\n" + "="*50)
    print(result["response"])