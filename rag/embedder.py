# Convert text strings into numeric vectors (embeddings).

from sentence_transformers import SentenceTransformer

# Load the model ONCE at module level.

_MODEL_NAME = "all-MiniLM-L6-v2"   # 384-dimensional output, free on HuggingFace
_model = SentenceTransformer(_MODEL_NAME)

print(f"[embedder] Model '{_MODEL_NAME}' loaded.")


def embed_texts(texts: list) -> list:
    """
    Convert a list of text strings into a list of embedding vectors.

    Args:
        texts : list of strings 

    Returns:
        List of lists — each inner list is a 384-float embedding vector.
    """
    # encode() runs the neural network; convert_to_numpy=False > plain lists
    embeddings = _model.encode(texts, show_progress_bar=True, convert_to_numpy=False) 
    return [emb.tolist() for emb in embeddings]
    # .tolist() converts each numpy vector to a plain Python list for ChromaDB


def embed_query(query: str) -> list:
    """
    Embed a single query string.

    Returns a plain Python list of 384 floats.
    """
    vector = _model.encode([query], convert_to_numpy=False)
    return vector[0].tolist()   # [0] because encode() always returns a list of vectors
