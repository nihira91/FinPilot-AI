

#  Analyse financial data using Pandas and RAG pipeline,
#  then interpret results using Gemini LLM.


#   from agents.financial_agent import run
#   result = run("What is our Q3 profit performance?")


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


def compute_metrics(df: pd.DataFrame) -> dict:
    """
    Compute basic financial metrics from a DataFrame.
    Expected columns: revenue, cogs, expenses
    """
    revenue  = df["revenue"].sum()  if "revenue"  in df.columns else 0.0
    cogs     = df["cogs"].sum()     if "cogs"     in df.columns else 0.0
    expenses = df["expenses"].sum() if "expenses" in df.columns else 0.0

    gross_profit = revenue - cogs
    net_income   = gross_profit - expenses

    return {
        "total_revenue":  float(revenue),
        "total_cogs":     float(cogs),
        "total_expenses": float(expenses),
        "gross_profit":   float(gross_profit),
        "net_income":     float(net_income),
    }


def run(query: str, df: pd.DataFrame = None) -> dict:
    """
    Main entry point for Financial Analyst Agent.
    Called by Orchestrator whenever financial analysis is needed.

    Args:
        query : question from Orchestrator
        df    : optional DataFrame with financial data

    Returns:
        {
          "agent"    : "Financial Analyst",
          "query"    : original query,
          "metrics"  : computed financial metrics,
          "response" : LLM full analysis
        }
    """
    print(f"\n[Financial Agent] Query received: {query}")

    # RAG retrieval from financial_reports collection
    chunks  = rag_query("financial_reports", query, top_k=5)
    context = format_context(chunks)

    # Pandas analysis on sample/real data
    if df is None:
        df = pd.DataFrame([{
            "revenue":  50000,
            "cogs":     20000,
            "expenses":  8000
        }])

    metrics      = compute_metrics(df)
    metrics_text = "\n".join([f"{k}: {v}" for k, v in metrics.items()])

    # LLM interprets RAG context + metrics
    prompt = f"""You are a Financial Analyst AI agent in a
multi-agent financial intelligence system.

RETRIEVED CONTEXT FROM DOCUMENTS:
{context}

COMPUTED FINANCIAL METRICS:
{metrics_text}

QUERY: {query}

Respond using EXACTLY this structure:
## Financial Summary
[2-3 sentence overview]

## Key Metrics
[Bullet list of important numbers]

## Budget Forecast
[Predicted revenue, expenses, profit trends]

## Recommendations
[Numbered list of specific actions]

## Source References
[List of documents used]"""

    response = call_gemini(prompt)
    print(f"[Financial Agent] Analysis complete.")

    return {
        "agent":    "Financial Analyst",
        "query":    query,
        "metrics":  metrics,
        "response": response,
    }


if __name__ == "__main__":
    result = run("What is our Q3 financial performance?")
    print("\n" + "="*50)
    print(result["response"])
