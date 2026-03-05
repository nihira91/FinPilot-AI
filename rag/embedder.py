# ─────────────────────────────────────────────────────────────────────────────
# embedder.py
#
# PURPOSE : Convert text strings into numeric vectors (embeddings).
#
# WHY EMBEDDINGS ?
#   A computer cannot do "find text with similar meaning" on raw strings.
#   An embedding model turns each piece of text into a list of ~384 numbers
#   where semantically similar sentences produce numerically close vectors.
#   That is what powers semantic (meaning-based) search in our RAG pipeline.
#
# WHY sentence-transformers ?
#   • Runs 100 % locally — no API call, no token cost, no rate limits.
#   • "all-MiniLM-L6-v2" is a free HuggingFace model that is small (80 MB),
#     fast, and accurate enough for document retrieval tasks.
#   • The model is downloaded once on first use, then cached automatically.
#
# NOTE : ChromaDB can manage embeddings itself, but we do it manually here
#        so the same embedder can be reused across every agent and collection.
# ─────────────────────────────────────────────────────────────────────────────

from sentence_transformers import SentenceTransformer

# Load the model ONCE at module level.
# Loading is slow (~2 s); doing it once and reusing is much faster.
_MODEL_NAME = "all-MiniLM-L6-v2"   # 384-dimensional output, free on HuggingFace
_model = SentenceTransformer(_MODEL_NAME)

print(f"[embedder] Model '{_MODEL_NAME}' loaded.")


def embed_texts(texts: list) -> list:
    """
    Convert a list of text strings into a list of embedding vectors.

    Args:
        texts : list of strings (your document chunks)

    Returns:
        List of lists — each inner list is a 384-float embedding vector.
        e.g. [[0.12, -0.34, 0.07, ...], [0.56, 0.21, -0.44, ...]]

    WHY return plain Python lists ?
        ChromaDB's add() method expects plain Python lists, not numpy arrays.
    """
    # encode() runs the neural network; convert_to_numpy=False → plain lists
    embeddings = _model.encode(texts, show_progress_bar=True, convert_to_numpy=False)
    return [emb.tolist() for emb in embeddings]
    # .tolist() converts each numpy vector to a plain Python list for ChromaDB


def embed_query(query: str) -> list:
    """
    Embed a single query string.

    Returns a plain Python list of 384 floats.

    WHY a separate function ?
        At query time we always have exactly one string.
        Keeping it separate makes call sites cleaner.
    """
    vector = _model.encode([query], convert_to_numpy=False)
    return vector[0].tolist()   # [0] because encode() always returns a list of vectors