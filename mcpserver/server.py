import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

from agents.investment_strategist import run as investment_run
from agents.financial_agent import run as financial_run
from agents.sales_agent import run as sales_run
from agents.cloud_agent import run as cloud_run
from orchestrator.orchestrator_agent import build_graph

load_dotenv()

app = FastMCP("FinPilot-AI")


@app.tool()
def orchestrate(query: str) -> str:
    """Main orchestrator. Routes query to correct agent and returns consolidated output."""
    graph  = build_graph()
    result = graph.invoke({"query": query})
    return result["final_output"]


@app.tool()
def financial_agent(query: str) -> str:
    """Financial Analyst. Analyses financial reports, profit/loss, budget forecasting."""
    result = financial_run(query)
    return result["response"]


@app.tool()
def sales_agent(query: str) -> str:
    """Sales Data Scientist. Analyses sales trends, patterns, growth predictions."""
    result = sales_run(query)
    return result["response"]


@app.tool()
def investment_agent(query: str) -> str:
    """Investment Strategist. Analyses consultant reports and strategic recommendations."""
    result = investment_run(query)
    return result["response"]


@app.tool()
def cloud_agent(query: str) -> str:
    """Cloud Architect. Recommends AWS/GCP infrastructure and scalability."""
    result = cloud_run(query)
    return result["response"]


if __name__ == "__main__":
    print("[MCP Server] Starting FinPilot-AI MCP Server...")
    print("[MCP Server] Tools: orchestrate, financial_agent, sales_agent, investment_agent, cloud_agent")
    app.run()
