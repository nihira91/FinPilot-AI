"""Comparison script: single LLM vs multi-agent (Member 2) pipeline.

This script demonstrates running a single LLM prompt and running the
two Member 2 agents, printing both outputs for easy comparison.
"""
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

from member2.agents.financial_analyst_agent import FinancialAnalystAgent
from member2.agents.sales_data_scientist_agent import SalesDataScientistAgent
from member2.utils.rag_connector import get_rag_pipeline


def run_single_llm(summary_text: str) -> str:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return "OPENAI_API_KEY not set; single-LLM run skipped."
    try:
        from langchain.llms import OpenAI
        llm = OpenAI(openai_api_key=key, temperature=0.2)
        return llm(summary_text)
    except Exception as e:
        return f"Single LLM invocation failed: {e}"


def main():
    # Sample data
    fin_df = pd.DataFrame([{"revenue": 5000, "cogs": 2000, "expenses": 800}])
    sales_df = pd.DataFrame({"sales": [400, 450, 500, 600]})

    # Try RAG connector (if available) - placeholder behavior
    rag = get_rag_pipeline()
    if rag:
        print("Using shared RAG pipeline from Member 3 (not implemented here).")

    # Run agents
    fa_agent = FinancialAnalystAgent()
    sd_agent = SalesDataScientistAgent()

    fa_out = fa_agent.analyze_financials(fin_df)
    sd_out = sd_agent.analyze_sales(sales_df)

    # Prepare single-LLM prompt (simple concatenation)
    summary_text = "Financial Summary:\n" + "\n".join([f"{k}: {v}" for k, v in fa_out["metrics"].items()])
    summary_text += "\n\nSales Summary:\n" + "\n".join([f"{k}: {v}" for k, v in sd_out["metrics"].items()])

    single_llm_resp = run_single_llm(summary_text)

    print("--- Single-LLM Output ---")
    print(single_llm_resp)
    print("--- Multi-Agent Outputs ---")
    print("FinancialAgent:")
    print(fa_out)
    print("SalesDataScientistAgent:")
    print(sd_out)


if __name__ == "__main__":
    main()
