# ─────────────────────────────────────────────────────────────────────────────
# sales_agent.py — Sales & Data Scientist Agent
#
# PURPOSE : Analyse sales trends using Pandas/NumPy and RAG pipeline,
#           then interpret results using Gemini LLM.
#
# HOW ORCHESTRATOR USES THIS:
#   from agents.sales_agent import run
#   result = run("What are our sales trends?")
# ─────────────────────────────────────────────────────────────────────────────

import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types
from rag.pipeline import rag_query, format_context

load_dotenv()

MODEL_ID = "gemini-2.5-flash-preview-04-17"


def call_gemini(prompt: str) -> str:
    token = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=token)
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=1024,
        )
    )
    return response.text.strip()


def compute_trends(df: pd.DataFrame) -> dict:
    """
    Compute sales trends and growth predictions from a DataFrame.
    Expected columns: sales
    """
    if "sales" not in df.columns:
        return {"error": "DataFrame must include 'sales' column"}

    series = df["sales"].astype(float)
    result = {
        "count":  int(series.size),
        "mean":   float(series.mean()),
        "median": float(series.median()),
        "std":    float(series.std()),
    }

    # Growth rate between first and last period
    if series.size >= 2:
        growth = (series.iloc[-1] - series.iloc[0]) / max(series.iloc[0], 1e-9)
        result["simple_growth_rate"] = float(growth)
    else:
        result["simple_growth_rate"] = None

    # Linear regression for next period prediction
    try:
        x      = np.arange(series.size)
        coeffs = np.polyfit(x, series.values, 1)
        slope, intercept = coeffs[0], coeffs[1]
        result.update({
            "slope":           float(slope),
            "intercept":       float(intercept),
            "next_prediction": float(slope * series.size + intercept),
        })
    except Exception:
        result.update({
            "slope":           None,
            "intercept":       None,
            "next_prediction": None,
        })

    return result


def run(query: str, df: pd.DataFrame = None) -> dict:
    """
    Main entry point for Sales & Data Scientist Agent.
    Called by Orchestrator whenever sales analysis is needed.

    Args:
        query : question from Orchestrator
        df    : optional DataFrame with sales data

    Returns:
        {
          "agent"    : "Sales Data Scientist",
          "query"    : original query,
          "metrics"  : computed sales metrics,
          "response" : LLM full analysis
        }
    """
    print(f"\n[Sales Agent] Query received: {query}")

    # Step 1: RAG retrieval from sales_reports collection
    chunks  = rag_query("sales_reports", query, top_k=5)
    context = format_context(chunks)

    # Step 2: Pandas trend analysis on sample/real data
    if df is None:
        df = pd.DataFrame({
            "sales": [400, 450, 500, 600, 700]
        })

    trends      = compute_trends(df)
    trends_text = "\n".join([f"{k}: {v}" for k, v in trends.items()])

    # Step 3: LLM interprets RAG context + trends
    prompt = f"""You are a Sales Data Scientist AI agent in a
multi-agent financial intelligence system.

RETRIEVED CONTEXT FROM DOCUMENTS:
{context}

COMPUTED SALES METRICS:
{trends_text}

QUERY: {query}

Respond using EXACTLY this structure:
## Sales Summary
[2-3 sentence overview of sales performance]

## Trend Analysis
[Bullet list of growth, decline, anomaly patterns]

## Key Correlations
[How sales relate to external factors]

## Data-Driven Recommendations
[Numbered list of specific actions]

## Source References
[List of documents used]"""

    response = call_gemini(prompt)
    print(f"[Sales Agent] Analysis complete.")

    return {
        "agent":    "Sales Data Scientist",
        "query":    query,
        "metrics":  trends,
        "response": response,
    }


if __name__ == "__main__":
    result = run("What are our sales trends this year?")
    print("\n" + "="*50)
    print(result["response"])