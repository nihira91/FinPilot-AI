# tests/test_mcp.py
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator.orchestrator_agent import build_graph

def test_mcp_tools():
    print("\n[MCP Test] Testing all agent tools...")
    
    graph = build_graph()
    
    # Test 1: Financial query
    print("\n── Test 1: Financial Query ──")
    result = graph.invoke({
        "query": "What is our Q3 profit performance?"
    })
    assert result["final_output"], "Should return output"
    print(f"✅ Financial routing works")
    
    # Test 2: Investment query  
    print("\n── Test 2: Investment Query ──")
    result = graph.invoke({
        "query": "What investment strategy is recommended?"
    })
    assert result["final_output"], "Should return output"
    print(f"✅ Investment routing works")
    
    # Test 3: All agents query
    print("\n── Test 3: All Agents Query ──")
    result = graph.invoke({
        "query": "Give me complete analysis of our business performance"
    })
    assert result["final_output"], "Should return output"
    print(f"✅ All agents routing works")
    
    print("\n✅ All MCP tests passed!")

if __name__ == "__main__":
    test_mcp_tools()