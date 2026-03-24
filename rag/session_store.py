# ─────────────────────────────────────────────────────────────────────────────
# rag/session_store.py — Session Management for User Collections
# ─────────────────────────────────────────────────────────────────────────────

import chromadb
from chromadb.config import Settings

# Global session client (RAM-based, ephemeral)
_session_client = None
_collection_cache = {}  # Cache to avoid re-creating with different settings


def get_session_client():
    """
    Get or create session client (ephemeral, RAM-based).
    User collections stored here — cleared on session end.
    """
    global _session_client
    if _session_client is None:
        print("[Session Store] Creating ephemeral client...")
        _session_client = chromadb.EphemeralClient(
            settings=Settings(anonymized_telemetry=False)
        )
    return _session_client


def get_system_client():
    """
    Get system client (persistent, disk-based).
    System collections stored here — permanent.
    """
    return chromadb.PersistentClient(
        path="./chroma_store/system",
        settings=Settings(anonymized_telemetry=False)
    )


def get_collection(name: str, collection_type: str = "user", embedder=None):
    """
    Get or create collection from appropriate client.
    
    Args:
        name: Collection name (e.g., "financial_reports")
        collection_type: "system" or "user"
        embedder: Optional embedder function (IGNORED - ChromaDB manages internally)
    
    Returns:
        ChromaDB collection object
    """
    global _collection_cache
    
    # Check cache first (prevents re-creating with different settings)
    cache_key = f"{collection_type}:{name}"
    if cache_key in _collection_cache:
        print(f"[Session Store] Using cached collection: {name}")
        return _collection_cache[cache_key]
    
    if collection_type == "system":
        client = get_system_client()
    else:
        client = get_session_client()
    
    try:
        # Get or create WITHOUT embedder - let ChromaDB handle it
        # Use consistent metadata across ALL collections
        collection = client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"}
        )
        _collection_cache[cache_key] = collection
        print(f"[Session Store] Collection created/retrieved: {name} (type: {collection_type})")
        return collection
    
    except Exception as e:
        error_msg = str(e).lower()
        
        # Handle "already exists" error gracefully
        if "already exists" in error_msg or "ephemeral" in error_msg:
            print(f"[Session Store] Collection '{name}' conflict detected, attempting recovery...")
            try:
                # Try to get existing collection
                collection = client.get_collection(name=name)
                _collection_cache[cache_key] = collection
                print(f"[Session Store] Successfully recovered collection: {name}")
                return collection
            except Exception as e2:
                print(f"[Session Store] Recovery failed for '{name}': {e2}")
                raise
        else:
            print(f"[Session Store] ERROR creating collection '{name}': {e}")
            raise


def clear_session():
    """
    Clear all user session collections (RAM).
    System collections remain intact (disk).
    """
    global _session_client, _collection_cache
    
    print("[Session Store] Clearing session collections...")
    
    if _session_client is not None:
        try:
            # Delete all collections in session client
            collections = _session_client.list_collections()
            for col in collections:
                _session_client.delete_collection(name=col.name)
                # Remove from cache
                cache_key = f"user:{col.name}"
                if cache_key in _collection_cache:
                    del _collection_cache[cache_key]
            
            print(f"[Session Store] Deleted {len(collections)} session collections")
        except Exception as e:
            print(f"[Session Store] Error clearing collections: {e}")
    
    # Reset session client
    _session_client = None
    _collection_cache = {k: v for k, v in _collection_cache.items() if k.startswith("system:")}
    print("[Session Store] Session cleared. Ready for new session.")


def list_session_collections() -> list:
    """List all collections in session (RAM)."""
    client = get_session_client()
    try:
        return [col.name for col in client.list_collections()]
    except Exception:
        return []


def list_system_collections() -> list:
    """List all collections in system (disk)."""
    client = get_system_client()
    try:
        return [col.name for col in client.list_collections()]
    except Exception:
        return []
