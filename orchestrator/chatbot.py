"""
Chatbot orchestrator - Question-driven agent responses.
Minimal orchestration - just route questions to appropriate agents.
"""

import os
from typing import TypedDict, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
import pandas as pd
import json
import re

from rag.pipeline import rag_query, format_context
from agents.financial_agent import run as financial_run
from agents.sales_agent import run as sales_run
from agents.investment_strategist import run as investment_run
from agents.cloud_agent import run as cloud_run
from .orchestrator_agent import orchestrator_node as orchestrator_node_impl

load_dotenv()

MODEL_ID = "gemini-2.5-flash"


def extract_routes_from_text(text: str) -> list:
    """Extract valid agent names from free-form LLM text while preserving order."""
    lowered = (text or "").lower()
    matches = re.findall(r"\b(financial|sales|investment|cloud)\b", lowered)
    # Deduplicate while preserving first-seen order
    return list(dict.fromkeys(matches))


def call_gemini(prompt: str, max_tokens: int = 4096) -> str:
    """Call Gemini API with the given prompt."""
    token = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=token)
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=max_tokens,
        )
    )
    return response.text.strip()


def route_query(query: str, default_agents: Optional[list] = None) -> list:
    """
    Route a query to appropriate agents using orchestrator logic.
    Uses routing_rules.pdf via RAG (same as orchestrator_agent).
    
    Args:
        query: User's question
        
    Returns:
        List of agent names: ["financial"], ["sales"], etc.
    """
    print(f"[Routing] Query: {query}")
    
    try:
        # Use RAG to get routing rules context
        chunks = rag_query("routing_rules", query, top_k=5)
        context = format_context(chunks)
        
        # Use LLM + routing rules to decide agents
        prompt = f"""You are an orchestrator of a financial AI system.
Based on the routing rules and the query, decide which agents are needed.

ROUTING RULES AND EXAMPLES:
{context}

USER QUERY: {query}

Respond with ONLY agent names separated by comma. Nothing else.
Examples:
- "financial" 
- "financial,sales"
- "financial,sales,investment"

Your response:"""
        
        response = call_gemini(prompt, max_tokens=100).strip()
        routes = extract_routes_from_text(response)

        # If user explicitly names domains, preserve those routes.
        for agent in extract_routes_from_text(query):
            if agent not in routes:
                routes.append(agent)
        
        # Fallback to keyword matching if RAG didn't help
        if not routes:
            print(f"[Routing] RAG routing unclear, using keyword fallback")
            keywords = {
                "financial": ["financial", "revenue", "profit", "budget", "expense", "p&l", "quarterly", "margin", "forecast", "cash", "balance", "accounting"],
                "sales": ["sales", "growth", "region", "seasonal", "pattern", "trend", "anomal", "customer", "order", "conversion"],
                "investment": ["consultant", "strategy", "expansion", "investment", "risk", "3-year", "portfolio"],
                "cloud": ["aws", "gcp", "infrastructure", "deploy", "scalab", "cloud", "architecture"],
            }
            
            query_lower = query.lower()
            for agent, kws in keywords.items():
                if any(kw in query_lower for kw in kws):
                    routes.append(agent)
            
            routes = list(dict.fromkeys(routes))
        
        # Fallback if still nothing
        if not routes:
            if default_agents:
                print(f"[Routing] Still ambiguous - defaulting to uploaded PDF agents: {default_agents}")
                routes = list(dict.fromkeys(default_agents))
            else:
                print("[Routing] Still ambiguous - defaulting to financial,sales")
                routes = ["financial", "sales"]
        
        print(f"[Routing] Routed to: {routes}")
        return routes
        
    except Exception as e:
        if default_agents:
            print(f"[Routing] Error in routing: {e}, defaulting to uploaded PDF agents: {default_agents}")
            return list(dict.fromkeys(default_agents))
        print(f"[Routing] Error in routing: {e}, defaulting to financial,sales")
        return ["financial", "sales"]


def get_uploaded_pdf_agents(uploaded_collections: Optional[dict] = None) -> list:
    """Map uploaded PDF collections to agent names, preserving first-seen order."""
    if not uploaded_collections:
        return []

    collection_to_agent = {
        "financial_reports": "financial",
        "sales_reports": "sales",
        "investment_reports": "investment",
        "cloud_docs": "cloud",
    }

    uploaded_agents = []
    for collection_name, file_names in uploaded_collections.items():
        agent_name = collection_to_agent.get(collection_name)
        if not agent_name:
            continue

        has_pdf = any(str(name).lower().endswith(".pdf") for name in (file_names or []))
        if has_pdf and agent_name not in uploaded_agents:
            uploaded_agents.append(agent_name)

    return uploaded_agents


