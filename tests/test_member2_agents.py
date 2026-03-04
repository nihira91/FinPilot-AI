# tests/test_member2_agents.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from agents.financial_agent import compute_metrics, run as financial_run
from agents.sales_agent import compute_trends, run as sales_run


def test_financial_metrics():
    print("\n── Test 1: Financial Metrics ──")
    df = pd.DataFrame([{
        "revenue": 2000,
        "cogs": 800,
        "expenses": 300
    }])
    metrics = compute_metrics(df)
    assert metrics["gross_profit"] == 1200
    assert metrics["net_income"] == 900
    print(f"✅ Metrics correct: {metrics}")


def test_sales_trends():
    print("\n── Test 2: Sales Trends ──")
    df = pd.DataFrame({"sales": [100, 150, 200]})
    trends = compute_trends(df)
    assert trends["count"] == 3
    assert trends["next_prediction"] is not None
    assert trends["simple_growth_rate"] == 1.0
    print(f"✅ Trends correct: {trends}")


def test_financial_agent_full():
    print("\n── Test 3: Financial Agent Full Run ──")
    result = financial_run("What is our financial performance?")
    assert result["agent"] == "Financial Analyst"
    assert len(result["response"]) > 50
    print(f"✅ Financial Agent working")
    print(f"   Response preview: {result['response'][:200]}")


def test_sales_agent_full():
    print("\n── Test 4: Sales Agent Full Run ──")
    result = sales_run("What are our sales trends?")
    assert result["agent"] == "Sales Data Scientist"
    assert len(result["response"]) > 50
    print(f"✅ Sales Agent working")
    print(f"   Response preview: {result['response'][:200]}")


if __name__ == "__main__":
    print("="*50)
    print(" Member 2 Agent Tests")
    print("="*50)

    test_financial_metrics()
    test_sales_trends()
    test_financial_agent_full()
    test_sales_agent_full()

    print("\n" + "="*50)
    print(" All Member 2 tests passed! ✅")
    print("="*50)



