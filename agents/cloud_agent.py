import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rag.pipeline import build_collection, rag_query, format_context
from rag.vector_store import query_with_domain_filter
from rag.prompt_templates import AGENT_SYSTEM_PROMPTS, build_user_message
from rag.hf_llm import call_llm

COLLECTION_NAME = "cloud_docs"
TOP_K           = 10


def build_cloud_index() -> None:
    print(f"[cloud_agent] Building index for '{COLLECTION_NAME}'...")
    build_collection(COLLECTION_NAME)
    print(f"[cloud_agent] Index ready.")


def run(query: str) -> dict:
    """
    Main entry point — called by Orchestrator.
    Returns dict with 'response' key and agent metadata.
    """
    print(f"\n[Cloud Agent] Query received: {query}")

    # Use domain-filtered RAG
    filtered_chunks, domain_relevance = query_with_domain_filter(
        COLLECTION_NAME, query, domain="cloud", top_k=TOP_K
    )
    
    if filtered_chunks:
        context = format_context(filtered_chunks)
        data_source = f"RAG Documents (Domain-Filtered, {domain_relevance:.0%} relevance)"
        print(f"[Cloud Agent] Using {len(filtered_chunks)} domain-filtered chunks.")
    else:
        print("[Cloud Agent] No docs found — using baseline mode.")
        context = "No cloud infrastructure documents available."
        data_source = "General Knowledge (No Docs)"

    system_prompt = AGENT_SYSTEM_PROMPTS["cloud_architect"]
    user_message  = build_user_message(context, query)

    print(f"[Cloud Agent] Calling LLM...")
    response = call_llm(system_prompt, user_message)
    print(f"[Cloud Agent] Analysis complete.")

    return {
        "agent": "Cloud Architect",
        "agent_domain": "Cloud Infrastructure & Deployment",
        "query": query,
        "response": response,
        "data_source": data_source,
        "confidence": "HIGH" if filtered_chunks else "MEDIUM",
    }


# Backward compatibility
def run_cloud_architect_agent(query: str) -> str:
    return run(query)["response"]


def run_cloud_architect_agent_no_rag(query: str) -> str:
    system_prompt = AGENT_SYSTEM_PROMPTS["cloud_architect"]
    user_message  = (
        f"Answer using general knowledge.\n\nQuery: {query}\n\n"
        f"Infrastructure Summary, Architecture Recommendations, "
        f"Cost Optimisation, Scalability Roadmap."
    )
    return call_llm(system_prompt, user_message)


if __name__ == "__main__":
    result = run("Design cloud infrastructure for multi-agent AI financial system")
    print(result["response"])