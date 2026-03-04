import pandas as pd
from member2.agents.sales_data_scientist_agent import SalesDataScientistAgent


def test_sales_agent_basic():
    df = pd.DataFrame({"sales": [100, 150, 200]})
    agent = SalesDataScientistAgent()
    result = agent.analyze_sales(df)
    assert "metrics" in result
    assert result["metrics"]["count"] == 3
    assert "next_prediction" in result["metrics"]
    assert "interpretation" in result
