
import chromadb
from chromadb.config import Settings

from rag.embedder import embed_texts, embed_query

_chroma_client = chromadb.PersistentClient(
    path="./chroma_store",
    settings=Settings(anonymized_telemetry=False)
)


def get_or_create_collection(collection_name: str):
    
    collection = _chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}   # cosine similarity for semantic search
    )
    print(f"[vector_store] Collection '{collection_name}' ready "
          f"({collection.count()} existing vectors).")
    return collection


def add_chunks_to_collection(collection_name: str, chunks: list) -> None:
    
    if not chunks:
        print(f"[vector_store] No chunks to add to '{collection_name}'.")
        return

    collection = get_or_create_collection(collection_name)

    # Find which chunk_ids are already stored so we don't duplicate 
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

    #Prepare the three parallel lists ChromaDB's add() expects 
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
    
    collection = get_or_create_collection(collection_name)

    if collection.count() == 0:
        print(f"[vector_store] WARNING: '{collection_name}' is empty — add documents first.")
        return []

    query_vector = embed_query(query_text)   # embed the query into a vector

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
            "distance": round(dist, 4)   # lower = more relevant
        })

    return retrieved   # already sorted best-first by ChromaDB