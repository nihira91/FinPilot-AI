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
from agents.cloud_agent import run as cloud_run
from utils.chart_generator import create_breakdown_pie, create_category_bar, create_timeseries_line
import json
import re

load_dotenv()

MODEL_ID = "gemini-2.5-flash"


ROUTING_EXAMPLES = """
ROUTING EXAMPLES:

FINANCIAL AGENT EXAMPLES:
- "Analyze the company's quarterly financial performance" → financial
- "What is the profit trend over the last four quarters" → financial
- "Identify cost anomalies in the financial data" → financial
- "Suggest ways to improve profitability based on financial data" → financial

SALES AGENT EXAMPLES:
- "Analyze the sales growth trend over the past year" → sales
- "Which region generated the highest sales" → sales
- "Identify seasonal sales patterns in the dataset" → sales
- "Detect anomalies in the sales data" → sales

INVESTMENT AGENT EXAMPLES:
- "Summarize the key insights from the consultant reports" → investment
- "Suggest an expansion strategy based on the strategy documents" → investment
- "Identify potential investment opportunities mentioned in the reports" → investment
- "What risks are highlighted in the consultant analysis" → investment

CLOUD AGENT EXAMPLES:
- "Recommend a scalable cloud architecture for 1 million users" → cloud
- "Suggest AWS services suitable for a data analytics platform" → cloud
- "Provide a cost optimized cloud deployment strategy" → cloud
- "Design a scalable infrastructure for a growing SaaS application" → cloud

MULTI-AGENT EXAMPLES:
- "Analyze our financial performance and suggest an expansion strategy" → financial,investment
- "Based on sales trends and financial data recommend a growth plan" → financial,sales,investment
- "Evaluate company performance and suggest infrastructure scaling" → financial,sales,cloud
- "Provide a complete business intelligence report for the company" → financial,sales,investment,cloud
- "Analyze quarterly sales and recommend investment opportunities" → sales,investment
"""


def extract_routes_from_text(text: str) -> list:
    """Extract valid agent names from free-form LLM text while preserving order."""
    lowered = (text or "").lower()
    matches = re.findall(r"\b(financial|sales|investment|cloud)\b", lowered)
    return list(dict.fromkeys(matches))


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


#  Agent State 
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
    model_type: Optional[str]
    investment_output: str
    financial_output: str
    sales_output: str
    cloud_output: str
    final_output: str
    request_visualization: bool
    chart_type: Optional[str]
    visualization_output: Optional[dict]
    agent_info: Optional[dict]
    agent_info_financial: Optional[dict]
    agent_info_sales: Optional[dict]
    agent_info_investment: Optional[dict]
    agent_info_cloud: Optional[dict]
    financial_result: Optional[dict]
    sales_result: Optional[dict]
    investment_result: Optional[dict]
    uploaded_pdf_agents: Optional[list]


# Orchestrator Node 
def orchestrator_node(state: AgentState):
    query = state["query"]
    uploaded_pdf_agents = state.get("uploaded_pdf_agents") or []
    
    # Ensure query is valid string 
    if query is None:
        raise ValueError("Query is None - should not reach here")
    query = str(query).strip()
    
    if not query:
        raise ValueError("Query is empty - should not reach here")
    
    print(f"\n[Orchestrator] Query received: {query}")

    # Orchestrator prompt with examples for routing context
    orchestrator_prompt = f"""
    You are an orchestrator routing user queries to specialized financial agents.
    
    {ROUTING_EXAMPLES}
    
    USER QUERY: {query}
    
    Based on the examples above, decide which agents should handle this query.
    """
    
    # Store prompt in state for reference
    state["orchestrator_prompt"] = orchestrator_prompt

    # RULE-BASED ROUTING (replaces RAG for better accuracy)
    query_lower = query.lower()
    routes = []
    
    # Define comprehensive routing keywords
    financial_keywords = ["financial", "profit", "budget", "expenses", "cost", "p&l", "quarterly", "revenue", "forecast", "cash", "balance", "margin", "profitability", "performance", "revenue trend", "revenue generation"]
    sales_keywords     = ["sales", "region", "product performance", "seasonal", "pattern", "trend", "anomal", "customer", "order", "conversion", "sales growth", "sales trend"]
    investment_keywords = ["investment", "portfolio", "expansion", "strategy", "risk", "consultant", "strategic", "growth", "opportunity", "market", "expansion strategy", "growth strategy"]
    cloud_keywords     = ["cloud", "aws", "gcp", "infrastructure", "scalab", "deployment", "saas", "high availability", "traffic", "scaling"]
    
    # Check for each domain
    found_financial = any(k in query_lower for k in financial_keywords)
    found_sales     = any(k in query_lower for k in sales_keywords)
    found_investment = any(k in query_lower for k in investment_keywords)
    found_cloud     = any(k in query_lower for k in cloud_keywords)
    
    # Multi-domain routing logic (matching your routing rules)
    domain_count = sum([found_financial, found_sales, found_investment, found_cloud])
    
    # If query mentions company performance broadly (3+ domains)
    if domain_count >= 3:
        routes = ["financial", "sales", "investment"]
        print(f"[Orchestrator] Multi-domain query detected (3+ domains) → routing to financial,sales,investment")
    
    # If query mentions complete business intelligence (cloud + others)
    elif found_cloud and domain_count >= 2:
        routes = ["financial", "sales", "investment", "cloud"]
        print(f"[Orchestrator] Business intelligence + cloud → routing to all agents")
    
    # Two-domain combinations
    elif found_financial and found_investment:
        routes = ["financial", "investment"]
        print(f"[Orchestrator] Financial + Investment domains")
    elif found_financial and found_sales:
        routes = ["financial", "sales"]
        print(f"[Orchestrator] Financial + Sales domains")
    elif found_sales and found_investment:
        routes = ["sales", "investment"]
        print(f"[Orchestrator] Sales + Investment domains")
    elif found_sales and found_cloud:
        routes = ["sales", "cloud"]
        print(f"[Orchestrator] Sales + Cloud domains")
    
    # Single domain
    elif found_financial:
        routes = ["financial"]
    elif found_sales:
        routes = ["sales"]
    elif found_investment:
        routes = ["investment"]
    elif found_cloud:
        routes = ["cloud"]
    
    # Final fallback if still no routes matched
    if not routes:
        if uploaded_pdf_agents:
            print(f"[Orchestrator] No keywords matched - defaulting to uploaded PDF agents: {uploaded_pdf_agents}")
            routes = uploaded_pdf_agents
        else:
            print("[Orchestrator] No keywords matched - defaulting to financial,sales,investment")
            routes = ["financial", "sales", "investment"]
    
    # Deduplicate routes
    routes = list(dict.fromkeys(routes))

    route = "multi_agent" if len(routes) > 1 else routes[0]

    print(f"[Orchestrator] Final routing: {routes}")
    return {"route": route, "routes": routes}


  

