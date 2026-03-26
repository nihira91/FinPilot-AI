import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
MODEL_ID = "gemini-2.5-flash"

# Try importing visualization - optional feature
try:
    from utils.chart_generator import create_timeseries_line, create_category_bar
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False


CHART_INTENT_KEYWORDS = {
    "region": [
        "region", "location", "area", "territory", "zone", "state", "city",
        "by region", "region-wise", "regional", "across region", "geographic",
        "where", "by location", "breakdown by location"
    ],
    "product": [
        "product", "category", "item", "what", "which product", "sku",
        "by product", "product-wise", "type", "service", "category-wise",
        "product performance", "product breakdown", "category analysis"
    ],
    "trend": [
        "trend", "month", "time", "over time", "pattern", "temporal",
        "monthly", "time-series", "when", "period", "weekly", "quarterly",
        "forecast", "growth", "trajectory", "evolution", "progression"
    ]
}


def detect_chart_intent(query: str) -> str:
    """Detect chart intent from query using semantic keywords."""
    query_lower = query.lower()
    for intent, keywords in CHART_INTENT_KEYWORDS.items():
        if any(kw in query_lower for kw in keywords):
            print(f"[Sales Agent] Chart intent detected: {intent}")
            return intent
    return "default"


def safe_format_value(val):
    if val is None:
        return "N/A"
    if isinstance(val, (int, float)):
        return f"{val:,.2f}"
    return str(val)


def validate_response(response: str, metrics: dict) -> str:
    """Prevent hallucinated values."""
    if not metrics or not response:
        return response
    import re
    fake_growth = re.findall(r"\d+\.?\d*%", response)
    for g in fake_growth:
        num = float(g.replace("%", ""))
        if num > 100:
            response = response.replace(g, "Not Available")
    return response


def call_gemini(prompt: str, max_tokens: int = 8192) -> str:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.0,
            max_output_tokens=max_tokens,
        )
    )
    return response.text.strip()


def parse_month_flexible(date_str: str):
    """
    Try multiple date formats to parse month string.
    Handles: Jan-2022, Jan-22, January-2022, 2022-01, 01/2022, Jan 2022
    """
    if not date_str or pd.isna(date_str):
        return pd.NaT

    date_str = str(date_str).strip()

    formats = [
        "%b-%Y",   # Jan-2022 ← main format
        "%b-%y",   # Jan-22
        "%B-%Y",   # January-2022
        "%B-%y",   # January-22
        "%Y-%m",   # 2022-01
        "%m/%Y",   # 01/2022
        "%b %Y",   # Jan 2022
        "%B %Y",   # January 2022
        "%m-%Y",   # 01-2022
    ]

    for fmt in formats:
        try:
            return pd.to_datetime(date_str, format=fmt)
        except:
            continue

    # Last resort — pandas auto-detect
    try:
        return pd.to_datetime(date_str, infer_datetime_format=True)
    except:
        return pd.NaT


