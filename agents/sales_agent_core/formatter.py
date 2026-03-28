from .helpers import safe_format_value


def build_trends_text(trends: dict) -> str:
    if "error" in trends:
        return f"Error: {trends['error']}"

    lines = []

    # Sales column used.
    if "sales_column_used" in trends:
        lines.append(f"Sales Column Used: {trends['sales_column_used']}")

    # Date range.
    if "date_range" in trends:
        lines.append(
            f"Data Range: {trends['date_range']['earliest']} "
            f"to {trends['date_range']['latest']}"
        )

    # Available years.
    if "available_years" in trends:
        years_str = ", ".join(map(str, trends["available_years"]))
        lines.append(f"Years in Dataset: {years_str}")

    # Basic metrics.
    lines.append("\n--- OVERALL METRICS ---")
    for key in ["total", "mean", "median", "min", "max"]:
        if key in trends:
            lines.append(f"{key.title()}: {safe_format_value(trends[key])}")

    if "growth_rate" in trends:
        lines.append(f"Avg Growth Rate: {safe_format_value(trends['growth_rate'])}%")

    if "next_prediction" in trends and trends["next_prediction"]:
        lines.append(
            f"Next Period Prediction: {safe_format_value(trends['next_prediction'])}"
        )

    # Yearly breakdown.
    if "yearly_breakdown" in trends:
        lines.append("\n--- YEARLY SALES ---")
        for year, val in sorted(trends["yearly_breakdown"].items()):
            lines.append(f"  {year}: {safe_format_value(val)}")

    # Monthly breakdown.
    if "period_breakdown" in trends and trends["period_breakdown"]:
        lines.append(f"\n--- MONTHLY SALES ({len(trends['period_breakdown'])} months) ---")
        for month, sales in trends["period_breakdown"].items():
            lines.append(f"  {month}: {safe_format_value(sales)}")

    # Region breakdown.
    if "region_breakdown" in trends:
        lines.append("\n--- SALES BY REGION ---")
        for region, val in sorted(trends["region_breakdown"].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {region}: {safe_format_value(val)}")

    # Product breakdown.
    if "product_breakdown" in trends:
        lines.append("\n--- SALES BY PRODUCT ---")
        for product, val in sorted(trends["product_breakdown"].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {product}: {safe_format_value(val)}")

    # Categorical metadata.
    if "categorical_metadata" in trends and trends["categorical_metadata"]:
        lines.append("\n--- AVAILABLE CATEGORIES ---")
        for col, values in trends["categorical_metadata"].items():
            lines.append(f"  {col.upper()}: {', '.join(map(str, values))}")

    return "\n".join(lines)
