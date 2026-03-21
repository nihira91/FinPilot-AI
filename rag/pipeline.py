
# Single entry point that ties together



from rag.pdf_loader   import load_all_pdfs
from rag.chunker      import chunk_documents
from rag.vector_store import add_chunks_to_collection, query_collection


COLLECTIONS = {
    "financial_reports":  "docs/financial_reports",   # → Financial Analyst Agent
    "sales_reports":      "docs/sales_reports",       # → Sales & Data Scientist Agent
    "investment_reports": "docs/investment_reports",  # → Investment Strategist Agent 
    "cloud_docs":         "docs/cloud_docs",          # → Cloud Architect Agent
    "routing_rules":      "docs/routing_rules",       # → Orchestrator Agent
}


def build_collection(collection_name: str) -> None:
    """
     load PDFs from disk → chunk → embed → store in ChromaDB.

    """
    if collection_name not in COLLECTIONS:
        raise ValueError(
            f"Unknown collection '{collection_name}'. "
            f"Available: {list(COLLECTIONS.keys())}"
        )

    folder = COLLECTIONS[collection_name]
    print(f"\n[pipeline] Building collection '{collection_name}' from '{folder}/'")

    documents = load_all_pdfs(folder)           #extract text from PDFs

    if not documents:
        print(f"[pipeline] No PDFs found in '{folder}/' — collection will be empty.")
        return

    chunks = chunk_documents(documents)         # split text into chunks
    add_chunks_to_collection(collection_name, chunks)  # embed + store
    print(f"[pipeline] Collection '{collection_name}' is ready.\n")


def build_all_collections() -> None:
    """
    build ALL five collections in one call.
    """
    for name in COLLECTIONS:
        build_collection(name)


def rag_query(collection_name: str, query: str, top_k: int = 5) -> list:
    """
    Retrieves the top_k most relevant text chunks from a collection.

    """
    if collection_name not in COLLECTIONS:
        raise ValueError(f"Unknown collection '{collection_name}'.")

    return query_collection(collection_name, query, top_k=top_k)


def format_context(chunks: list) -> str:
    """
    Format retrieved chunks into a clean block of text to inject into an LLM prompt.

    """
    if not chunks:
        return "No relevant documents found in the knowledge base."

    parts = []
    for chunk in chunks:
        source   = chunk.get("source",   "unknown")
        distance = chunk.get("distance",  0.0)
        text     = chunk.get("text",      "")
        # Lower distance = more relevant; 
        parts.append(f"[Source: {source} | Relevance distance: {distance}]\n{text}")

    return "\n---\n".join(parts)
