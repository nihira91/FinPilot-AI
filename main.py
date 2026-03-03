from orchestrator.orchestrator_agent import build_graph
from rag.pipeline import build_collection
from dotenv import load_dotenv

load_dotenv()

def run_system(query: str):
    print(f"\n{'='*50}")
    print(f"QUERY: {query}")
    print(f"{'='*50}")

    graph = build_graph()
    result = graph.invoke({"query": query})

    print(f"\n{'='*50}")
    print("FINAL OUTPUT:")
    print(f"{'='*50}")
    print(result["final_output"])
    return result

if __name__ == "__main__":
    # Build collections first time only
    # Comment these out after first run
    build_collection("routing_rules")
    build_collection("investment_reports")
    build_collection("financial_reports")
    build_collection("sales_reports")
    build_collection("cloud_docs")

    # Test queries
    run_system("Analyse our Q3 financial performance")