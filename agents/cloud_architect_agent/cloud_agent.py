
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rag.pipeline import build_collection, rag_query, format_context
from rag.prompt_templates import AGENT_SYSTEM_PROMPTS, build_user_message
from rag.hf_llm import call_llm


COLLECTION_NAME = "cloud_docs"   # This agent's dedicated ChromaDB collection
TOP_K           = 5              # Number of chunks to retrieve per query


def build_cloud_index() -> None:
    """
    One-time setup: load PDFs from docs/cloud_docs/ and index them.
    """
    print(f"[cloud_agent] Building index for collection '{COLLECTION_NAME}'…")
    build_collection(COLLECTION_NAME)
    print(f"[cloud_agent] Index ready.\n")


def run_cloud_architect_agent(query: str, top_k: int = TOP_K) -> str:
    """
    Main entry point for the Cloud Architect Agent.

    Args:
        query  : The user's question or the Orchestrator's sub-task description.
                 e.g. "Recommend a cloud setup to handle 10 million daily users."
        top_k  : Number of document chunks to retrieve (default 5).

    Returns:
        A structured string following the cloud_architect prompt template:
        ## Infrastructure Summary
        ## Architecture Recommendations
        ## Cost Optimisation
        ## Scalability Roadmap
        ## Source References
    """
    print(f"\n[cloud_agent] Received query: {query!r}")

    chunks = rag_query(COLLECTION_NAME, query, top_k=top_k)
    print(f"[cloud_agent] Retrieved {len(chunks)} chunks.")

    context = format_context(chunks)

    system_prompt = AGENT_SYSTEM_PROMPTS["cloud_architect"]
    user_message  = build_user_message(context, query)

    print(f"[cloud_agent] Calling LLM…")
    response = call_llm(system_prompt, user_message)
    print(f"[cloud_agent] Response received ({len(response)} chars).\n")

    return response


def run_cloud_architect_agent_no_rag(query: str) -> str:
    """
    Fallback: run the Cloud Architect Agent WITHOUT retrieved context.

    Used when:
      • The cloud_docs collection is empty (no PDFs loaded yet).
      • You want to compare RAG vs. baseline LLM output.

    The LLM answers from general pre-trained knowledge only.

    Args:
        query : The infrastructure question.

    Returns:
        A structured string (same format as run_cloud_architect_agent).
    """
    print(f"\n[cloud_agent] Running WITHOUT RAG context (baseline mode).")
    system_prompt = AGENT_SYSTEM_PROMPTS["cloud_architect"]
    user_message  = (
        f"Answer the following cloud infrastructure query using your general knowledge.\n\n"
        f"Query: {query}\n\n"
        f"Provide a thorough, structured response covering:\n"
        f"Infrastructure Summary, Architecture Recommendations, "
        f"Cost Optimisation, and a Scalability Roadmap."
    )
    response = call_llm(system_prompt, user_message)
    return response


if __name__ == "__main__":
    test_query = (
        "Design a cloud infrastructure for a multi-agent AI financial system "
        "that processes 1 million documents daily and serves 50,000 concurrent users."
    )

    print("=" * 70)
    print("CLOUD ARCHITECT AGENT — SELF TEST")
    print("=" * 70)

    # Try RAG first; fall back to no-RAG if collection is empty
    chunks = rag_query(COLLECTION_NAME, test_query, top_k=1)
    if chunks:
        result = run_cloud_architect_agent(test_query)
    else:
        print("[cloud_agent] No cloud_docs indexed — using baseline (no RAG).")
        result = run_cloud_architect_agent_no_rag(test_query)

    print("\n" + "=" * 70)
    print("AGENT OUTPUT:")
    print("=" * 70)
    print(result)
