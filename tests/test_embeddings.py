# tests/test_embeddings.py
from langchain_huggingface import HuggingFaceEmbeddings

# HuggingFace embeddings stay same
# Only LLM changes to Gemini
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

test = embeddings.embed_query("Test financial query")
print("Embeddings working!")
print(f"Embedding size: {len(test)}")