# Optional visualization support for the sales agent.
try:
    from utils.chart_generator import create_timeseries_line, create_category_bar

    VISUALIZATION_AVAILABLE = True
except ImportError:
    create_timeseries_line = None
    create_category_bar = None
    VISUALIZATION_AVAILABLE = False

from .helpers import detect_chart_intent
from .metrics import detect_sales_column, parse_month_flexible


def build_visualization(query: str, df, column_mapping: dict = None):
    if not VISUALIZATION_AVAILABLE or df is None or df.empty:
        return None

    sales_col = detect_sales_column(df, column_mapping)
    chart_intent = detect_chart_intent(query)
    visualization = None

    if chart_intent == "region" and "region" in df.columns:
        region_sales = df.groupby("region")[sales_col].sum().to_dict()
        visualization = create_category_bar(region_sales, title="Sales by Region")
        print("[Sales Agent] Region visualization created")

    elif chart_intent == "product" and "product" in df.columns:
        product_sales = df.groupby("product")[sales_col].sum().to_dict()
        visualization = create_category_bar(product_sales, title="Sales by Product")
        print("[Sales Agent] Product visualization created")

    elif chart_intent in ["trend", "default"] and "month" in df.columns:
        # Use parsed months for proper sorting.
        df_temp = df.copy()
        df_temp["month_parsed"] = df_temp["month"].apply(parse_month_flexible)
        df_temp = df_temp.dropna(subset=["month_parsed"])
        df_temp = df_temp.sort_values("month_parsed")

        monthly_sales = df_temp.groupby("month_parsed")[sales_col].sum()
        monthly_dict = {
            str(date.strftime("%b-%Y")): float(val)
            for date, val in monthly_sales.items()
        }
        visualization = create_timeseries_line(monthly_dict, title="Sales Trend - Monthly")
        print("[Sales Agent] Time series visualization created")

    # Fallbacks.
    elif "month" in df.columns:
        df_temp = df.copy()
        df_temp["month_parsed"] = df_temp["month"].apply(parse_month_flexible)
        df_temp = df_temp.dropna(subset=["month_parsed"])
        df_temp = df_temp.sort_values("month_parsed")
        monthly_sales = df_temp.groupby("month_parsed")[sales_col].sum()
        monthly_dict = {
            str(date.strftime("%b-%Y")): float(val)
            for date, val in monthly_sales.items()
        }
        visualization = create_timeseries_line(monthly_dict, title="Sales Trend - Monthly")

    elif "region" in df.columns:
        region_sales = df.groupby("region")[sales_col].sum().to_dict()
        visualization = create_category_bar(region_sales, title="Sales by Region")

    elif "product" in df.columns:
        product_sales = df.groupby("product")[sales_col].sum().to_dict()
        visualization = create_category_bar(product_sales, title="Sales by Product")

    return visualization
