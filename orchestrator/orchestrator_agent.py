# orchestrator/orchestrator_agent.py
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from typing import TypedDict, Literal
from dotenv import load_dotenv

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash"
)

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# State that passes between all agents
class AgentState(TypedDict):
    query: str
    route: str
    financial_output: str
    sales_output: str
    investment_output: str
    cloud_output: str
    final_output: str

# Orchestrator decides which agent to call
def orchestrator_node(state: AgentState):
    query = state["query"]

    prompt = f"""
    You are an orchestrator of a financial
    AI system. Based on the query decide
    which agents to call.

    Query: {query}

    Available agents:
    - financial: for financial analysis,
                 profit/loss, budget
    - sales: for sales trends,
             pattern detection
    - investment: for strategy documents,
                  consultant reports
    - cloud: for infrastructure,
             AWS/GCP recommendations
    - all: if query needs all agents

    Respond with only one word:
    financial, sales, investment, cloud,
    or all
    """

    response = llm.invoke(prompt)
    route = response.content.strip().lower()
    print(f"\nRouting query to: {route}")
    return {"route": route}

# Router function
def route_query(state: AgentState) -> Literal[
    "financial", "sales",
    "investment", "cloud", "all_agents"
]:
    route = state["route"]
    if route == "all":
        return "all_agents"
    return route

# Placeholder nodes
# Replace with real agents later
def financial_node(state: AgentState):
    print("Financial Agent running...")
    return {
        "financial_output":
        "Financial analysis placeholder"
    }

def sales_node(state: AgentState):
    print("Sales Agent running...")
    return {
        "sales_output":
        "Sales analysis placeholder"
    }

def investment_node(state: AgentState):
    print("Investment Agent running...")
    return {
        "investment_output":
        "Investment analysis placeholder"
    }

def cloud_node(state: AgentState):
    print("Cloud Agent running...")
    return {
        "cloud_output":
        "Cloud analysis placeholder"
    }

def all_agents_node(state: AgentState):
    print("All Agents running...")
    return {
        "financial_output": "Financial placeholder",
        "sales_output": "Sales placeholder",
        "investment_output": "Investment placeholder",
        "cloud_output": "Cloud placeholder"
    }

# Aggregate all results into final output
def aggregator_node(state: AgentState):
    print("Aggregating results...")
    final = f"""
=== FINANCIAL ANALYSIS ===
{state.get('financial_output', 'N/A')}

=== SALES ANALYSIS ===
{state.get('sales_output', 'N/A')}

=== INVESTMENT STRATEGY ===
{state.get('investment_output', 'N/A')}

=== CLOUD RECOMMENDATION ===
{state.get('cloud_output', 'N/A')}
    """
    return {"final_output": final}

# Build the complete graph
def build_graph():
    graph = StateGraph(AgentState)

    # Add all nodes
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("financial", financial_node)
    graph.add_node("sales", sales_node)
    graph.add_node("investment", investment_node)
    graph.add_node("cloud", cloud_node)
    graph.add_node("all_agents", all_agents_node)
    graph.add_node("aggregator", aggregator_node)

    # Entry point
    graph.set_entry_point("orchestrator")

    # Conditional routing from orchestrator
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

    # All agents connect to aggregator
    graph.add_edge("financial", "aggregator")
    graph.add_edge("sales", "aggregator")
    graph.add_edge("investment", "aggregator")
    graph.add_edge("cloud", "aggregator")
    graph.add_edge("all_agents", "aggregator")
    graph.add_edge("aggregator", END)

    return graph.compile()