import pandas as pd
from member2.agents.financial_analyst_agent import FinancialAnalystAgent


def test_financial_agent_basic():
    df = pd.DataFrame([{"revenue": 2000, "cogs": 800, "expenses": 300}])
    agent = FinancialAnalystAgent()
    result = agent.analyze_financials(df)
    assert "metrics" in result
    assert "gross_profit" in result["metrics"]
    assert result["metrics"]["gross_profit"] == 1200
    assert "interpretation" in result