def detect_sales_column(df, column_mapping=None):
    """
    Detect the sales column using multiple strategies.
    """
    # Strategy 1: Use provided column mapping
    if column_mapping and "sales" in column_mapping:
        col = column_mapping["sales"]
        if col in df.columns:
            print(f"[Sales Agent] Column mapping match: {col}")
            return col

    # Strategy 2: Exact match first (most reliable)
    exact_matches = [
        "sales_amount", "sales", "revenue",
        "total_sales", "amount", "income",
        "earnings", "value", "total_revenue",
        "net_sales", "gross_sales"
    ]
    for exact in exact_matches:
        if exact in df.columns:
            if pd.to_numeric(df[exact], errors="coerce").notna().sum() > 0:
                print(f"[Sales Agent] Exact match: {exact}")
                return exact

    # Strategy 3: Keyword search in column names
    keywords = [
        "sales", "revenue", "amount",
        "income", "earnings", "total", "value"
    ]
    for col in df.columns:
        col_lower = col.lower()
        if any(k in col_lower for k in keywords):
            if df[col].dtype in ["int64", "float64", "Int64", "Float64"]:
                print(f"[Sales Agent] Keyword match: {col}")
                return col

    # Strategy 4: Only one numeric column
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if len(numeric_cols) == 1:
        print(f"[Sales Agent] Only one numeric column: {numeric_cols[0]}")
        return numeric_cols[0]

    # Strategy 5: First numeric column
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
        return {"error": "Invalid sales data — all values are null"}

    trends = {}

    trends["total"]  = float(series.sum())
    trends["mean"]   = float(series.mean())
    trends["median"] = float(series.median())
    trends["min"]    = float(series.min())
    trends["max"]    = float(series.max())
    trends["count"]  = int(series.count())

    if "sales_growth_pct" in df.columns:
        growth = pd.to_numeric(
            df["sales_growth_pct"], errors="coerce"
        ).dropna()
        if not growth.empty:
            trends["growth_rate"] = float(growth.mean())

    if "month" in df.columns:

        print(f"[Sales Agent] Parsing month column...")
        print(f"[Sales Agent] Sample values: {df['month'].head(3).tolist()}")

        # Parse using flexible parser
        df["month_parsed"] = df["month"].apply(parse_month_flexible)

        # Check how many parsed successfully
        parsed_count = df["month_parsed"].notna().sum()
        total_count  = len(df)
        print(f"[Sales Agent] Parsed {parsed_count}/{total_count} dates successfully")

        if parsed_count == 0:
            print(f"[Sales Agent] Warning: Date parsing failed for all records")
        else:
            df = df.sort_values("month_parsed", na_position="last")
            df_valid = df.dropna(subset=["month_parsed"])

            if not df_valid.empty:
                # Monthly aggregation
                monthly = df_valid.groupby("month_parsed")[sales_col].sum()
                period_breakdown = {
                    str(date.strftime("%b-%Y")): float(val)
                    for date, val in monthly.items()
                }
                trends["period_breakdown"] = period_breakdown

                # Year-wise breakdown
                df_valid["year"] = df_valid["month_parsed"].dt.year
                yearly = df_valid.groupby("year")[sales_col].sum()
                trends["yearly_breakdown"] = {
                    str(year): float(val)
                    for year, val in yearly.items()
                }

                # Available years
                available_years = sorted(list(set(
                    df_valid["month_parsed"].dt.year.unique()
                )))
                trends["available_years"] = available_years

                # Date range
                valid_dates = df_valid["month_parsed"].dropna()
                min_date = valid_dates.min()
                max_date = valid_dates.max()
                if pd.notna(min_date) and pd.notna(max_date):
                    trends["date_range"] = {
                        "earliest": str(min_date.strftime("%b-%Y")),
                        "latest":   str(max_date.strftime("%b-%Y"))
                    }

                print(f"[Sales Agent] Processed {len(period_breakdown)} months")

    if "region" in df.columns:
        region_sales = df.groupby("region")[sales_col].sum()
        trends["region_breakdown"] = {
            str(k): float(v) for k, v in region_sales.items()
        }
        print(f"[Sales Agent] Region breakdown: {list(trends['region_breakdown'].keys())}")

    if "product" in df.columns:
        product_sales = df.groupby("product")[sales_col].sum()
        trends["product_breakdown"] = {
            str(k): float(v) for k, v in product_sales.items()
        }
        print(f"[Sales Agent] Product breakdown: {list(trends['product_breakdown'].keys())}")

    try:
        x = np.arange(len(series))
        slope, intercept = np.polyfit(x, series.values, 1)
        trends["next_prediction"] = float(slope * len(series) + intercept)
    except:
        trends["next_prediction"] = None

    trends["available_columns"] = df.columns.tolist()
    trends["sales_column_used"]  = sales_col

    categorical_info = {}
    for col in df.columns:
        if df[col].dtype == "object":
            unique_vals = df[col].unique().tolist()
            if len(unique_vals) <= 20:
                categorical_info[col] = unique_vals
    trends["categorical_metadata"] = categorical_info

    return trends