def auto_detect_column_mappings(
    financial_csv: Optional[pd.DataFrame] = None,
    sales_csv: Optional[pd.DataFrame] = None,
    financial_column_mapping: Optional[dict] = None,
    sales_column_mapping: Optional[dict] = None,
) -> tuple:
    """
    Auto-detect column mappings if not provided.
    Returns: (financial_column_mapping, sales_column_mapping)
    """
    
    # Financial mapping auto-detection
    if financial_column_mapping is None and financial_csv is not None:
        financial_column_mapping = {}
        numeric_cols = financial_csv.select_dtypes(include=['number']).columns.tolist()
        
        # Look for revenue column
        for col in financial_csv.columns:
            col_lower = col.lower()
            if 'revenue' in col_lower:
                financial_column_mapping['revenue'] = col
                break
        
        # Look for COGS column
        for col in financial_csv.columns:
            col_lower = col.lower()
            if any(k in col_lower for k in ['cogs', 'cost of goods', 'cost', 'expenses']):
                financial_column_mapping['cogs'] = col
                break
        
        print(f"[Chatbot] Auto-detected financial mapping: {financial_column_mapping}")
    
    # Sales mapping auto-detection
    if sales_column_mapping is None and sales_csv is not None:
        sales_column_mapping = {}
        numeric_cols = sales_csv.select_dtypes(include=['number']).columns.tolist()
        
        # Look for sales/revenue column with priority
        keywords = ["sales", "revenue", "amount", "income", "total", "value"]
        for col in sales_csv.columns:
            col_lower = col.lower()
            if any(k in col_lower for k in keywords):
                if sales_csv[col].dtype in ['int64', 'float64', 'Int64', 'Float64']:
                    sales_column_mapping['sales'] = col
                    break
        
        # Fallback: use first numeric column
        if not sales_column_mapping and numeric_cols:
            sales_column_mapping['sales'] = numeric_cols[0]
        
        print(f"[Chatbot] Auto-detected sales mapping: {sales_column_mapping}")
    
    return financial_column_mapping or {}, sales_column_mapping or {}


class ChatState(TypedDict, total=False):
    """State for chatbot conversation."""
    user_question: str
    routed_agents: list  # ["financial", "sales", etc]
    responses: dict  # {agent_name: response_text}
    final_answer: str
    agents_used: str  # Human readable
    visualization_data: Optional[dict]  # {agent: plotly_figure}


def should_visualize(question: str) -> bool:
    """Detect if user is asking for visualization."""
    viz_keywords = ["visualize", "show", "chart", "graph", "plot", "display", "visual", "see", "picture", "create visualization", "visualization", "trend"]
    return any(keyword in question.lower() for keyword in viz_keywords)


def clean_question_for_agent(question: str) -> str:
    """
    Remove visualization keywords from question so agents focus on analysis only.
    
    Example:
        Input: "what are sales trends? also visualize it"
        Output: "what are sales trends?"
    """
    # Remove only generic visualization tails while preserving business keywords
    # (e.g. keep "cogs trend" in "tell and show the cogs trend").
    viz_phrases = [
        r"\s*,?\s*also\s+(visualize|create)\s+(it|this|that)\b.*$",
        r"\s*,?\s*also\s+show\s+(it|this|that)\b.*$",
        r"\s*\.\s*(visualize|create|show|plot|chart|graph)\s+(it|this|that)\b.*$",
        r"\s*(visualize|create|show|plot|chart|graph)\s+(it|this|that)\b.*$",
    ]
    
    import re
    cleaned = str(question)
    for phrase in viz_phrases:
        cleaned = re.sub(phrase, "", cleaned, flags=re.IGNORECASE)

    # If cleanup removed too much, keep the original question to preserve intent.
    if len(cleaned.strip()) < 4:
        cleaned = str(question)
    
    # Clean up extra spaces and punctuation
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    cleaned = re.sub(r'[,;]\s*$', '', cleaned)
    
    if cleaned != question:
        print(f"[Chatbot] Cleaned question for agent:")
        print(f"  Original: {question}")
        print(f"  Cleaned:  {cleaned}")
    
    return cleaned


