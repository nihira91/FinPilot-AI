"""Financial Analyst Agent

Starter agent that performs basic P&L and budget analysis using pandas,
then passes a summary to an LLM (via LangChain) for interpretation.
If `OPENAI_API_KEY` is not set, the agent returns the analysis and a
placeholder interpretation message so tests can run offline.
"""
from typing import Dict, Any
import os
from pathlib import Path
import pandas as pd
import numpy as np
from dotenv import load_dotenv

load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_API_KEY")


class FinancialAnalystAgent:
    def __init__(self, llm_api_key: str = None):
        # Prefer explicit key, fallback to env
        self.api_key = llm_api_key or OPENAI_KEY

    def _compute_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        # Expecting columns: revenue, cogs, expenses (numbers)
        revenue = df["revenue"].sum() if "revenue" in df.columns else 0.0
        cogs = df["cogs"].sum() if "cogs" in df.columns else 0.0
        expenses = df["expenses"].sum() if "expenses" in df.columns else 0.0

        gross_profit = revenue - cogs
        net_income = gross_profit - expenses

        metrics = {
            "total_revenue": float(revenue),
            "total_cogs": float(cogs),
            "total_expenses": float(expenses),
            "gross_profit": float(gross_profit),
            "net_income": float(net_income),
        }
        return metrics

    def _llm_interpret(self, summary: str) -> str:
        # Minimal LangChain usage placeholder: only runs when API key present
        if not self.api_key:
            return (
                "LLM not configured. Set OPENAI_API_KEY in your .env to enable "
                "natural language interpretation."
            )

        try:
            # Import lazily to avoid raising if langchain isn't installed during tests
            from langchain.llms import OpenAI
            from langchain import PromptTemplate, LLMChain

            llm = OpenAI(openai_api_key=self.api_key, temperature=0.2)
            template = "Analyze the following financial summary and provide insights and recommendations:\n\n{summary}"
            prompt = PromptTemplate(template=template, input_variables=["summary"]) 
            chain = LLMChain(llm=llm, prompt=prompt)
            resp = chain.run({"summary": summary})
            return resp
        except Exception as e:
            return f"LLM invocation failed: {e}"

    def analyze_financials(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze a DataFrame of financial rows and return metrics + interpretation.

        Args:
            data: pd.DataFrame with columns like `revenue`, `cogs`, `expenses`.

        Returns:
            dict with `metrics` and `interpretation` keys.
        """
        metrics = self._compute_metrics(data)
        summary_lines = [f"{k}: {v}" for k, v in metrics.items()]
        summary = "\n".join(summary_lines)
        interpretation = self._llm_interpret(summary)

        return {"metrics": metrics, "interpretation": interpretation}


if __name__ == "__main__":
    # quick local demo
    df = pd.DataFrame([{"revenue": 1000, "cogs": 400, "expenses": 200}])
    agent = FinancialAnalystAgent()
    print(agent.analyze_financials(df))
