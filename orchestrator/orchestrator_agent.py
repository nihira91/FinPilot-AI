import os
from typing import TypedDict
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


def call_gemini(prompt: str, max_tokens: int = 8192) -> str:
    token = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=token)
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=max_tokens,
        )
    )
    return response.text.strip()


# ── Agent State ───────────────────────────────────────────
from typing import Optional
import pandas as pd

class AgentState(TypedDict, total=False):
    query: str
    route: str
    routes: list
    financial_csv: Optional[pd.DataFrame]
    sales_csv: Optional[pd.DataFrame]
    financial_column_mapping: Optional[dict]
    sales_column_mapping: Optional[dict]
    investment_output: str
    financial_output: str
    sales_output: str
    cloud_output: str
    final_output: str


# ── Orchestrator Node ─────────────────────────────────────
def orchestrator_node(state: AgentState):
    query = state["query"]
    
    # ── Ensure query is valid string ──
    if query is None:
        raise ValueError("Query is None - should not reach here")
    query = str(query).strip()
    
    if not query:
        raise ValueError("Query is empty - should not reach here")
    
    print(f"\n[Orchestrator] Query received: {query}")

    chunks  = rag_query("routing_rules", query, top_k=5)
    context = format_context(chunks)

    prompt = f"""You are an orchestrator of a financial AI system.
Based on the routing rules and the query, decide which agents are needed.

ROUTING RULES AND EXAMPLES:
{context}

QUERY: {query}

Respond with ONLY agent names separated by comma. Nothing else.
Example: financial
Example: financial,investment"""
    response = call_gemini(prompt, max_tokens=100).lower().strip()

    valid  = ["financial", "sales", "investment", "cloud"]
    routes = [r.strip() for r in response.split(",") if r.strip() in valid]

    # ── Ambiguous fallback ────────────────────────────────
    if not routes:
        print("[Orchestrator] Ambiguous query — defaulting to financial,sales,investment")
        routes = ["financial", "sales", "investment"]

    # ── Safety keyword check ──────────────────────────────
    query_lower = query.lower()

    sales_keywords = ["sales", "revenue growth", "region", "product performance", "seasonal"]
    inv_keywords   = ["investment", "strategy", "consultant", "expansion", "strategic", "portfolio", "risks", "opportunities", "reports"]
    fin_keywords   = ["financial", "profit", "budget", "expenses", "cost", "p&l", "quarterly"]
    cloud_keywords = ["cloud", "aws", "gcp", "infrastructure", "scalab", "deployment"]

    if any(k in query_lower for k in sales_keywords) and "sales" not in routes:
        routes.append("sales")
    if any(k in query_lower for k in inv_keywords) and "investment" not in routes:
        routes.append("investment")
    if any(k in query_lower for k in fin_keywords) and "financial" not in routes:
        routes.append("financial")
    if any(k in query_lower for k in cloud_keywords) and "cloud" not in routes:
        routes.append("cloud")

    route = "multi_agent" if len(routes) > 1 else routes[0]

    print(f"[Orchestrator] Routing to: {routes}")
    return {"route": route, "routes": routes}


  

# ── Router Function ───────────────────────────────────────
def route_query(state: AgentState) -> str:
    routes = state.get("routes", [])
    route  = state.get("route", "financial")

    if len(routes) > 1:
        return "multi_agent"
    if route not in ["financial", "sales", "investment", "cloud"]:
        return "financial"
    return route


# ── Single Agent Nodes ────────────────────────────────────
def investment_node(state: AgentState):
    print("[Investment Agent] Running...")
    result = investment_run(state["query"])
    return {"investment_output": result["response"]}


def financial_node(state: AgentState):
    print("[Financial Agent] Running...")
    csv_data = state.get("financial_csv")
    column_mapping = state.get("financial_column_mapping")
    result = financial_run(state["query"], df=csv_data, column_mapping=column_mapping)
    return {"financial_output": result["response"]}


def sales_node(state: AgentState):
    print("[Sales Agent] Running...")
    csv_data = state.get("sales_csv")
    column_mapping = state.get("sales_column_mapping")
    result = sales_run(state["query"], df=csv_data, column_mapping=column_mapping)
    return {"sales_output": result["response"]}


def cloud_node(state: AgentState):
    print("[Cloud Agent] Running...")
    result = cloud_run(state["query"])
    return {"cloud_output": result["response"]}


# ── Multi Agent Node (only required agents) ───────────────
def multi_agent_node(state: AgentState):
    routes  = state.get("routes", [])
    updates = {}

    print(f"[Multi-Agent] Running agents: {routes}")

    if "financial" in routes:
        print("[Financial Agent] Running...")
        csv_data = state.get("financial_csv")
        column_mapping = state.get("financial_column_mapping")
        result = financial_run(state["query"], df=csv_data, column_mapping=column_mapping)
        updates["financial_output"] = result["response"]

    if "sales" in routes:
        print("[Sales Agent] Running...")
        csv_data = state.get("sales_csv")
        column_mapping = state.get("sales_column_mapping")
        result = sales_run(state["query"], df=csv_data, column_mapping=column_mapping)
        updates["sales_output"] = result["response"]

    if "investment" in routes:
        print("[Investment Agent] Running...")
        result = investment_run(state["query"])
        updates["investment_output"] = result["response"]

    if "cloud" in routes:
        print("[Cloud Agent] Running...")
        chunks  = rag_query("cloud_docs", state["query"], top_k=5)
        context = format_context(chunks)
        prompt  = f"""You are a Cloud Architect AI.
CONTEXT: {context}
QUERY: {state["query"]}
Respond with:
## Infrastructure Summary
## Architecture Recommendations
## Cost Optimisation
## Scalability Roadmap"""
        updates["cloud_output"] = call_gemini(prompt)

    return updates


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
    graph.add_node("financial",    financial_node)
    graph.add_node("sales",        sales_node)
    graph.add_node("investment",   investment_node)
    graph.add_node("cloud",        cloud_node)
    graph.add_node("multi_agent",  multi_agent_node)
    graph.add_node("aggregator",   aggregator_node)

    graph.set_entry_point("orchestrator")

    graph.add_conditional_edges(
        "orchestrator",
        route_query,
        {
            "financial":  "financial",
            "sales":      "sales",
            "investment": "investment",
            "cloud":      "cloud",
            "multi_agent": "multi_agent",
        }
    )

    graph.add_edge("financial",   "aggregator")
    graph.add_edge("sales",       "aggregator")
    graph.add_edge("investment",  "aggregator")
    graph.add_edge("cloud",       "aggregator")
    graph.add_edge("multi_agent", "aggregator")
    graph.add_edge("aggregator",  END)

    return graph.compile()

