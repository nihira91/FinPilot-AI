# ─────────────────────────────────────────────────────────────────────────────
# pipeline.py  —  THE SHARED RAG PIPELINE
#
# PURPOSE : Single entry point that ties together
#             pdf_loader → chunker → embedder → vector_store
#           into two simple functions any agent can call.
#
# HOW TEAMMATES USE THIS FILE:
#   from rag.pipeline import build_collection, rag_query, format_context
#
#   # (One-time setup) build the index for your collection:
#   build_collection("financial_reports")
#
#   # (Every query) get relevant chunks:
#   chunks = rag_query("financial_reports", "What is the Q3 profit forecast?")
#   context_text = format_context(chunks)
#   # → inject context_text into your LLM prompt
#
# COLLECTION → FOLDER MAPPING:
#   Each collection name maps to a docs/ subfolder.
#   Add PDFs to the correct folder, then call build_collection() once.
# ─────────────────────────────────────────────────────────────────────────────

from rag.pdf_loader   import load_all_pdfs
from rag.chunker      import chunk_documents
from rag.vector_store import add_chunks_to_collection, query_collection


# ── Collection Registry ────────────────────────────────────────────────────────
# Maps each collection name to the folder where its PDFs live.
# All five collections required by the project spec are listed here.
COLLECTIONS = {
    "financial_reports":  "docs/financial_reports",   # → Financial Analyst Agent
    "sales_reports":      "docs/sales_reports",       # → Sales & Data Scientist Agent
    "investment_reports": "docs/investment_reports",  # → Investment Strategist Agent (YOU)
    "cloud_docs":         "docs/cloud_docs",          # → Cloud Architect Agent
    "routing_rules":      "docs/routing_rules",       # → Orchestrator Agent
}


def build_collection(collection_name: str) -> None:
    """
    One-time setup : load PDFs from disk → chunk → embed → store in ChromaDB.

    Call this ONCE per collection (or whenever you add new PDFs).
    ChromaDB persists data to ./chroma_store/ so you do NOT need to re-run
    this every time you start the program — only when PDFs change.

    Args:
        collection_name : must be a key in COLLECTIONS above
    """
    if collection_name not in COLLECTIONS:
        raise ValueError(
            f"Unknown collection '{collection_name}'. "
            f"Available: {list(COLLECTIONS.keys())}"
        )

    folder = COLLECTIONS[collection_name]
    print(f"\n[pipeline] Building collection '{collection_name}' from '{folder}/'")

    documents = load_all_pdfs(folder)           # Step 1 : extract text from PDFs

    if not documents:
        print(f"[pipeline] No PDFs found in '{folder}/' — collection will be empty.")
        return

    chunks = chunk_documents(documents)         # Step 2 : split text into chunks
    add_chunks_to_collection(collection_name, chunks)  # Step 3 : embed + store
    print(f"[pipeline] Collection '{collection_name}' is ready.\n")


def build_all_collections() -> None:
    """
    Convenience function — build ALL five collections in one call.
    Useful for initial project setup.
    """
    for name in COLLECTIONS:
        build_collection(name)


def rag_query(collection_name: str, query: str, top_k: int = 5) -> list:
    """
    THE MAIN FUNCTION — called by every agent at query time.

    Retrieves the top_k most relevant text chunks from a collection.

    Args:
        collection_name : which collection to search  (see COLLECTIONS above)
        query           : the question in plain English
        top_k           : number of chunks to return

    Returns:
        List of dicts: [{"text": "…", "source": "file.pdf", "distance": 0.13}, …]
        Sorted best-first (lowest distance = most relevant).

    Example — Investment Strategist uses this:
        chunks = rag_query("investment_reports", "What is the growth strategy?")
    """
    if collection_name not in COLLECTIONS:
        raise ValueError(f"Unknown collection '{collection_name}'.")

    return query_collection(collection_name, query, top_k=top_k)


def format_context(chunks: list) -> str:
    """
    Format retrieved chunks into a clean block of text to inject into an LLM prompt.

    WHY FORMAT IT ?
        The LLM needs context as readable text, not a Python list.
        We include source citations so the LLM can reference them in its answer.

    Args:
        chunks : output from rag_query()

    Returns:
        A formatted string like:
        [Source: report.pdf | Relevance distance: 0.13]
        chunk text here...
        ---
        [Source: analysis.pdf | Relevance distance: 0.21]
        another chunk here...
    """
    if not chunks:
        return "No relevant documents found in the knowledge base."

    parts = []
    for chunk in chunks:
        source   = chunk.get("source",   "unknown")
        distance = chunk.get("distance",  0.0)
        text     = chunk.get("text",      "")
        # Lower distance = more relevant; we show it so the LLM can gauge confidence
        parts.append(f"[Source: {source} | Relevance distance: {distance}]\n{text}")

    return "\n---\n".join(parts)