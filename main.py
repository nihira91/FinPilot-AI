# main.py
from orchestrator.orchestrator_agent import build_graph
from dotenv import load_dotenv

load_dotenv()

def run_system(query: str):
    print(f"\n{'='*40}")
    print(f"Query: {query}")
    print(f"{'='*40}")

    graph = build_graph()
    result = graph.invoke({"query": query})

    print(f"\n{'='*40}")
    print("FINAL OUTPUT:")
    print(f"{'='*40}")
    print(result["final_output"])
    return result

if __name__ == "__main__":
    # Test queries
    queries = [
        "Analyse our Q3 financial performance",
        "What are our sales trends this year?",
        "Suggest investment strategy for expansion",
        "Recommend cloud infrastructure for scaling"
    ]

    # Run with first query
    run_system(queries[0])