import numpy as np
import pandas as pd


def parse_month_flexible(date_str: str):
    """
    Try multiple date formats to parse month string.
    Handles: Jan-2022, Jan-22, January-2022, 2022-01, 01/2022, Jan 2022
    """
    if not date_str or pd.isna(date_str):
        return pd.NaT

    date_str = str(date_str).strip()

    formats = [
        "%b-%Y",  # Jan-2022
        "%b-%y",  # Jan-22
        "%B-%Y",  # January-2022
        "%B-%y",  # January-22
        "%Y-%m",  # 2022-01
        "%m/%Y",  # 01/2022
        "%b %Y",  # Jan 2022
        "%B %Y",  # January 2022
        "%m-%Y",  # 01-2022
    ]

    for fmt in formats:
        try:
            return pd.to_datetime(date_str, format=fmt)
        except Exception:
            continue

    # Last resort: pandas auto-detect.
    try:
        return pd.to_datetime(date_str, infer_datetime_format=True)
    except Exception:
        return pd.NaT


def detect_sales_column(df: pd.DataFrame, column_mapping: dict = None):
    """
    Detect the sales column using multiple strategies.
    """
    # Strategy 1: Use provided column mapping.
    if column_mapping and "sales" in column_mapping:
        col = column_mapping["sales"]
        if col in df.columns:
            print(f"[Sales Agent] Column mapping match: {col}")
            return col

    # Strategy 2: Exact match first (most reliable).
    exact_matches = [
        "sales_amount", "sales", "revenue",
        "total_sales", "amount", "income",
        "earnings", "value", "total_revenue",
        "net_sales", "gross_sales",
    ]
    for exact in exact_matches:
        if exact in df.columns:
            if pd.to_numeric(df[exact], errors="coerce").notna().sum() > 0:
                print(f"[Sales Agent] Exact match: {exact}")
                return exact

    # Strategy 3: Keyword search in column names.
    keywords = [
        "sales", "revenue", "amount",
        "income", "earnings", "total", "value",
    ]
    for col in df.columns:
        col_lower = col.lower()
        if any(k in col_lower for k in keywords):
            if df[col].dtype in ["int64", "float64", "Int64", "Float64"]:
                print(f"[Sales Agent] Keyword match: {col}")
                return col

    # Strategy 4: Only one numeric column.
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if len(numeric_cols) == 1:
        print(f"[Sales Agent] Only one numeric column: {numeric_cols[0]}")
        return numeric_cols[0]

    # Strategy 5: First numeric column.
    if numeric_cols:
        print(f"[Sales Agent] Using first numeric column: {numeric_cols[0]}")
        return numeric_cols[0]

    return None


def compute_trends(df: pd.DataFrame, column_mapping: dict = None):
    if df is None or df.empty:
        return {"error": "No data"}

    df = df.copy()

    sales_col = detect_sales_column(df, column_mapping)
    if not sales_col:
        print(f"[Sales Agent] Available columns: {df.columns.tolist()}")
        return {"error": f"No sales column found. Available: {df.columns.tolist()}"}

    print(f"[Sales Agent] Using sales column: {sales_col}")

    df[sales_col] = pd.to_numeric(df[sales_col], errors="coerce")
    series = df[sales_col].dropna()

    if series.empty:
        return {"error": "Invalid sales data - all values are null"}

    trends = {}

    trends["total"] = float(series.sum())
    trends["mean"] = float(series.mean())
    trends["median"] = float(series.median())
    trends["min"] = float(series.min())
    trends["max"] = float(series.max())
    trends["count"] = int(series.count())

    if "sales_growth_pct" in df.columns:
        growth = pd.to_numeric(df["sales_growth_pct"], errors="coerce").dropna()
        if not growth.empty:
            trends["growth_rate"] = float(growth.mean())

    if "month" in df.columns:
        print("[Sales Agent] Parsing month column...")
        print(f"[Sales Agent] Sample values: {df['month'].head(3).tolist()}")

        # Parse using flexible parser.
        df["month_parsed"] = df["month"].apply(parse_month_flexible)

        # Check how many parsed successfully.
        parsed_count = df["month_parsed"].notna().sum()
        total_count = len(df)
        print(f"[Sales Agent] Parsed {parsed_count}/{total_count} dates successfully")

        if parsed_count == 0:
            print("[Sales Agent] Warning: Date parsing failed for all records")
        else:
            df = df.sort_values("month_parsed", na_position="last")
            df_valid = df.dropna(subset=["month_parsed"])

            if not df_valid.empty:
                # Monthly aggregation.
                monthly = df_valid.groupby("month_parsed")[sales_col].sum()
                period_breakdown = {
                    str(date.strftime("%b-%Y")): float(val)
                    for date, val in monthly.items()
                }
                trends["period_breakdown"] = period_breakdown

                # Year-wise breakdown.
                df_valid["year"] = df_valid["month_parsed"].dt.year
                yearly = df_valid.groupby("year")[sales_col].sum()
                trends["yearly_breakdown"] = {
                    str(year): float(val)
                    for year, val in yearly.items()
                }

                # Available years.
                available_years = sorted(list(set(df_valid["month_parsed"].dt.year.unique())))
                trends["available_years"] = available_years

                # Date range.
                valid_dates = df_valid["month_parsed"].dropna()
                min_date = valid_dates.min()
                max_date = valid_dates.max()
                if pd.notna(min_date) and pd.notna(max_date):
                    trends["date_range"] = {
                        "earliest": str(min_date.strftime("%b-%Y")),
                        "latest": str(max_date.strftime("%b-%Y")),
                    }

                print(f"[Sales Agent] Processed {len(period_breakdown)} months")

    if "region" in df.columns:
        region_sales = df.groupby("region")[sales_col].sum()
        trends["region_breakdown"] = {str(k): float(v) for k, v in region_sales.items()}
        print(f"[Sales Agent] Region breakdown: {list(trends['region_breakdown'].keys())}")

    if "product" in df.columns:
        product_sales = df.groupby("product")[sales_col].sum()
        trends["product_breakdown"] = {str(k): float(v) for k, v in product_sales.items()}
        print(f"[Sales Agent] Product breakdown: {list(trends['product_breakdown'].keys())}")

    try:
        x = np.arange(len(series))
        slope, intercept = np.polyfit(x, series.values, 1)
        trends["next_prediction"] = float(slope * len(series) + intercept)
    except Exception:
        trends["next_prediction"] = None

    trends["available_columns"] = df.columns.tolist()
    trends["sales_column_used"] = sales_col

    categorical_info = {}
    for col in df.columns:
        if df[col].dtype == "object":
            unique_vals = df[col].unique().tolist()
            if len(unique_vals) <= 20:
                categorical_info[col] = unique_vals
    trends["categorical_metadata"] = categorical_info

    return trends
