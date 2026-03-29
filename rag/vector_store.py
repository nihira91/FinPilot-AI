# ─────────────────────────────────────────────────────────────────────────────
# rag/vector_store.py — Vector Store Management with Session Support
# ─────────────────────────────────────────────────────────────────────────────

import os
import numpy as np
from chromadb.config import Settings

from rag.embedder import embed_texts, embed_query
from rag.session_store import get_collection

# ── Collection Classification ──
SYSTEM_COLLECTIONS = ["routing_rules"]  # Persistent, disk-based
USER_COLLECTIONS = [
    "financial_reports", "sales_reports", 
    "investment_reports", "cloud_docs"
]  # Session-based, RAM clearable

# ── Domain Keywords for Specialized Filtering ──
DOMAIN_KEYWORDS = {
    "financial": ["revenue", "profit", "expense", "cogs", "margin", "income", "financial", "accounting", "budget", "cash flow", "assets", "liabilities", "balance sheet", "quarterly", "annual", "forecast", "performance", "metrics"],
    "sales": ["sales", "customer", "transaction", "order", "deal", "pipeline", "volume", "growth", "trend", "region", "product", "market", "channel", "segment", "conversion", "revenue"],
    "investment": ["invest", "portfolio", "return", "stock", "fund", "opportunity", "expansion", "market", "strategy", "acquisition", "growth", "valuation", "roi", "performance", "financial", "opportunity", "strategic", "expansion", "capital"],
    "cloud": ["cloud", "infrastructure", "deployment", "server", "aws", "azure", "gcp", "kubernetes", "database", "architecture", "scaling", "compute", "storage", "network"]
}


def get_or_create_collection(collection_name: str):
    """
    Get or create collection from appropriate client.
    - System collections: Persistent (disk)
    - User collections: Ephemeral (RAM, session-cleared)
    """
    collection_type = "system" if collection_name in SYSTEM_COLLECTIONS else "user"
    
    collection = get_collection(name=collection_name, collection_type=collection_type)
    
    print(f"[vector_store] Collection '{collection_name}' ready "
          f"({collection.count()} existing vectors) [Type: {collection_type}].")
    return collection


def add_chunks_to_collection(collection_name: str, chunks: list) -> None:
    """
    Add chunks to collection, avoiding duplicates.
    """
    if not chunks:
        print(f"[vector_store] No chunks to add to '{collection_name}'.")
        return

    collection = get_or_create_collection(collection_name)

    # Find which chunk_ids are already stored to avoid duplicates
    existing_ids = set()
    if collection.count() > 0:
        existing = collection.get()
        existing_ids = set(existing["ids"])

    # Filter out chunks that are already in the collection
    new_chunks = [c for c in chunks if c["chunk_id"] not in existing_ids]

    if not new_chunks:
        print(f"[vector_store] All chunks already exist in '{collection_name}' — skipping.")
        return

    print(f"[vector_store] Embedding {len(new_chunks)} new chunks for '{collection_name}'…")

    # Prepare the three parallel lists ChromaDB's add() expects
    texts      = [c["text"]     for c in new_chunks]
    ids        = [c["chunk_id"] for c in new_chunks]
    metadatas  = [{"source": c["source"]} for c in new_chunks]

    embeddings = embed_texts(texts)

    # ChromaDB add() takes: ids, embeddings, documents (text), metadatas
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )

    print(f"[vector_store] Added {len(new_chunks)} chunks. "
          f"Collection now has {collection.count()} total vectors.")


def query_collection(collection_name: str, query_text: str, top_k: int = 5) -> list:
    """
    Query collection for relevant chunks.
    """
    collection = get_or_create_collection(collection_name)

    if collection.count() == 0:
        print(f"[vector_store] WARNING: '{collection_name}' is empty — add documents first.")
        return []

    query_vector = embed_query(query_text)

    # query() returns a dict with lists: ids, documents, metadatas, distances
    results = collection.query(
        query_embeddings=[query_vector],   
        n_results=min(top_k, collection.count()),  
        include=["documents", "metadatas", "distances"]
    )

    docs       = results["documents"][0]
    metadatas  = results["metadatas"][0]
    distances  = results["distances"][0]

    # Combine into a clean list of dicts for the calling agent
    retrieved = []
    for doc, meta, dist in zip(docs, metadatas, distances):
        retrieved.append({
            "text":     doc,
            "source":   meta.get("source", "unknown"),
            "distance": round(dist, 4)
        })

    return retrieved


def query_with_domain_filter(collection_name: str, query_text: str, domain: str, top_k: int = 10) -> tuple:
    """
    Query collection with domain-aware reranking.
    - Fetches top_k*4 semantically similar chunks (more context)
    - Reranks by domain keyword relevance
    - Returns top_k results with domain relevance score
    
    Args:
        collection_name: Which collection to query
        query_text: User query
        domain: Domain for keyword filtering (investment, financial, sales, cloud)
        top_k: Number of chunks to return (default 10 for better context)
    
    Returns (filtered_chunks, avg_domain_relevance)
    """
    # Fetch MORE chunks for better semantic context and reranking
    # Increased: top_k*4 with max 40 (better context coverage)
    fetch_count = min(top_k * 4, 40)
    all_chunks = query_collection(collection_name, query_text, top_k=fetch_count)
    
    if not all_chunks:
        return [], 0.0
    
    domain_lower = domain.lower()
    keywords = DOMAIN_KEYWORDS.get(domain_lower, [])
    
    if not keywords:
        print(f"[vector_store] WARNING: Unknown domain '{domain}', returning top semantic results")
        return all_chunks[:top_k], 1.0
    
    # Score chunks by domain keyword presence (soft scoring, not hard filter)
    scored_chunks = []
    for chunk in all_chunks:
        text_lower = chunk["text"].lower()
        
        # Count keyword matches
        keyword_matches = sum(1 for kw in keywords if kw in text_lower)
        
        # Calculate domain relevance (0.0 to 1.0)
        # Even if no keywords match, don't penalize - semantic similarity already matters
        domain_relevance = keyword_matches / max(len(keywords), 1) if keyword_matches > 0 else 0.1
        
        # Combine semantic distance (lower is better) with domain relevance
        # Semantic distance is already normalized (0.0 best, ~1.0 worst)
        semantic_score = max(0, 1.0 - chunk["distance"])  # Convert distance to similarity
        
        # Reranking score: 70% semantic, 30% domain keywords
        combined_score = (0.7 * semantic_score) + (0.3 * domain_relevance)
        
        scored_chunks.append({
            "chunk": chunk,
            "domain_relevance": domain_relevance,
            "semantic_score": semantic_score,
            "combined_score": combined_score
        })
    
    # Sort by combined score (semantic + domain awareness)
    scored_chunks.sort(key=lambda x: -x["combined_score"])
    
    # Take top_k best results (increased default from 5 to 10)
    filtered = [c["chunk"] for c in scored_chunks[:top_k]]
    domain_relevances = [c["domain_relevance"] for c in scored_chunks[:top_k]]
    avg_domain_relevance = np.mean(domain_relevances) if domain_relevances else 0.0
    
    # Show useful metrics
    keyword_found = sum(1 for relevance in domain_relevances if relevance > 0)
    print(f"[vector_store] Domain '{domain}': {len(filtered)} chunks retrieved (keyword enrichment: {keyword_found}/{len(filtered)}, score: {avg_domain_relevance:.2%})")
    
    return filtered, avg_domain_relevance
