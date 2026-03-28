import warnings
import pandas as pd
import numpy as np


def detect_cost_columns(df: pd.DataFrame) -> list:
    """
    Automatically detect columns that contain cost/expense data.
    Looks for numeric columns with 'cost', 'expense', 'spending' in name.
    """
    cost_keywords = ["cost", "expense", "spending", "amount"]
    cost_cols = []

    for col in df.columns:
        if df[col].dtype in ["float64", "int64"]:
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

    # Slow-fallback: infer standard financial columns.
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

    # Safe numeric conversion for all known financial columns.
    num_cols = [
        revenue_col,
        cogs_col,
        operating_expenses_col,
        marketing_col,
        rd_col,
        net_income_col,
        profit_margin_col,
        employee_col,
    ]
    for col in set([c for c in num_cols if c is not None]):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Core revenue/costs metrics.
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

    # Gross profit: use input if present, else compute revenue - cogs.
    if "gross_profit" in df.columns:
        gp = pd.to_numeric(df["gross_profit"], errors="coerce").dropna()
        if not gp.empty:
            metrics["total_gross_profit"] = float(gp.sum())
            metrics["average_gross_profit"] = float(gp.mean())
    elif "total_revenue" in metrics and "total_cogs" in metrics:
        metrics["total_gross_profit"] = float(metrics["total_revenue"] - metrics["total_cogs"])

    # net income fallback if missing.
    if "total_net_income" not in metrics and "total_revenue" in metrics and "total_operating_expenses" in metrics:
        metrics["total_net_income"] = float(metrics["total_revenue"] - metrics["total_operating_expenses"] - metrics.get("total_cogs", 0))

    # profit margin calculations.
    if profit_margin_col and profit_margin_col in df.columns:
        pm = df[profit_margin_col].dropna()
        if not pm.empty:
            metrics["average_profit_margin_pct"] = float(pm.mean())
    elif "total_gross_profit" in metrics and "total_revenue" in metrics and metrics["total_revenue"] != 0:
        metrics["calculated_profit_margin_pct"] = float((metrics["total_gross_profit"] / metrics["total_revenue"]) * 100)

    # per employee metrics.
    if employee_col and employee_col in df.columns and "total_revenue" in metrics:
        emp = df[employee_col].dropna()
        if not emp.empty and emp.sum() != 0:
            metrics["revenue_per_employee"] = float(metrics["total_revenue"] / emp.mean())
            if "total_net_income" in metrics:
                metrics["net_income_per_employee"] = float(metrics["total_net_income"] / emp.mean())

    # trend by quarter if exists.
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
                metrics["quarter_over_quarter_growth_pct"] = float(((last - first) / abs(first) * 100) if first != 0 else 0)
        except Exception:
            pass

    # Auto-detect and sum all cost columns.
    cost_cols = detect_cost_columns(df)
    if cost_cols:
        metrics["cost_breakdown"] = {}
        total_costs = 0
        for col in cost_cols:
            total = float(df[col].sum())
            metrics["cost_breakdown"][col] = total
            total_costs += total
        metrics["total_cost_sum"] = total_costs

    # Optional budget vs actual analysis remains.
    if "Budget/Actual" in df.columns or "Type" in df.columns or "Category" in df.columns:
        budget_actual_col = next((col for col in ["Budget/Actual", "Type", "Category"] if col in df.columns), None)
        if budget_actual_col is not None:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                budget_data = df[df[budget_actual_col].astype(str).str.lower() == "budget"]
                actual_data = df[df[budget_actual_col].astype(str).str.lower() == "actual"]

            numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns
            if not budget_data.empty and not actual_data.empty and len(numeric_cols) > 0:
                budget_total = budget_data[numeric_cols].sum().sum()
                actual_total = actual_data[numeric_cols].sum().sum()
                variance = float(actual_total - budget_total)
                variance_pct = float((variance / budget_total * 100) if budget_total != 0 else 0)

                metrics["budget_vs_actual"] = {
                    "budget_total": float(budget_total),
                    "actual_total": float(actual_total),
                    "variance": variance,
                    "variance_percentage": variance_pct,
                }

    # Date-based trends if available.
    date_col = next((col for col in df.columns if col.lower() in ["quarter", "month", "date", "period"]), None)
    if date_col and revenue_col in df.columns:
        try:
            by_date = df.groupby(date_col)[revenue_col].sum()
            metrics["time_series_revenue"] = {str(k): float(v) for k, v in by_date.items()}
            metrics["revenue_trend_slope"] = float(np.polyfit(np.arange(len(by_date)), by_date.values, 1)[0]) if len(by_date) > 1 else 0.0
        except Exception:
            pass

    # Column-level summary for all columns.
    metrics["column_summary"] = {}
    for col in df.columns:
        summary = {
            "dtype": str(df[col].dtype),
            "missing_count": int(df[col].isna().sum()),
            "unique_count": int(df[col].nunique(dropna=True)),
        }
        if pd.api.types.is_numeric_dtype(df[col]):
            num = pd.to_numeric(df[col], errors="coerce").dropna()
            if not num.empty:
                summary.update(
                    {
                        "total": float(num.sum()),
                        "mean": float(num.mean()),
                        "median": float(num.median()),
                        "std": float(num.std(ddof=0)),
                        "min": float(num.min()),
                        "max": float(num.max()),
                    }
                )
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

    # Return simplified version for backward compatibility.
    simple = {
        "total_revenue": detailed.get("total_revenue", 0.0),
        "total_cogs": detailed.get("total_cogs", 0.0),
        "total_expenses": detailed.get("total_cost_sum", detailed.get("total_expenses", 0.0)),
        "gross_profit": detailed.get("gross_profit", 0.0),
        "net_income": detailed.get("net_income", 0.0),
    }

    # Add detailed info if available.
    if "cost_breakdown" in detailed:
        simple["cost_breakdown"] = detailed["cost_breakdown"]
    if "budget_vs_actual" in detailed:
        simple["budget_vs_actual"] = detailed["budget_vs_actual"]
    if "monthly_trend" in detailed:
        simple["monthly_trend"] = detailed["monthly_trend"]

    # Keep legacy computed fields used by existing tests and callers.
    if "total_revenue" in simple and "total_cogs" in simple:
        simple["gross_profit"] = float(simple["total_revenue"] - simple["total_cogs"])
    if "gross_profit" in simple and "total_expenses" in simple:
        simple["net_income"] = float(simple["gross_profit"] - simple["total_expenses"])

    return simple
