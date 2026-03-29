

import sys, os
# Add project root to path so imports work when run from any directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.chunker      import chunk_text, chunk_documents
from rag.embedder     import embed_texts, embed_query
from rag.vector_store import add_chunks_to_collection, query_collection
from rag.pipeline     import rag_query, format_context


# synthetic document chunks (no real PDFs needed for unit tests) 
MOCK_CHUNKS = {
    "financial_reports": [
        {"text": "Q3 net profit increased by 18% to $4.2M due to cost reduction.",
         "source": "financial_q3.pdf", "chunk_id": "financial_q3.pdf_chunk_0"},
        {"text": "Operating expenses declined 12% following the cloud migration.",
         "source": "financial_q3.pdf", "chunk_id": "financial_q3.pdf_chunk_1"},
    ],
    "sales_reports": [
        {"text": "Southeast Asia sales grew 34% year-over-year led by mobile channel.",
         "source": "sales_annual.pdf", "chunk_id": "sales_annual.pdf_chunk_0"},
        {"text": "Product line B shows declining trend in North American markets.",
         "source": "sales_annual.pdf", "chunk_id": "sales_annual.pdf_chunk_1"},
    ],
    "investment_reports": [
        {"text": "The report recommends increasing allocation to emerging market equities.",
         "source": "inv_strategy.pdf", "chunk_id": "inv_strategy.pdf_chunk_0"},
        {"text": "Technology sector shows 40% upside potential based on current valuations.",
         "source": "inv_strategy.pdf", "chunk_id": "inv_strategy.pdf_chunk_1"},
        {"text": "Risk factors include regulatory uncertainty and currency fluctuation.",
         "source": "risk_assessment.pdf", "chunk_id": "risk_assessment.pdf_chunk_0"},
    ],
    "cloud_docs": [
        {"text": "AWS auto-scaling groups are recommended for the data processing tier.",
         "source": "cloud_arch.pdf", "chunk_id": "cloud_arch.pdf_chunk_0"},
    ],
    "routing_rules": [
        {"text": "Queries about stock price route to Financial Analyst agent.",
         "source": "routing.pdf", "chunk_id": "routing.pdf_chunk_0"},
    ],
}


def separator(title: str):
    """Print a visible section header in the test output."""
    print(f"\n{'─'*60}")
    print(f" TEST: {title}")
    print('─'*60)


# Chunker 

def test_chunker():
    separator("Chunker")

    # Create text longer than one chunk (chunk_size=200)
    long_text = "Investment analysis shows strong growth potential. " * 30

    chunks = chunk_text(long_text, chunk_size=200, overlap=20)

    assert len(chunks) > 1, "Long text should produce multiple chunks"
    # Allow 10 % tolerance above chunk_size for the splitter's boundaries
    assert all(len(c) <= 220 for c in chunks), "No chunk should vastly exceed chunk_size"

    print(f"✓ {len(chunks)} chunks from {len(long_text)}-char text")
    print(f"  Chunk 0 preview : {chunks[0][:80]} …")

    # Test chunk_documents with a mock dict
    docs = {"mock.pdf": long_text}
    doc_chunks = chunk_documents(docs)
    assert all("source" in c and "chunk_id" in c for c in doc_chunks)
    print(f"✓ chunk_documents() adds 'source' and 'chunk_id' metadata correctly")


# Embedder 

def test_embedder():
    separator("Embedder")

    texts = [
        "Market expansion opportunity in Asia",
        "Revenue declined due to supply chain issues",
        "Strong Q3 performance"
    ]

    embeddings = embed_texts(texts)

    # Should return a list of 3 vectors, each with 384 floats
    assert len(embeddings) == 3,        "Should produce one vector per input text"
    assert len(embeddings[0]) == 384,   "all-MiniLM-L6-v2 outputs 384-dim vectors"
    assert isinstance(embeddings[0][0], float), "Vector elements should be floats"

    query_vec = embed_query("What are the growth opportunities?")
    assert len(query_vec) == 384,       "Query vector should also be 384-dimensional"

    print(f"✓ embed_texts() : {len(embeddings)} vectors × {len(embeddings[0])} dims")
    print(f"✓ embed_query() : vector of {len(query_vec)} dims")


#  ChromaDB VectorStore (each collection) 

def test_all_collections():
    separator("ChromaDB — all 5 collections")

    for collection_name, chunks in MOCK_CHUNKS.items():
        print(f"\n  ▸ Testing collection : {collection_name}")

        # Add mock chunks (safe to call multiple times — skips duplicates)
        add_chunks_to_collection(collection_name, chunks)

        # Query each collection with a relevant phrase
        query_map = {
            "financial_reports":  "What is the profit trend?",
            "sales_reports":      "Which region has the best sales growth?",
            "investment_reports": "What allocation is recommended?",
            "cloud_docs":         "What cloud services should we use?",
            "routing_rules":      "Where do stock price queries go?",
        }
        results = query_collection(collection_name, query_map[collection_name], top_k=2)

        assert len(results) > 0,        f"Should return results for '{collection_name}'"
        assert "text"     in results[0], "Result must contain 'text'"
        assert "source"   in results[0], "Result must contain 'source'"
        assert "distance" in results[0], "Result must contain 'distance'"

        print(f"    ✓ Retrieved {len(results)} chunks")
        print(f"      Top result (dist={results[0]['distance']}) : "
              f"{results[0]['text'][:60]} …")


# format_context()

def test_format_context():
    separator("format_context()")

    mock_results = [
        {"text": "Emerging markets show strong upside.",
         "source": "inv_strategy.pdf", "distance": 0.12},
        {"text": "Currency risk must be hedged.",
         "source": "risk_report.pdf",  "distance": 0.25},
    ]

    formatted = format_context(mock_results)

    assert "inv_strategy.pdf"  in formatted, "Source filename should appear in context"
    assert "Emerging markets"  in formatted, "Chunk text should appear in context"
    assert "---"               in formatted, "Chunks should be separated by ---"

    print("✓ format_context() produces correctly formatted context string")
    print(f"  Preview :\n{formatted[:200]} …")


#  rag_query() end-to-end via pipeline 

def test_rag_query_pipeline():
    separator("rag_query() — end-to-end pipeline")

    # Pre-populate the investment_reports collection with mock data
    # (build_collection() would load real PDFs; we skip that for unit tests)
    add_chunks_to_collection("investment_reports", MOCK_CHUNKS["investment_reports"])

    results = rag_query("investment_reports",
                        "What investment strategy is recommended?",
                        top_k=3)

    assert len(results) > 0, "rag_query() should return results"
    assert results[0]["distance"] <= results[-1]["distance"], \
        "Results should be sorted best-first (lowest distance first)"

    print(f"✓ rag_query() returned {len(results)} results, sorted by relevance")
    for r in results:
        print(f"  [{r['distance']}] {r['text'][:60]} … ({r['source']})")


# Run all tests 

if __name__ == "__main__":
    print("=" * 60)
    print(" RAG Pipeline Test Suite — Step 6")
    print("=" * 60)

    test_chunker()
    test_embedder()
    test_all_collections()
    test_format_context()
    test_rag_query_pipeline()

    print("\n" + "=" * 60)
    print(" All RAG pipeline tests passed! ✓")
    print("=" * 60)