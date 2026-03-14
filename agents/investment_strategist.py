#Investment Strategist Agent

from rag.pipeline          import rag_query, format_context
from rag.prompt_templates  import AGENT_SYSTEM_PROMPTS, build_user_message
from rag.hf_llm            import call_llm

SYSTEM_PROMPT = AGENT_SYSTEM_PROMPTS["investment_strategist"]


def run(query: str, top_k: int = 5) -> dict:
    """
    Main entry point for the Investment Strategist Agent.

    Args:
        query  : the task/question from the Orchestrator
                 e.g. "Summarise expansion opportunities from consultant reports"
        top_k  : how many document chunks to retrieve as context (default 5)

    Returns:
        {
          "agent"        : "Investment Strategist",
          "query"        : original query string,
          "response"     : LLM's full structured analysis (markdown),
          "sources"      : list of unique source filenames used,
          "chunks_used"  : number of chunks retrieved from RAG
        }
    """
    print(f"\n[Investment Strategist] Query received: {query}")

    #pass "investment_reports" this agent reads from this collection.
    chunks = rag_query("investment_reports", query, top_k=top_k)

    if not chunks:
        #return a failure message 
        print("[Investment Strategist] No relevant documents found.")
        return {
            "agent":       "Investment Strategist",
            "query":       query,
            "response":    "No relevant investment documents found in the knowledge base. "
                           "Please add consultant reports or investment PDFs to "
                           "docs/investment_reports/ and run build_collection().",
            "sources":     [],
            "chunks_used": 0
        }

    # format_context() turns the list of dicts 
    context = format_context(chunks)

    # Collect unique source filenames for the metadata we return
    sources = list({chunk["source"] for chunk in chunks})

    # build_user_message() 
    user_message = build_user_message(context, query)

    print(f"[Investment Strategist] Calling LLM with {len(chunks)} context chunks …")
    llm_response = call_llm(SYSTEM_PROMPT, user_message)

    print(f"[Investment Strategist] Analysis complete. Sources used: {sources}")

    return {
        "agent":       "Investment Strategist",
        "query":       query,
        "response":    llm_response,
        "sources":     sources,
        "chunks_used": len(chunks)
    }