#  Router Function 
def route_query(state: AgentState) -> str:
    routes = state.get("routes", [])
    route  = state.get("route", "financial")

    if len(routes) > 1:
        return "multi_agent"
    if route not in ["financial", "sales", "investment", "cloud"]:
        return "financial"
    return route


# Single Agent Nodes
def investment_node(state: AgentState):
    print("[Investment Agent] Running...")
    result = investment_run(state["query"])
    return {
        "investment_output": result["response"],
        "investment_result": result,
        "agent_info_investment": {
            "agent": result.get("agent", "Investment Strategist"),
            "agent_domain": result.get("agent_domain", "Investment Strategy & Portfolio Analysis"),
            "data_source": result.get("data_source", "RAG Documents"),
            "confidence": result.get("confidence", "MEDIUM"),
        }
    }


def financial_node(state: AgentState):
    print("[Financial Agent] Running...")
    csv_data = state.get("financial_csv")
    column_mapping = state.get("financial_column_mapping")
    result = financial_run(state["query"], df=csv_data, column_mapping=column_mapping)
    return {
        "financial_output": result["response"],
        "financial_result": result,
        "agent_info_financial": {
            "agent": result.get("agent", "Financial Analyst"),
            "agent_domain": result.get("agent_domain", "Financial Performance Analysis"),
            "data_source": result.get("data_source", "CSV"),
            "confidence": result.get("confidence", "HIGH"),
        }
    }


def sales_node(state: AgentState):
    print("[Sales Agent] Running...")
    csv_data = state.get("sales_csv")
    column_mapping = state.get("sales_column_mapping")
    result = sales_run(state["query"], df=csv_data, column_mapping=column_mapping)
    return {
        "sales_output": result["response"],
        "sales_result": result,
        "agent_info_sales": {
            "agent": result.get("agent", "Sales Analyst"),
            "agent_domain": result.get("agent_domain", "Sales & Revenue Analysis"),
            "data_source": result.get("data_source", "CSV"),
            "confidence": result.get("confidence", "HIGH"),
        }
    }


def cloud_node(state: AgentState):
    print("[Cloud Agent] Running...")
    result = cloud_run(state["query"])
    return {
        "cloud_output": result["response"],
        "agent_info_cloud": {
            "agent": result.get("agent", "Cloud Architect"),
            "agent_domain": result.get("agent_domain", "Cloud Infrastructure & Deployment"),
            "data_source": result.get("data_source", "RAG Documents"),
            "confidence": result.get("confidence", "MEDIUM"),
        }
    }