def get_agent_context(agent: str) -> str:
    """Get readable description for agent."""
    contexts = {
        "financial": "Financial Analysis",
        "sales": "Sales Analysis",
        "investment": "Investment Strategy",
        "cloud": "Cloud Architecture",
    }
    return contexts.get(agent, agent.title())



def process_chat_question(
    question: str,
    financial_csv: Optional[pd.DataFrame] = None,
    sales_csv: Optional[pd.DataFrame] = None,
    financial_column_mapping: Optional[dict] = None,
    sales_column_mapping: Optional[dict] = None,
    previous_agents: Optional[list] = None,
    uploaded_collections: Optional[dict] = None,
) -> dict:
    """
    Process a user question and get response from appropriate agents.
    
    Args:
        question: User's natural language question
        financial_csv: Optional financial data
        sales_csv: Optional sales data
        financial_column_mapping: Column mappings for financial data
        sales_column_mapping: Column mappings for sales data
        previous_agents: Agents from previous response (for context in follow-ups like "create a chart for this")
        
    Returns:
        {
            "question": user's question,
            "agents": ["financial", "sales"],
            "responses": {
                "financial": "response from financial agent",
                "sales": "response from sales agent"
            },
            "final_answer": "combined/synthesized answer",
            "agents_summary": "Financial Analysis + Sales Analysis"
        }
    """
    
    print(f"\n[Chatbot] Processing question: {question}")

    uploaded_pdf_agents = get_uploaded_pdf_agents(uploaded_collections)
    if uploaded_pdf_agents:
        print(f"[Chatbot] Uploaded PDF agents available for fallback: {uploaded_pdf_agents}")
    
    # Step 0: Auto-detect column mappings if not provided
    financial_column_mapping, sales_column_mapping = auto_detect_column_mappings(
        financial_csv, sales_csv, financial_column_mapping, sales_column_mapping
    )
    
    # Step 1: Route the question via the central orchestrator routing (RAG + keywords)
    try:
        orch_state = {
            "query": question,
            "financial_csv": financial_csv,
            "sales_csv": sales_csv,
            "financial_column_mapping": financial_column_mapping,
            "sales_column_mapping": sales_column_mapping,
            "uploaded_pdf_agents": uploaded_pdf_agents,
        }
        orch_result = orchestrator_node_impl(orch_state)
        routed_agents = orch_result.get("routes", [])
        print(f"[Chatbot] Routed by orchestrator_agent to: {routed_agents}")
    except Exception as e:
        print(f"[Chatbot] Orchestrator routing failed: {e}, falling back to local routing")
        routed_agents = route_query(question, default_agents=uploaded_pdf_agents)

    # PDF-aware fallback for unexpected empty routing output.
    if not routed_agents and uploaded_pdf_agents:
        print(f"[Chatbot] Empty routing result - using uploaded PDF agents: {uploaded_pdf_agents}")
        routed_agents = uploaded_pdf_agents.copy()
    
    # Step 1.5: Filter agents based on available data
    # Financial agent supports both CSV and RAG/PDF mode, so do NOT drop it when CSV is missing.
    # Sales agent is CSV-centric and should still be dropped when sales CSV is unavailable.
    # Keep non-CSV agents (investment, cloud).
    filtered_agents = []
    for a in routed_agents:
        if a == "financial":
            filtered_agents.append(a)
            if financial_csv is None or financial_csv.empty:
                print("[Chatbot] Keeping 'financial' route without CSV (RAG/PDF mode)")
        elif a == "sales":
            if sales_csv is not None and not sales_csv.empty:
                filtered_agents.append(a)
            else:
                print(f"[Chatbot] Dropping 'sales' route - no sales CSV provided")
        else:
            # investment/cloud do not require CSVs - keep them
            filtered_agents.append(a)

    routed_agents = filtered_agents

    # If filtering removed everything, prefer uploaded PDF agents still available.
    if not routed_agents and uploaded_pdf_agents:
        print("[Chatbot] All routed agents were filtered out - retrying with uploaded PDF agents")
        for agent in uploaded_pdf_agents:
            if agent == "sales":
                if sales_csv is not None and not sales_csv.empty:
                    routed_agents.append(agent)
                else:
                    print("[Chatbot] Skipping uploaded 'sales' PDF fallback - no sales CSV provided")
            else:
                routed_agents.append(agent)

    print(f"[Chatbot] After filtering by available data: {routed_agents}")
    
    # Step 1.6: Handle context-dependent requests (e.g., "create a chart for this")
    # If query is just about visualization/details without specific agent keywords,
    # and we have previous agents, use those for context
    viz_only_keywords = ["chart", "visualize", "graph", "plot", "create for this", "for this"]
    agent_keywords = ["sales", "financial", "investment", "cloud", "budget", "revenue", "profit", "region", "product"]
    
    is_viz_only_request = any(kw in question.lower() for kw in viz_only_keywords)
    has_agent_keywords = any(kw in question.lower() for kw in agent_keywords)
    
    if is_viz_only_request and not has_agent_keywords and previous_agents:
        print(f"[Chatbot] Context-dependent request detected. Using previous agents: {previous_agents}")
        routed_agents = previous_agents
    
    # Step 1.7: Clean visualization keywords from question for agents
    # Agents should focus on analysis, not visualization
    agent_question = clean_question_for_agent(question)
    will_visualize = should_visualize(question)  # Check BEFORE cleaning
    
    # Step 2: Call each agent with the specific question
    responses = {}
    
    agent_runners = {
        "financial": lambda: financial_run(
            query=agent_question,
            df=financial_csv,
            column_mapping=financial_column_mapping
        ),
        "sales": lambda: sales_run(
            query=agent_question,
            df=sales_csv,
            column_mapping=sales_column_mapping
        ),
        "investment": lambda: investment_run(agent_question),
        "cloud": lambda: cloud_run(agent_question),
    }
    
    # Store full agent results for later extraction of visualization
    agent_results = {}
    responses = {}
    
    for agent in routed_agents:
        try:
            print(f"[Chatbot] Calling {agent} agent...")
            result = agent_runners[agent]()
            agent_results[agent] = result  # Store full result for visualization extraction
            responses[agent] = result.get("response", "No response from agent")
            print(f"[Chatbot] ✓ Got response from {agent} agent")
            if result.get("visualization"):
                print(f"[Chatbot]   → Visualization included")
        except Exception as e:
            print(f"[Chatbot] ✗ Error calling {agent} agent: {str(e)}")
            responses[agent] = f"Error: {str(e)}"
            agent_results[agent] = {}
    
    # Safety check: if no responses, provide helpful message
    if not responses:
        final_answer = "No data available for analysis. Please upload CSV files for the data you want to analyze (financial, sales, etc.)"
        agents_summary = "NO DATA"
    
    # Step 3: Synthesize final answer (optional - combine if multiple agents)
    elif len(responses) == 1:
        final_answer = list(responses.values())[0]
        agents_summary = " + ".join([get_agent_context(a) for a in list(responses.keys())])
    else:
        # Multiple agents - synthesize
        combined_responses = "\n\n".join([
            f"=== {agent.upper()} ===\n{response}"
            for agent, response in responses.items()
        ])
        
        synthesis_prompt = f"""You are a financial analysis synthesizer.
A user asked: "{question}"

You received responses from multiple expert agents:
{combined_responses}

Synthesize these into ONE coherent, conversational answer that directly addresses the user's question.
Keep it concise and focused on what the user asked about.
Remove redundancy, combine insights, and present a unified response."""
        
        final_answer = call_gemini(synthesis_prompt)
        agents_summary = " + ".join([get_agent_context(a) for a in list(responses.keys())])
        print(f"[Chatbot] Synthesized final answer")
    
    # Step 4: Collect visualizations from agent responses if available
    # Agents now handle their own visualization generation
    visualization_data = {}
    for agent in agent_results:
        if agent_results[agent].get("visualization"):
            visualization_data[agent] = agent_results[agent]["visualization"]
            print(f"[Chatbot] ✓ Collected visualization from {agent} agent")
    
    # Step 5: Prepare response
    return {
        "question": question,
        "agents": routed_agents,
        "responses": responses,
        "final_answer": final_answer,
        "agents_summary": agents_summary,
        "visualization_data": visualization_data if visualization_data else None,
    }


if __name__ == "__main__":
    # Test
    result = process_chat_question("What are our sales trends?")
    print("\n" + "="*60)
    print(result["final_answer"])
