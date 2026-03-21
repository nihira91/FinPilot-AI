
#Convert text strings into numeric vectors (embeddings).


from sentence_transformers import SentenceTransformer

_MODEL_NAME = "all-MiniLM-L6-v2"   # 384-dimensional output
_model = SentenceTransformer(_MODEL_NAME)

print(f"[embedder] Model '{_MODEL_NAME}' loaded.")


def embed_texts(texts: list) -> list:
    """
    Convert a list of text strings into a list of embedding vectors.
    """
    # encode() runs the neural network;
    embeddings = _model.encode(texts, show_progress_bar=True, convert_to_numpy=False)
    return [emb.tolist() for emb in embeddings]



def embed_query(query: str) -> list:
    """
    Embed a single query string.

    """
    vector = _model.encode([query], convert_to_numpy=False)
    return vector[0].tolist()   # [0] because encode() always returns a list of vectors
