from .constants import CHART_INTENT_KEYWORDS


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
