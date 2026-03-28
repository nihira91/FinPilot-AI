# Optional visualization support for the financial agent.
try:
    from utils.chart_generator import create_breakdown_pie, create_category_bar, create_timeseries_line

    VISUALIZATION_AVAILABLE = True
except ImportError:
    create_breakdown_pie = None
    create_category_bar = None
    create_timeseries_line = None
    VISUALIZATION_AVAILABLE = False


def _query_implies_cost_intent(query: str) -> bool:
    query_lower = (query or "").lower()
    cost_terms = [
        "cogs",
        "cost of goods sold",
        "cost",
        "expense",
        "operating_expenses",
        "operating expenses",
        "opex",
        "marketing_spend",
        "marketing spend",
        "rd_expense",
        "r&d",
        "breakdown",
        "split",
        "distribution",
    ]
    return any(term in query_lower for term in cost_terms)


def _format_cost_label(raw_name: str) -> str:
    label_map = {
        "cogs": "COGS (Cost of Goods Sold)",
        "cost_of_goods_sold": "COGS (Cost of Goods Sold)",
        "operating_expenses": "Operating Expenses (OPEX)",
        "op_expenses": "Operating Expenses (OPEX)",
        "opex": "Operating Expenses (OPEX)",
        "marketing_spend": "Marketing Spend",
        "rd_expense": "R&D Expense",
    }
    key = str(raw_name).strip().lower()
    if key in label_map:
        return label_map[key]
    return str(raw_name).replace("_", " ").title()


def _build_cost_data(metrics: dict) -> dict:
    # Prefer detailed breakdown when available so charts reflect uploaded column names.
    breakdown = metrics.get("cost_breakdown", {}) if isinstance(metrics, dict) else {}
    if isinstance(breakdown, dict) and breakdown:
        cost_data = {}
        for key, val in breakdown.items():
            try:
                num_val = float(val)
            except (TypeError, ValueError):
                continue
            if num_val > 0:
                cost_data[_format_cost_label(key)] = num_val
        if cost_data:
            return cost_data

    # Backward-compatible fallback.
    return {
        "COGS (Cost of Goods Sold)": float(metrics.get("total_cogs", 0)),
        "Operating Expenses (OPEX)": float(metrics.get("total_expenses", 0)),
    }


def build_visualization(query: str, df, metrics: dict, chart_intent: str):
    if not VISUALIZATION_AVAILABLE or df is None or df.empty:
        return None

    print(f"[Financial Agent] Generating visualization from query: {query}")

    # Detect revenue column.
    revenue_col = None
    for candidate in ["revenue", "sales_amount", "total_revenue"]:
        if candidate in df.columns:
            revenue_col = candidate
            break

    query_lower = (query or "").lower()
    cost_intent = chart_intent == "cost" or _query_implies_cost_intent(query)
    prefers_bar_for_cost = "bar" in query_lower

    visualization = None

    # Generate chart based on intent.
    if cost_intent and isinstance(metrics, dict):
        cost_data = _build_cost_data(metrics)
        if any(v > 0 for v in cost_data.values()):
            if prefers_bar_for_cost:
                visualization = create_category_bar(cost_data, title="Cost Breakdown")
                print("[Financial Agent] Cost breakdown bar visualization created")
            else:
                visualization = create_breakdown_pie(cost_data, title="Cost Breakdown")
                print("[Financial Agent] Cost breakdown pie visualization created")

    elif chart_intent in ["trend", "default"] and revenue_col:
        # Look for date column.
        date_col = None
        for candidate in ["quarter", "month", "period"]:
            if candidate in df.columns:
                date_col = candidate
                break

        if date_col:
            period_revenue = df.groupby(date_col)[revenue_col].sum().to_dict()
            visualization = create_timeseries_line(period_revenue, title="Revenue Trend")
            print("[Financial Agent] Revenue trend visualization created")
        else:
            # Fallback to costs if available.
            if "total_cogs" in metrics and "total_expenses" in metrics:
                cost_data = _build_cost_data(metrics)
                visualization = create_breakdown_pie(cost_data, title="Cost Breakdown")
                print("[Financial Agent] Cost visualization created")
            elif revenue_col:
                revenue_data = {revenue_col: float(df[revenue_col].sum())}
                visualization = create_category_bar(revenue_data, title="Total Revenue")
                print("[Financial Agent] Default revenue visualization created")

    # Fallback: Try to detect period data.
    if not visualization:
        date_col = None
        for candidate in ["quarter", "month", "period"]:
            if candidate in df.columns:
                date_col = candidate
                break

        if date_col and revenue_col:
            period_revenue = df.groupby(date_col)[revenue_col].sum().to_dict()
            visualization = create_timeseries_line(period_revenue, title="Revenue Trend")
            print("[Financial Agent] Revenue trend visualization created")
        elif "total_cogs" in metrics:
            cost_data = _build_cost_data(metrics)
            visualization = create_breakdown_pie(cost_data, title="Cost Breakdown")
            print("[Financial Agent] Cost breakdown visualization created")
        elif revenue_col:
            revenue_data = {revenue_col: float(df[revenue_col].sum())}
            visualization = create_category_bar(revenue_data, title="Total Revenue")
            print("[Financial Agent] Default visualization created")

    return visualization
