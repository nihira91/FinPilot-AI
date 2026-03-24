# test_langgraph.py
from langgraph.graph import StateGraph, END
from typing import TypedDict

# Define state
class AgentState(TypedDict):
    query: str
    result: str

# Define simple node
def orchestrator_node(state: AgentState):
    print(f"Received query: {state['query']}")
    return {"result": "Query received!"}

# Build graph
graph = StateGraph(AgentState)
graph.add_node("orchestrator", orchestrator_node)
graph.set_entry_point("orchestrator")
graph.add_edge("orchestrator", END)

# Compile and run
app = graph.compile()
result = app.invoke({
    "query": "Analyse our performance"
})
print(result)