def run(query: str, df: pd.DataFrame = None, column_mapping: dict = None):

    if not query:
        raise ValueError("Query is empty")

    print(f"\n[Sales Agent] Query: {query}")

    trends      = {}
    trends_text = "No CSV data uploaded"

    if df is not None and not df.empty:

        trends = compute_trends(df, column_mapping)

        if "error" in trends:
            trends_text = f"Error: {trends['error']}"
        else:
            lines = []

            # Sales column used
            if "sales_column_used" in trends:
                lines.append(f"Sales Column Used: {trends['sales_column_used']}")

            # Date range
            if "date_range" in trends:
                lines.append(
                    f"Data Range: {trends['date_range']['earliest']} "
                    f"to {trends['date_range']['latest']}"
                )

            # Available years
            if "available_years" in trends:
                years_str = ", ".join(map(str, trends["available_years"]))
                lines.append(f"Years in Dataset: {years_str}")

            # Basic metrics
            lines.append("\n--- OVERALL METRICS ---")
            for key in ["total", "mean", "median", "min", "max"]:
                if key in trends:
                    lines.append(f"{key.title()}: {safe_format_value(trends[key])}")

            if "growth_rate" in trends:
                lines.append(
                    f"Avg Growth Rate: {safe_format_value(trends['growth_rate'])}%"
                )

            if "next_prediction" in trends and trends["next_prediction"]:
                lines.append(
                    f"Next Period Prediction: {safe_format_value(trends['next_prediction'])}"
                )

            # Yearly breakdown
            if "yearly_breakdown" in trends:
                lines.append("\n--- YEARLY SALES ---")
                for year, val in sorted(trends["yearly_breakdown"].items()):
                    lines.append(f"  {year}: {safe_format_value(val)}")

            # Monthly breakdown — ALL months
            if "period_breakdown" in trends and trends["period_breakdown"]:
                lines.append(f"\n--- MONTHLY SALES ({len(trends['period_breakdown'])} months) ---")
                for month, sales in trends["period_breakdown"].items():
                    lines.append(f"  {month}: {safe_format_value(sales)}")

            # Region breakdown
            if "region_breakdown" in trends:
                lines.append("\n--- SALES BY REGION ---")
                for region, val in sorted(
                    trends["region_breakdown"].items(),
                    key=lambda x: x[1], reverse=True
                ):
                    lines.append(f"  {region}: {safe_format_value(val)}")

            # Product breakdown
            if "product_breakdown" in trends:
                lines.append("\n--- SALES BY PRODUCT ---")
                for product, val in sorted(
                    trends["product_breakdown"].items(),
                    key=lambda x: x[1], reverse=True
                ):
                    lines.append(f"  {product}: {safe_format_value(val)}")

            # Categorical metadata
            if "categorical_metadata" in trends and trends["categorical_metadata"]:
                lines.append("\n--- AVAILABLE CATEGORIES ---")
                for col, values in trends["categorical_metadata"].items():
                    lines.append(
                        f"  {col.upper()}: {', '.join(map(str, values))}"
                    )

            trends_text = "\n".join(lines)

    prompt = f"""
You are a Sales Analyst providing data-driven insights to business stakeholders.

The COMPLETE dataset breakdown is provided below including ALL months, years, 
regions and products. Use this data to answer the user's question precisely.

COMPLETE SALES DATA:
{trends_text}

USER QUESTION:
{query}

ANALYSIS INSTRUCTIONS:
1. Use the exact data provided above — do NOT say data is unavailable
2. If user asks about 2023 or 2024 specifically, refer to the 
   YEARLY SALES and MONTHLY SALES sections above
3. Ground ALL statements in the numbers shown above
4. Provide specific figures, percentages and comparisons
5. If asking about regions or products, use the breakdowns provided

RESPONSE FORMAT:
- Start with a direct answer to the question
- Support with specific numbers from the data
- Provide trend analysis if relevant
- Give actionable insights
- Keep it professional and concise

Respond confidently using the data provided above.
"""

    response = call_gemini(prompt)
    response = validate_response(response, trends)

    visualization = None
    if VISUALIZATION_AVAILABLE and df is not None and not df.empty:
        try:
            sales_col    = detect_sales_column(df, column_mapping)
            chart_intent = detect_chart_intent(query)

            if chart_intent == "region" and "region" in df.columns:
                region_sales = df.groupby("region")[sales_col].sum().to_dict()
                visualization = create_category_bar(
                    region_sales, title="Sales by Region"
                )
                print(f"[Sales Agent] Region visualization created")

            elif chart_intent == "product" and "product" in df.columns:
                product_sales = df.groupby("product")[sales_col].sum().to_dict()
                visualization = create_category_bar(
                    product_sales, title="Sales by Product"
                )
                print(f"[Sales Agent] Product visualization created")

            elif chart_intent in ["trend", "default"] and "month" in df.columns:
                # Use parsed months for proper sorting
                df_temp = df.copy()
                df_temp["month_parsed"] = df_temp["month"].apply(
                    parse_month_flexible
                )
                df_temp = df_temp.dropna(subset=["month_parsed"])
                df_temp = df_temp.sort_values("month_parsed")

                monthly_sales = (
                    df_temp.groupby("month_parsed")[sales_col]
                    .sum()
                )
                monthly_dict = {
                    str(date.strftime("%b-%Y")): float(val)
                    for date, val in monthly_sales.items()
                }
                visualization = create_timeseries_line(
                    monthly_dict, title="Sales Trend - Monthly"
                )
                print(f"[Sales Agent] Time series visualization created")

            # Fallbacks
            elif "month" in df.columns:
                df_temp = df.copy()
                df_temp["month_parsed"] = df_temp["month"].apply(
                    parse_month_flexible
                )
                df_temp = df_temp.dropna(subset=["month_parsed"])
                df_temp = df_temp.sort_values("month_parsed")
                monthly_sales = df_temp.groupby(
                    "month_parsed"
                )[sales_col].sum()
                monthly_dict = {
                    str(date.strftime("%b-%Y")): float(val)
                    for date, val in monthly_sales.items()
                }
                visualization = create_timeseries_line(
                    monthly_dict, title="Sales Trend - Monthly"
                )

            elif "region" in df.columns:
                region_sales = df.groupby("region")[sales_col].sum().to_dict()
                visualization = create_category_bar(
                    region_sales, title="Sales by Region"
                )

            elif "product" in df.columns:
                product_sales = df.groupby("product")[sales_col].sum().to_dict()
                visualization = create_category_bar(
                    product_sales, title="Sales by Product"
                )

        except Exception as e:
            print(f"[Sales Agent] Visualization generation error: {str(e)}")
            import traceback
            traceback.print_exc()

    return {
        "agent":         "Sales Analyst",
        "query":         query,
        "metrics":       trends,
        "response":      response,
        "visualization": visualization,
    }