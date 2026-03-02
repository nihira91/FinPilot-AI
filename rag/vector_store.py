# ─────────────────────────────────────────────────────────────────────────────
# vector_store.py
#
# PURPOSE : Wrap ChromaDB so any agent can store and query chunks with
#           one simple function call.
#
# WHY ChromaDB INSTEAD OF FAISS ?
#   • ChromaDB has BUILT-IN named collections — perfect for our 5-collection design.
#   • It persists data to disk automatically (no manual save/load needed).
#   • It stores text AND metadata alongside vectors in one place.
#   • FAISS stores only raw vectors; you must manage text/metadata yourself.
#
# HOW COLLECTIONS MAP TO AGENTS :
#   collection "financial_reports"  → used by Financial Analyst Agent
#   collection "sales_reports"      → used by Sales & Data Scientist Agent
#   collection "investment_reports" → used by Investment Strategist Agent  (YOU)
#   collection "cloud_docs"         → used by Cloud Architect Agent
#   collection "routing_rules"      → used by Orchestrator Agent
#
# PERSISTENCE :
#   ChromaDB saves everything to  ./chroma_store/  on disk.
#   Re-running the program reloads the existing data — no re-embedding needed.
# ─────────────────────────────────────────────────────────────────────────────

import chromadb
from chromadb.config import Settings

from rag.embedder import embed_texts, embed_query


# ── ChromaDB persistent client ─────────────────────────────────────────────────
# path="./chroma_store" tells ChromaDB where to save its files on disk.
# anonymized_telemetry=False turns off usage tracking (privacy-friendly).
_chroma_client = chromadb.PersistentClient(
    path="./chroma_store",
    settings=Settings(anonymized_telemetry=False)
)


def get_or_create_collection(collection_name: str):
    """
    Return a ChromaDB collection, creating it if it does not already exist.

    ChromaDB uses cosine similarity by default for vector search,
    which is the standard measure for semantic document retrieval.

    Args:
        collection_name : e.g. "investment_reports"

    Returns:
        A chromadb.Collection object ready for add() and query() calls.
    """
    collection = _chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}   # cosine similarity for semantic search
    )
    print(f"[vector_store] Collection '{collection_name}' ready "
          f"({collection.count()} existing vectors).")
    return collection


def add_chunks_to_collection(collection_name: str, chunks: list) -> None:
    """
    Embed all chunks and add them to the named ChromaDB collection.

    Skips chunks whose chunk_id already exists (safe to call multiple times).

    Args:
        collection_name : which ChromaDB collection to write to
        chunks          : list of {"text":..., "source":..., "chunk_id":...}
                          from chunker.chunk_documents()
    """
    if not chunks:
        print(f"[vector_store] No chunks to add to '{collection_name}'.")
        return

    collection = get_or_create_collection(collection_name)

    # ── Find which chunk_ids are already stored so we don't duplicate ──────────
    existing_ids = set()
    if collection.count() > 0:
        existing = collection.get()              # get all stored items
        existing_ids = set(existing["ids"])      # extract their IDs into a set

    # Filter out chunks that are already in the collection
    new_chunks = [c for c in chunks if c["chunk_id"] not in existing_ids]

    if not new_chunks:
        print(f"[vector_store] All chunks already exist in '{collection_name}' — skipping.")
        return

    print(f"[vector_store] Embedding {len(new_chunks)} new chunks for '{collection_name}'…")

    # ── Prepare the three parallel lists ChromaDB's add() expects ─────────────
    texts      = [c["text"]     for c in new_chunks]   # the actual text content
    ids        = [c["chunk_id"] for c in new_chunks]   # unique string IDs
    metadatas  = [{"source": c["source"]} for c in new_chunks]  # source filename

    embeddings = embed_texts(texts)   # list of 384-float lists

    # ChromaDB add() takes: ids, embeddings, documents (text), metadatas
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,       # ChromaDB stores the raw text here
        metadatas=metadatas    # we store {"source": "filename.pdf"} here
    )

    print(f"[vector_store] Added {len(new_chunks)} chunks. "
          f"Collection now has {collection.count()} total vectors.")


def query_collection(collection_name: str, query_text: str, top_k: int = 5) -> list:
    """
    Retrieve the top-K most relevant chunks for a query.

    This is called by every agent when it needs context for its LLM call.

    Args:
        collection_name : which collection to search
        query_text      : the agent's question in plain English
        top_k           : how many chunks to return (5 is a good default)

    Returns:
        List of dicts sorted by relevance (most relevant first):
        [
          {"text": "…", "source": "report.pdf", "distance": 0.13},
          …
        ]
        distance is the cosine distance — LOWER = MORE similar.
    """
    collection = get_or_create_collection(collection_name)

    if collection.count() == 0:
        print(f"[vector_store] WARNING: '{collection_name}' is empty — add documents first.")
        return []

    query_vector = embed_query(query_text)   # embed the query into a vector

    # query() returns a dict with lists: ids, documents, metadatas, distances
    results = collection.query(
        query_embeddings=[query_vector],    # must be a list of vectors (we send one)
        n_results=min(top_k, collection.count()),  # can't ask for more than we have
        include=["documents", "metadatas", "distances"]
    )

    # ── Unpack ChromaDB's response format ─────────────────────────────────────
    # results["documents"][0]  → list of text strings for query 0
    # results["metadatas"][0]  → list of metadata dicts for query 0
    # results["distances"][0]  → list of cosine distances for query 0
    docs       = results["documents"][0]
    metadatas  = results["metadatas"][0]
    distances  = results["distances"][0]

    # Combine into a clean list of dicts for the calling agent
    retrieved = []
    for doc, meta, dist in zip(docs, metadatas, distances):
        retrieved.append({
            "text":     doc,
            "source":   meta.get("source", "unknown"),
            "distance": round(dist, 4)   # lower = more relevant
        })

    return retrieved   # already sorted best-first by ChromaDB