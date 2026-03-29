def detect_chart_intent(query: str, chart_intent_keywords: dict) -> str:
    """Detect chart intent from query using semantic keywords."""
    query_lower = query.lower()
    for intent, keywords in chart_intent_keywords.items():
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


def validate_response_against_metrics(response: str, metrics: dict, query: str = "") -> str:
    """
    Validate that LLM response doesn't introduce hallucinated data.
    Ensures only computed metrics are used.
    """
    if not metrics or not response:
        return response

    hallucination_warnings = []

    # If no metrics were computed but response claims specific numbers.
    has_numeric_metrics = any(isinstance(v, (int, float)) and v > 0 for v in metrics.values())

    if not has_numeric_metrics:
        if any(keyword in response.lower() for keyword in ["$", "revenue", "profit", "expenses", "costs", "income"]):
            hallucination_warnings.append("\n⚠️ WARNING: Financial numbers claimed but no CSV metrics were computed. Using document knowledge only.")

    if hallucination_warnings:
        return response + "\n" + "".join(hallucination_warnings)

    return response