# Visualization Node
def visualization_node(state: AgentState):
    """
    Generate interactive charts from agent analysis results.
    Combines metrics from multiple agents (financial + sales + investment).
    """
    print("[Visualization] Generating charts...")
    
    charts = []
    all_metrics = {}
    sources = []
    
    # Collect metrics from all available agent results
    if state.get("financial_result") and isinstance(state.get("financial_result"), dict):
        financial_metrics = state.get("financial_result").get("metrics", {})
        if financial_metrics:
            all_metrics.update(financial_metrics)
            sources.append("Financial")
            print(f"[Visualization] ✓ Added {len(financial_metrics)} financial metrics")
    
    if state.get("sales_result") and isinstance(state.get("sales_result"), dict):
        sales_metrics = state.get("sales_result").get("metrics", {})
        if sales_metrics:
            all_metrics.update(sales_metrics)
            sources.append("Sales")
            print(f"[Visualization] ✓ Added {len(sales_metrics)} sales metrics")
    
    if state.get("investment_result") and isinstance(state.get("investment_result"), dict):
        investment_metrics = state.get("investment_result").get("metrics", {})
        if investment_metrics:
            all_metrics.update(investment_metrics)
            sources.append("Investment")
            print(f"[Visualization] ✓ Added {len(investment_metrics)} investment metrics")
    
    source_text = ", ".join(sources) if sources else "Unknown"
    print(f"[Visualization] Total metrics collected: {len(all_metrics)} from {source_text}")
    
    # Generate charts from all collected metrics
    for key, value in all_metrics.items():
        if value is None or not isinstance(value, dict):
            continue
        
        try:
            # Determine chart type and create
            key_lower = key.lower()
            
            if any(x in key_lower for x in ["breakdown", "distribution", "split"]):
                # Breakdown/pie chart
                fig = create_breakdown_pie(value, title=key.replace("_", " ").title())
                if fig:
                    charts.append({
                        "title": key.replace("_", " ").title(),
                        "type": "pie",
                        "plotly_json": fig.to_json()
                    })
                    print(f"[Visualization] ✓ Created pie chart: {key}")
            
            elif any(x in key_lower for x in ["trend", "monthly", "period", "time", "over"]):
                # Time series/line chart
                fig = create_timeseries_line(value, title=key.replace("_", " ").title())
                if fig:
                    charts.append({
                        "title": key.replace("_", " ").title(),
                        "type": "line",
                        "plotly_json": fig.to_json()
                    })
                    print(f"[Visualization] ✓ Created line chart: {key}")
            
            else:
                # Default to bar chart
                fig = create_category_bar(value, title=key.replace("_", " ").title())
                if fig:
                    charts.append({
                        "title": key.replace("_", " ").title(),
                        "type": "bar",
                        "plotly_json": fig.to_json()
                    })
                    print(f"[Visualization] ✓ Created bar chart: {key}")
        
        except Exception as e:
            print(f"[Visualization] ✗ Error creating chart for {key}: {e}")
            continue
    
    print(f"[Visualization] Generated {len(charts)} total charts")
    
    return {
        "visualization_output": {
            "charts": charts,
            "count": len(charts),
            "source": source_text
        }
    }



# Multi Agent Node 
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
        updates["financial_result"] = result

    if "sales" in routes:
        print("[Sales Agent] Running...")
        csv_data = state.get("sales_csv")
        column_mapping = state.get("sales_column_mapping")
        result = sales_run(state["query"], df=csv_data, column_mapping=column_mapping)
        updates["sales_output"] = result["response"]
        updates["sales_result"] = result

    if "investment" in routes:
        print("[Investment Agent] Running...")
        result = investment_run(state["query"])
        updates["investment_output"] = result["response"]
        updates["investment_result"] = result

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


#  Aggregator Node 
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
    result = {"final_output": final}
    
    # Extract and pass the primary agent info (use first available agent's metadata)
    if state.get("agent_info_financial"):
        result["agent_info"] = state["agent_info_financial"]
    elif state.get("agent_info_sales"):
        result["agent_info"] = state["agent_info_sales"]
    elif state.get("agent_info_investment"):
        result["agent_info"] = state["agent_info_investment"]
    elif state.get("agent_info_cloud"):
        result["agent_info"] = state["agent_info_cloud"]
    
    # Pass through agent results for visualization (CSV or PDF data)
    if state.get("financial_result"):
        result["financial_result"] = state["financial_result"]
    if state.get("sales_result"):
        result["sales_result"] = state["sales_result"]
    if state.get("investment_result"):
        result["investment_result"] = state["investment_result"]
    
    # Pass through visualization if it was requested
    if state.get("visualization_output"):
        result["visualization_output"] = state["visualization_output"]
    
    return result


# Build Graph 
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("financial",    financial_node)
    graph.add_node("sales",        sales_node)
    graph.add_node("investment",   investment_node)
    graph.add_node("cloud",        cloud_node)
    graph.add_node("multi_agent",  multi_agent_node)
    graph.add_node("aggregator",   aggregator_node)
    graph.add_node("visualization", visualization_node)

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
    
    # Conditional routing from aggregator to visualization
    def should_visualize(state: AgentState) -> str:
        if state.get("request_visualization"):
            return "visualization"
        return "end"
    
    graph.add_conditional_edges(
        "aggregator",
        should_visualize,
        {
            "visualization": "visualization",
            "end": END,
        }
    )
    
    # Visualization ends the graph
    graph.add_edge("visualization", END)

    return graph.compile()

