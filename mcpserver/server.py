import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from dotenv import load_dotenv

from rag.pipeline import rag_query, format_context
from agents.investment_strategist import run as investment_run
from orchestrator.orchestrator_agent import call_gemini, build_graph

load_dotenv()

app = Server("finpilot-ai")


# ── List Available Tools ──────────────────────────────────
@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="orchestrate",
            description="Main orchestrator. Routes query to correct agent and returns consolidated output.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Financial query"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="investment_agent",
            description="Investment Strategist. Analyses consultant reports and provides strategic recommendations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Investment query"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="financial_agent",
            description="Financial Analyst. Analyses financial reports, profit/loss, budget forecasting.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Financial query"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="sales_agent",
            description="Sales Data Scientist. Analyses sales trends, patterns, growth predictions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Sales query"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="cloud_agent",
            description="Cloud Architect. Recommends AWS/GCP infrastructure and scalability.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Cloud query"}
                },
                "required": ["query"]
            }
        ),
    ]


# ── Call Tools ────────────────────────────────────────────
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    query = arguments.get("query", "")

    if name == "orchestrate":
        graph = build_graph()
        result = graph.invoke({"query": query})
        response = result["final_output"]

    elif name == "investment_agent":
        result = investment_run(query)
        response = result["response"]

    elif name == "financial_agent":
        chunks = rag_query("financial_reports", query, top_k=5)
        context = format_context(chunks)
        prompt = f"""You are a Financial Analyst AI.
CONTEXT:
{context}
QUERY: {query}
Respond with:
## Financial Summary
## Key Metrics
## Budget Forecast
## Recommendations"""
        response = call_gemini(prompt)

    elif name == "sales_agent":
        chunks = rag_query("sales_reports", query, top_k=5)
        context = format_context(chunks)
        prompt = f"""You are a Sales Data Scientist AI.
CONTEXT:
{context}
QUERY: {query}
Respond with:
## Sales Summary
## Trend Analysis
## Data-Driven Recommendations"""
        response = call_gemini(prompt)

    elif name == "cloud_agent":
        chunks = rag_query("cloud_docs", query, top_k=5)
        context = format_context(chunks)
        prompt = f"""You are a Cloud Architect AI.
CONTEXT:
{context}
QUERY: {query}
Respond with:
## Infrastructure Summary
## Architecture Recommendations
## Cost Optimisation
## Scalability Roadmap"""
        response = call_gemini(prompt)

    else:
        response = f"Unknown tool: {name}"

    return [TextContent(type="text", text=response)]


# ── Run Server ────────────────────────────────────────────
async def main():
    print("[MCP Server] Starting FinPilot-AI MCP Server...")
    print("[MCP Server] Tools: orchestrate, investment_agent, financial_agent, sales_agent, cloud_agent")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())