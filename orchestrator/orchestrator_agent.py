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
class AgentState(TypedDict):
    query: str
    route: str
    routes: list
    investment_output: str
    financial_output: str
    sales_output: str
    cloud_output: str
    final_output: str


# ── Orchestrator Node ─────────────────────────────────────
def orchestrator_node(state: AgentState):
    query = state["query"]
    print(f"\n[Orchestrator] Query received: {query}")

    chunks  = rag_query("routing_rules", query, top_k=3)
    context = format_context(chunks)

    prompt = f"""You are an orchestrator of a financial AI system.
Based on the query, decide which agents are needed.

ROUTING RULES CONTEXT:
{context}

QUERY: {query}

Available agents:
- financial: revenue, profit, budget, expenses, P&L, cost, margins,
             quarterly performance, profitability, financial data,
             financial summary, cost anomalies, marketing spend
             
- sales: sales trends, sales growth, sales patterns, sales predictions,
         region sales, seasonal sales, product performance, sales anomalies,
         sales strategies, factors influencing sales, historical sales data
         
- investment: investment strategy, portfolio, consultant reports,
              strategy documents, expansion strategy, growth strategy,
              market opportunities, competitive advantages, risks,
              strategic recommendations, 3 year plan, capital deployment,
              business strategy, future plans, market expansion
              
- cloud: AWS, GCP, cloud architecture, infrastructure, deployment,
         scalability, SaaS, DevOps, high availability, cloud costs,
         server, AI workloads, traffic handling, cloud services

ROUTING RULES:
- "quarterly performance" / "profit" / "revenue" / "budget" / 
  "expenses" / "cost" / "P&L" / "profitability" / "financial data"
  → financial

- "sales trend" / "sales growth" / "region sales" / "seasonal" /
  "product performance" / "sales pattern" / "sales prediction"
  → sales

- "consultant reports" / "strategy documents" / "expansion strategy" /
  "growth strategy" / "investment opportunities" / "risks" /
  "strategic recommendations" / "competitive advantages" /
  "markets for expansion" / "3 years" / "business strategy"
  → investment

- "cloud" / "AWS" / "GCP" / "infrastructure" / "scalable" /
  "deployment" / "SaaS" / "high availability" / "traffic"
  → cloud

- If query mentions BOTH financial AND investment topics
  → financial,investment

- If query mentions BOTH sales AND financial topics
  → financial,sales

- If query mentions BOTH sales AND investment topics
  → sales,investment

- If query mentions financial AND strategy/expansion
  → financial,investment

- If query mentions sales AND infrastructure/scaling
  → sales,cloud

- If query mentions company performance broadly (3+ domains)
  → financial,sales,investment

- If query mentions complete business intelligence
  → financial,sales,investment,cloud

EXAMPLES:
"Analyze the company's quarterly financial performance" → financial
"What is the profit trend over the last four quarters" → financial
"Identify which quarter had the highest expenses" → financial
"Suggest ways to improve profitability based on financial data" → financial
"Predict next quarter revenue based on previous trends" → financial
"What percentage of revenue is being spent on marketing" → financial
"Identify cost anomalies in the financial data" → financial
"Provide a financial summary for the last year" → financial

"Analyze the sales growth trend over the past year" → sales
"Which region generated the highest sales" → sales
"Identify seasonal sales patterns in the dataset" → sales
"Predict future sales based on historical data" → sales
"Detect anomalies in the sales data" → sales
"Which product category is performing best" → sales
"Suggest strategies to increase sales in low performing regions" → sales
"Identify factors influencing sales growth" → sales

"Summarize the key insights from the consultant reports" → investment
"Suggest an expansion strategy based on the strategy documents" → investment
"Identify potential investment opportunities mentioned in the reports" → investment
"What risks are highlighted in the consultant analysis" → investment
"What markets are recommended for expansion" → investment
"Summarize growth strategies discussed in the reports" → investment
"Identify competitive advantages mentioned in the documents" → investment
"Provide strategic recommendations for the next 3 years" → investment

"Recommend a scalable cloud architecture for 1 million users" → cloud
"Suggest AWS services suitable for a data analytics platform" → cloud
"Provide a cost optimized cloud deployment strategy" → cloud
"Design a scalable infrastructure for a growing SaaS application" → cloud
"What cloud services should be used for high availability" → cloud
"Suggest a deployment architecture for AI workloads" → cloud
"Recommend ways to reduce cloud costs" → cloud
"Design an architecture for handling high traffic during peak sales" → cloud

"Analyze our financial performance and suggest an expansion strategy" → financial,investment
"Based on sales trends and financial data recommend a growth plan" → financial,sales,investment
"Evaluate company performance and suggest infrastructure scaling" → financial,sales,cloud
"Analyze quarterly sales and recommend investment opportunities" → sales,investment
"Provide a complete business intelligence report for the company" → financial,sales,investment,cloud
"Identify growth opportunities based on financial and strategy documents" → financial,investment
"Suggest a business expansion strategy supported by financial analysis" → financial,investment
"Analyze company data and recommend infrastructure improvements" → financial,sales,cloud

Respond with ONLY agent names separated by comma. Nothing else.
Example: financial
Example: financial,investment
Example: financial,sales,investment"""
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
    result = financial_run(state["query"])
    return {"financial_output": result["response"]}


def sales_node(state: AgentState):
    print("[Sales Agent] Running...")
    result = sales_run(state["query"])
    return {"sales_output": result["response"]}


def cloud_node(state: AgentState):
    print("[Cloud Agent] Running...")
    chunks  = rag_query("cloud_docs", state["query"], top_k=5)
    context = format_context(chunks)
    prompt  = f"""You are a Cloud Architect AI.
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


# ── Multi Agent Node (only required agents) ───────────────
def multi_agent_node(state: AgentState):
    routes  = state.get("routes", [])
    updates = {}

    print(f"[Multi-Agent] Running agents: {routes}")

    if "financial" in routes:
        print("[Financial Agent] Running...")
        result = financial_run(state["query"])
        updates["financial_output"] = result["response"]

    if "sales" in routes:
        print("[Sales Agent] Running...")
        result = sales_run(state["query"])
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

