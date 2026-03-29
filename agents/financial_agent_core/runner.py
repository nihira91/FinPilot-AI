import pandas as pd

from rag.pipeline import rag_query, format_context
from rag.vector_store import query_with_domain_filter

from .constants import CHART_INTENT_KEYWORDS
from .helpers import detect_chart_intent, safe_format_value, validate_response_against_metrics
from .llm_client import call_gemini
from .metrics import compute_metrics
from .visualization import build_visualization


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
    # Ensure query is valid string.
    if query is None:
        raise ValueError("Query is None in Financial Agent")
    query = str(query).strip()

    if not query:
        raise ValueError("Query is empty in Financial Agent")

    print(f"\n[Financial Agent] Query received: {query}")

    # Step 1: Check if CSV data provided FIRST (takes absolute priority).
    has_csv_data = df is not None and not df.empty
    print(f"[Financial Agent] CSV data available: {has_csv_data}")

    # Step 2: ONLY retrieve RAG if NO CSV data is provided.
    # This prevents stale ChromaDB data from interfering with fresh uploads.
    context = "No document context - CSV data is primary source."
    chunks = []

    if not has_csv_data:
        # Only use RAG if no CSV data provided.
        print("[Financial Agent] No CSV data. Attempting RAG retrieval...")
        try:
            chunks = rag_query("financial_reports", query, top_k=5)
            context = format_context(chunks) if chunks else "No document context available."
        except Exception as e:
            print(f"[Financial Agent] RAG query error: {str(e)}")
            context = "No document context available."

    context = str(context)

    # Step 3: Pandas analysis - compute metrics from CSV if provided.
    metrics = {}
    metrics_text = "No financial data provided. Analyze from documents only."

    if df is not None and not df.empty:
        try:
            metrics = compute_metrics(df, column_mapping=column_mapping)

            # Format metrics for LLM with details.
            metrics_lines = []

            # Basic metrics.
            for key in ["total_revenue", "total_cogs", "total_expenses", "gross_profit", "net_income"]:
                if key in metrics and isinstance(metrics.get(key), (int, float)) and metrics[key] != 0:
                    metrics_lines.append(f"  {key.replace('_', ' ').title()}: {safe_format_value(metrics[key])}")

            # Cost breakdown.
            if "cost_breakdown" in metrics and isinstance(metrics["cost_breakdown"], dict):
                metrics_lines.append("\nCost Breakdown:")
                for cost_type, amount in metrics["cost_breakdown"].items():
                    if isinstance(amount, (int, float)) and amount != 0:
                        metrics_lines.append(f"  {cost_type}: {safe_format_value(amount)}")

            # Budget vs Actual.
            if "budget_vs_actual" in metrics and isinstance(metrics["budget_vs_actual"], dict):
                bva = metrics["budget_vs_actual"]
                metrics_lines.append("\nBudget vs Actual:")
                if "budget_total" in bva and isinstance(bva.get("budget_total"), (int, float)):
                    metrics_lines.append(f"  Budget Total: {safe_format_value(bva['budget_total'])}")
                if "actual_total" in bva and isinstance(bva.get("actual_total"), (int, float)):
                    metrics_lines.append(f"  Actual Total: {safe_format_value(bva['actual_total'])}")
                if "variance" in bva and isinstance(bva.get("variance"), (int, float)):
                    metrics_lines.append(f"  Variance: {safe_format_value(bva['variance'])}")

            # Monthly trend.
            if "monthly_trend" in metrics and isinstance(metrics["monthly_trend"], dict):
                trend = metrics["monthly_trend"]
                metrics_lines.append("\nMonthly Trend:")
                if "average_monthly" in trend and isinstance(trend.get("average_monthly"), (int, float)):
                    metrics_lines.append(f"  Average Monthly: {safe_format_value(trend['average_monthly'])}")
                if "highest_month" in trend and trend.get("highest_month"):
                    metrics_lines.append(f"  Highest Month: {safe_format_value(trend['highest_month'])}")
                if "lowest_month" in trend and trend.get("lowest_month"):
                    metrics_lines.append(f"  Lowest Month: {safe_format_value(trend['lowest_month'])}")

            # Add column metadata.
            metrics_lines.append("\n📊 AVAILABLE DATA STRUCTURE:")
            metrics_lines.append(f"  Total Rows: {df.shape[0]}")
            metrics_lines.append(f"  Total Columns: {df.shape[1]}")
            metrics_lines.append(f"  Column Names: {', '.join(df.columns.tolist())}")

            # Detect date range if date column exists.
            date_cols = [col for col in df.columns if col.lower() in ["date", "month", "quarter", "period"]]
            if date_cols:
                date_col = date_cols[0]
                try:
                    df_temp = df.copy()
                    # Use explicit format for month column (Jan-22 = Jan 2022).
                    if date_col.lower() == "month":
                        df_temp[date_col] = pd.to_datetime(df_temp[date_col], format="%b-%y", errors="coerce")
                    else:
                        df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors="coerce")

                    # Filter out invalid dates.
                    valid_dates = df_temp[date_col].dropna()
                    if not valid_dates.empty:
                        date_range_min = valid_dates.min()
                        date_range_max = valid_dates.max()
                        if pd.notna(date_range_min) and pd.notna(date_range_max):
                            try:
                                metrics_lines.append(f"  Data Range: {date_range_min.strftime('%b-%Y')} to {date_range_max.strftime('%b-%Y')}")
                            except Exception as date_err:
                                print(f"[Financial Agent] Date formatting error: {date_err}")
                except Exception as e:
                    print(f"[Financial Agent] Date range detection error: {e}")

            # List categorical columns and their values.
            categorical_cols = [col for col in df.columns if df[col].dtype == "object"]
            if categorical_cols:
                metrics_lines.append(f"  Categories Available: {', '.join(categorical_cols)}")

            metrics_text = "\n".join(metrics_lines) if metrics_lines else "Metrics computed from CSV data."
        except Exception as e:
            print(f"[Financial Agent] Error computing metrics: {str(e)}")
            metrics_text = "Metrics available from CSV data."
    else:
        metrics = {}
        metrics_text = "No financial data provided."

    # Step 4: LLM interprets metrics ONLY (CSV takes priority over RAG).
    query_str = str(query) if query else "No query provided"

    # If CSV data was provided, use ONLY that.
    if has_csv_data:
        # CSV data is primary source - suppress external context to prevent hallucination.
        context_str = ""
        print("[Financial Agent] Using CSV-only mode. Suppressing external context to ensure data accuracy.")
        data_source = "CSV"
    else:
        # No CSV data - use domain-filtered RAG context.
        try:
            filtered_chunks, domain_relevance = query_with_domain_filter("financial_reports", query, domain="financial", top_k=10)
            context = format_context(filtered_chunks) if filtered_chunks else ""
            context_str = str(context) if context else "No context available"
            print(f"[Financial Agent] Using RAG-only mode with domain filtering (relevance: {domain_relevance:.2%}).")
            data_source = "RAG Documents (Domain-Filtered)" if filtered_chunks else "RAG (No Docs)"
        except Exception as e:
            print(f"[Financial Agent] Domain filtering failed: {e}. Using basic RAG.")
            context_str = ""
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

    # Validate response against metrics to catch hallucination.
    response = validate_response_against_metrics(response, metrics, query)

    visualization = None
    try:
        chart_intent = detect_chart_intent(query, CHART_INTENT_KEYWORDS)
        visualization = build_visualization(query, df, metrics, chart_intent)
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
