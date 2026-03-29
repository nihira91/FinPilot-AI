
import os
import glob
from rag.pdf_loader   import load_all_pdfs
from rag.chunker      import chunk_documents
from rag.vector_store import add_chunks_to_collection, query_collection
from rag.vector_store import SYSTEM_COLLECTIONS, USER_COLLECTIONS


# System collections — permanent, disk-based (hamesha rahengi)
SYSTEM_COLLECTIONS_MAP = {
    "routing_rules": "docs/routing_rules",
}

# User collections — session-based, RAM-clearable (user session shuru-end)
USER_COLLECTIONS_MAP = {
    "financial_reports":  "docs/financial_reports",
    "sales_reports":      "docs/sales_reports",
    "investment_reports": "docs/investment_reports",
    "cloud_docs":         "docs/cloud_docs",
}

# Temp uploads root for session-based uploads
TEMP_UPLOADS_ROOT = "temp_uploads"

# Combined for backward compatibility
COLLECTIONS = {**SYSTEM_COLLECTIONS_MAP, **USER_COLLECTIONS_MAP}


def get_collection_folder(collection_name: str, session_id: str = None) -> str:
    """
    Determine the correct folder for a collection.
    - System collections: Always use docs/
    - User collections with session_id: Use temp_uploads/{session_id}/{collection}/
    - User collections without session_id: Use docs/ (fallback)
    """
    if collection_name in SYSTEM_COLLECTIONS:
        return COLLECTIONS[collection_name]
    
    # For user collections, check temp folder first
    if session_id:
        temp_folder = os.path.join(TEMP_UPLOADS_ROOT, session_id, collection_name)
        if os.path.exists(temp_folder) and os.listdir(temp_folder):
            print(f"[pipeline] Using session uploads: {temp_folder}")
            return temp_folder
    
    # Fallback to docs folder
    return COLLECTIONS[collection_name]


def build_collection(collection_name: str, session_id: str = None) -> None:
    """
    Build a collection and add it to ChromaDB.
    
    Args:
        collection_name: Name of collection to build
        session_id: Optional session ID for temp user uploads
    
    System collections (routing_rules):
    → Persistent (disk-based PersistentClient)
    → Rebuilt once, reused forever
    → Shared across all user sessions
    
    User collections (financial_reports, sales_reports, etc.):
    → Ephemeral (RAM-based EphemeralClient)
    → Built fresh per user session from temp_uploads/
    → Cleared when user clicks "New Session"
    """
    if collection_name not in COLLECTIONS:
        raise ValueError(
            f"Unknown collection '{collection_name}'. "
            f"Available: {list(COLLECTIONS.keys())}"
        )

    folder = get_collection_folder(collection_name, session_id)
    collection_type = "System" if collection_name in SYSTEM_COLLECTIONS else "User"
    
    print(f"\n[pipeline] Building {collection_type} collection '{collection_name}' from '{folder}/'")

    documents = load_all_pdfs(folder)        

    if not documents:
        print(f"[pipeline] No PDFs found in '{folder}/' — collection will be empty.")
        return

    chunks = chunk_documents(documents)    
    if not chunks:
        print(
            f"[pipeline] No text chunks created for '{collection_name}'. "
            "PDFs may be scanned/image-only or unreadable."
        )
        return

    add_chunks_to_collection(collection_name, chunks)  
    print(f"[pipeline] Collection '{collection_name}' ({collection_type}) is ready.\n")


def build_all_collections() -> None:
    
    for name in COLLECTIONS:
        build_collection(name)


def rag_query(collection_name: str, query: str, top_k: int = 5) -> list:
    """Query a collection. Sanitizes query to prevent None values."""
    
    if collection_name not in COLLECTIONS:
        raise ValueError(f"Unknown collection '{collection_name}'.")
    
    # ── Ensure query is valid string ──
    if query is None:
        raise ValueError(f"Query is None for collection '{collection_name}'")
    query = str(query).strip()
    
    if not query:
        raise ValueError(f"Query is empty for collection '{collection_name}'")

    return query_collection(collection_name, query, top_k=top_k)


def format_context(chunks: list) -> str:
   
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