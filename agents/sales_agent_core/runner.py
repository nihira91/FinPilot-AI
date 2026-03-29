import pandas as pd

from .formatter import build_trends_text
from .helpers import validate_response
from .llm_client import call_gemini
from .metrics import compute_trends
from .visualization import VISUALIZATION_AVAILABLE, build_visualization


PROMPT_TEMPLATE = """
You are a Sales Analyst providing data-driven insights to business stakeholders.

The COMPLETE dataset breakdown is provided below including ALL months, years,
regions and products. Use this data to answer the user's question precisely.

COMPLETE SALES DATA:
{trends_text}

USER QUESTION:
{query}

ANALYSIS INSTRUCTIONS:
1. Use the exact data provided above - do NOT say data is unavailable
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


def run(query: str, df: pd.DataFrame = None, column_mapping: dict = None):
    if not query:
        raise ValueError("Query is empty")

    print(f"\n[Sales Agent] Query: {query}")

    trends = {}
    trends_text = "No CSV data uploaded"

    if df is not None and not df.empty:
        trends = compute_trends(df, column_mapping)
        trends_text = build_trends_text(trends)

    prompt = PROMPT_TEMPLATE.format(trends_text=trends_text, query=query)

    response = call_gemini(prompt)
    response = validate_response(response, trends)

    visualization = None
    if VISUALIZATION_AVAILABLE and df is not None and not df.empty:
        try:
            visualization = build_visualization(query, df, column_mapping)
        except Exception as e:
            print(f"[Sales Agent] Visualization generation error: {str(e)}")
            import traceback

            traceback.print_exc()

    return {
        "agent": "Sales Analyst",
        "query": query,
        "metrics": trends,
        "response": response,
        "visualization": visualization,
    }
