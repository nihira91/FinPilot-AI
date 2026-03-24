

from rag.pipeline          import rag_query, format_context
from rag.vector_store      import query_with_domain_filter
from rag.prompt_templates  import AGENT_SYSTEM_PROMPTS, build_user_message
from rag.hf_llm            import call_llm


# Pull this agent's system prompt from the shared templates file

SYSTEM_PROMPT = AGENT_SYSTEM_PROMPTS["investment_strategist"]


def run(query: str, top_k: int = 10) -> dict:
    """
    Main entry point for the Investment Strategist Agent.

    Called by the Orchestrator whenever investment analysis is needed.

    Args:
        query  : the task/question from the Orchestrator
                 e.g. "Summarise expansion opportunities from consultant reports"
        top_k  : how many document chunks to retrieve as context (default 10 for better context)

    Returns:
        {
          "agent"        : "Investment Strategist",
          "query"        : original query string,
          "response"     : LLM's full structured analysis (markdown),
          "sources"      : list of unique source filenames used,
          "chunks_used"  : number of chunks retrieved from RAG
        }

    The Orchestrator receives this dict and merges it with all other agents'
    outputs into one final consolidated report.
    """
    print(f"\n[Investment Strategist] Query received: {query}")

    # Retrieve relevant chunks from the RAG pipeline with domain filtering
    filtered_chunks, domain_relevance = query_with_domain_filter(
        "investment_reports", query, domain="investment", top_k=top_k
    )

    if not filtered_chunks:
        print("[Investment Strategist] No relevant documents found.")
        return {
            "agent":       "Investment Strategist",
            "agent_domain": "Investment Strategy & Portfolio Analysis",
            "query":       query,
            "response":    "No relevant investment documents found in the knowledge base. "
                           "Please add consultant reports or investment PDFs to "
                           "docs/investment_reports/ and run build_collection().",
            "sources":     [],
            "chunks_used": 0,
            "data_source": "No Documents Available",
            "confidence": "LOW",
        }

    # Format chunks into readable context text 
 
    context = format_context(filtered_chunks)

    # Collect unique source filenames for the metadata we return
    sources = list({chunk["source"] for chunk in filtered_chunks})

    #  Build the user message
    # build_user_message() injects context BEFORE the question — standard RAG pattern.
    # The LLM reads "here is relevant information, now answer the question."
    user_message = build_user_message(context, query)

    #  Call the LLM 
    print(f"[Investment Strategist] Calling LLM with {len(filtered_chunks)} context chunks (domain relevance: {domain_relevance:.0%})…")
    llm_response = call_llm(SYSTEM_PROMPT, user_message)

    print(f"[Investment Strategist] Analysis complete. Sources used: {sources}")

    # Return structured result to Orchestrator 
    return {
        "agent":       "Investment Strategist",
        "agent_domain": "Investment Strategy & Portfolio Analysis",
        "query":       query,
        "response":    llm_response,
        "sources":     sources,
        "chunks_used": len(filtered_chunks),
        "data_source": f"RAG Documents (Domain-Filtered, {domain_relevance:.0%} relevance)",
        "confidence": "HIGH" if domain_relevance > 0.5 else "MEDIUM",
    }