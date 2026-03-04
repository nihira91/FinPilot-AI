"""Sales & Data Scientist Agent

Performs trend detection and a simple growth prediction using pandas/numpy,
then optionally asks an LLM (via LangChain) to interpret the findings.
"""
from typing import Dict, Any
import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv

load_dotenv()

OPENAI_KEY = os.getenv("OPENAI_API_KEY")


class SalesDataScientistAgent:
    def __init__(self, llm_api_key: str = None):
        self.api_key = llm_api_key or OPENAI_KEY

    def _compute_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        # Expect a timeseries-like DataFrame with `period` and `sales` columns
        result = {}
        if "sales" not in df.columns:
            return {"error": "DataFrame must include 'sales' column"}

        series = df["sales"].astype(float)
        result["count"] = int(series.size)
        result["mean"] = float(series.mean())
        result["median"] = float(series.median())
        result["std"] = float(series.std())

        # Simple growth rate: percent change between last and first
        if series.size >= 2:
            growth = (series.iloc[-1] - series.iloc[0]) / max(series.iloc[0], 1e-9)
            result["simple_growth_rate"] = float(growth)
        else:
            result["simple_growth_rate"] = None

        # Simple linear trend prediction for next period
        try:
            x = np.arange(series.size)
            coeffs = np.polyfit(x, series.values, 1)
            slope, intercept = coeffs[0], coeffs[1]
            next_pred = float(slope * series.size + intercept)
            result.update({"slope": float(slope), "intercept": float(intercept), "next_prediction": next_pred})
        except Exception:
            result.update({"slope": None, "intercept": None, "next_prediction": None})

        return result

    def _llm_interpret(self, summary: str) -> str:
        if not self.api_key:
            return (
                "LLM not configured. Set OPENAI_API_KEY in your .env to enable "
                "natural language interpretation."
            )

        try:
            from langchain.llms import OpenAI
            from langchain import PromptTemplate, LLMChain

            llm = OpenAI(openai_api_key=self.api_key, temperature=0.2)
            template = "Given the following sales analysis, provide an interpretation and suggested actions:\n\n{summary}"
            prompt = PromptTemplate(template=template, input_variables=["summary"]) 
            chain = LLMChain(llm=llm, prompt=prompt)
            resp = chain.run({"summary": summary})
            return resp
        except Exception as e:
            return f"LLM invocation failed: {e}"

    def analyze_sales(self, data: pd.DataFrame) -> Dict[str, Any]:
        metrics = self._compute_trends(data)
        summary_lines = [f"{k}: {v}" for k, v in metrics.items()]
        summary = "\n".join(summary_lines)
        interpretation = self._llm_interpret(summary)
        return {"metrics": metrics, "interpretation": interpretation}


if __name__ == "__main__":
    df = pd.DataFrame({"sales": [100, 120, 140, 160]})
    agent = SalesDataScientistAgent()
    print(agent.analyze_sales(df))
