import os
from typing import TypedDict, Literal
from dotenv import load_dotenv
from google import genai
from google.genai import types
from langgraph.graph import StateGraph, END
from rag.pipeline import rag_query, format_context, build_collection
from agents.investment_strategist import run as investment_run
from agents.financial_agent import run as financial_run
from agents.sales_agent import run as sales_run

load_dotenv()

MODEL_ID = "gemini-2.5-flash"

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


# ── Agent State ───────────────────────────────────────────
class AgentState(TypedDict):
    query: str
    route: str
    investment_output: str
    financial_output: str
    sales_output: str
    cloud_output: str
    final_output: str


# ── Orchestrator Node ─────────────────────────────────────
def orchestrator_node(state: AgentState):
    query = state["query"]
    print(f"\n[Orchestrator] Query received: {query}")

    # Use RAG on routing_rules collection
    chunks = rag_query("routing_rules", query, top_k=3)
    context = format_context(chunks)

    prompt = f"""You are an orchestrator of a financial AI system.
Based on the query and routing rules below, decide which agent to call.

ROUTING RULES CONTEXT:
{context}

QUERY: {query}

Available agents:
- financial: for profit/loss, budget, stock analysis
- sales: for sales trends, patterns, growth
- investment: for strategy documents, consultant reports
- cloud: for infrastructure, AWS/GCP recommendations
- all: if query needs multiple agents

Respond with ONLY one word: financial, sales, investment, cloud, or all"""

    route = call_gemini(prompt).lower().strip()
    
    # Clean route in case model adds extra text
    for option in ["financial", "sales", "investment", "cloud", "all"]:
        if option in route:
            route = option
            break
    
    print(f"[Orchestrator] Routing to: {route}")
    return {"route": route}


# ── Router Function ───────────────────────────────────────
def route_query(state: AgentState) -> Literal[
    "financial", "sales", "investment", "cloud", "all_agents"
]:
    route = state["route"]
    if route == "all":
        return "all_agents"
    if route not in ["financial", "sales", "investment", "cloud"]:
        return "investment"  # default fallback
    return route


# ── Agent Nodes ───────────────────────────────────────────
def investment_node(state: AgentState):
    print("[Investment Agent] Running...")
    result = investment_run(state["query"])
    return {"investment_output": result["response"]}


def financial_node(state: AgentState):
    print("[Financial Agent] Running...")
    result = financial_run(state["query"])
    return {"financial_output": result["response"]}


def sales_node(state: AgentState):
    print("[Sales Agent] Running...")
    result = sales_run(state["query"])
    return {"sales_output": result["response"]}


def cloud_node(state: AgentState):
    print("[Cloud Agent] Running...")
    chunks = rag_query("cloud_docs", state["query"], top_k=5)
    context = format_context(chunks)
    prompt = f"""You are a Cloud Architect AI.
Analyse the following context and answer the query.

CONTEXT:
{context}

QUERY: {state["query"]}

Respond with:
## Infrastructure Summary
## Architecture Recommendations
## Cost Optimisation
## Scalability Roadmap"""
    response = call_gemini(prompt)
    return {"cloud_output": response}


def all_agents_node(state: AgentState):
    print("[All Agents] Running all agents...")
    
    # Investment
    inv_result = investment_run(state["query"])
    
    # Financial
    fin_chunks = rag_query("financial_reports", state["query"], top_k=3)
    fin_context = format_context(fin_chunks)
    fin_response = call_gemini(f"You are a Financial Analyst AI.\n\nCONTEXT:\n{fin_context}\n\nQUERY: {state['query']}\n\nProvide financial analysis.")
    
    # Sales
    sales_chunks = rag_query("sales_reports", state["query"], top_k=3)
    sales_context = format_context(sales_chunks)
    sales_response = call_gemini(f"You are a Sales Data Scientist AI.\n\nCONTEXT:\n{sales_context}\n\nQUERY: {state['query']}\n\nProvide sales analysis.")
    
    # Cloud
    cloud_chunks = rag_query("cloud_docs", state["query"], top_k=3)
    cloud_context = format_context(cloud_chunks)
    cloud_response = call_gemini(f"You are a Cloud Architect AI.\n\nCONTEXT:\n{cloud_context}\n\nQUERY: {state['query']}\n\nProvide cloud recommendations.")
    
    return {
        "investment_output": inv_result["response"],
        "financial_output": fin_response,
        "sales_output": sales_response,
        "cloud_output": cloud_response,
    }


# ── Aggregator Node ───────────────────────────────────────
def aggregator_node(state: AgentState):
    print("[Aggregator] Combining results...")
    
    parts = []
    if state.get("financial_output"):
        parts.append(f"=== FINANCIAL ANALYSIS ===\n{state['financial_output']}")
    if state.get("sales_output"):
        parts.append(f"=== SALES ANALYSIS ===\n{state['sales_output']}")
    if state.get("investment_output"):
        parts.append(f"=== INVESTMENT STRATEGY ===\n{state['investment_output']}")
    if state.get("cloud_output"):
        parts.append(f"=== CLOUD RECOMMENDATION ===\n{state['cloud_output']}")

    combined = "\n\n".join(parts)

    # Final summary using Gemini
    summary_prompt = f"""You are a Financial Intelligence Aggregator.
Combine these agent outputs into one executive summary with key action points.

{combined}

Provide:
## Executive Summary
## Key Action Points
## Next Steps"""

    final = call_gemini(summary_prompt)
    return {"final_output": final}


# ── Build Graph ───────────────────────────────────────────
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("financial", financial_node)
    graph.add_node("sales", sales_node)
    graph.add_node("investment", investment_node)
    graph.add_node("cloud", cloud_node)
    graph.add_node("all_agents", all_agents_node)
    graph.add_node("aggregator", aggregator_node)

    graph.set_entry_point("orchestrator")

    graph.add_conditional_edges(
        "orchestrator",
        route_query,
        {
            "financial": "financial",
            "sales": "sales",
            "investment": "investment",
            "cloud": "cloud",
            "all_agents": "all_agents"
        }
    )

    graph.add_edge("financial", "aggregator")
    graph.add_edge("sales", "aggregator")
    graph.add_edge("investment", "aggregator")
    graph.add_edge("cloud", "aggregator")
    graph.add_edge("all_agents", "aggregator")
    graph.add_edge("aggregator", END)

    return graph.compile()

streamlit_app.py
