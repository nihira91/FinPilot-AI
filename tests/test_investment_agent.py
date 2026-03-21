#  Test Investment Agent independently


import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.vector_store import add_chunks_to_collection
from rag.pipeline     import rag_query


# Mock investment document chunks 
MOCK_INVESTMENT_CHUNKS = [
    {
        "text": "The consultant report recommends a 30% portfolio allocation to "
                "emerging market bonds in Southeast Asia due to high yield potential.",
        "source": "consultant_strategy_2024.pdf",
        "chunk_id": "consultant_strategy_2024.pdf_chunk_0"
    },
    {
        "text": "Technology sector valuations remain attractive with 40% upside "
                "potential. AI infrastructure companies are particularly favoured.",
        "source": "tech_investment_outlook.pdf",
        "chunk_id": "tech_investment_outlook.pdf_chunk_0"
    },
    {
        "text": "Inflation risk remains elevated. Fixed income portfolios should "
                "shift toward inflation-linked bonds and shorter duration assets.",
        "source": "macro_risk_report.pdf",
        "chunk_id": "macro_risk_report.pdf_chunk_0"
    },
    {
        "text": "The fund recommends reducing exposure to commercial real estate "
                "given rising vacancy rates in major urban markets.",
        "source": "asset_allocation_memo.pdf",
        "chunk_id": "asset_allocation_memo.pdf_chunk_0"
    },
]


def test_rag_retrieval_for_agent():
    """Step 7a — Verify agent retrieves correct chunks before calling LLM."""
    print("\n── TEST 7a : RAG Retrieval for Investment Agent ─────────────")

    # Inject mock data directly, no real PDFs needed
    add_chunks_to_collection("investment_reports", MOCK_INVESTMENT_CHUNKS)

    query = "What allocation strategy is recommended and what are the risks?"
    chunks = rag_query("investment_reports", query, top_k=3)

    assert len(chunks) > 0,    "Agent should retrieve at least one chunk"
    assert "text"   in chunks[0], "Chunk must have text field"
    assert "source" in chunks[0], "Chunk must have source field"

    print(f"✓ Retrieved {len(chunks)} chunks for agent query")
    for c in chunks:
        print(f"  [{c['distance']}] {c['text'][:70]} … ({c['source']})")


def test_agent_full_run_with_mock_llm():
    """
    Step 7b — Test full agent pipeline with a MOCKED LLM response.
    This lets us test the pipeline structure without needing an API token.
    """
    print("\n── TEST 7b : Full Agent Run (mocked LLM) ────────────────────")

    import unittest.mock as mock

    # Inject mock data
    add_chunks_to_collection("investment_reports", MOCK_INVESTMENT_CHUNKS)

    # Patch call_llm() to return a fake response ,no API call made
    fake_llm_response = """## Executive Summary
Based on the provided documents, a diversified strategy with emerging market
exposure is recommended alongside technology sector positions.

## Key Insights
- 30% allocation to Southeast Asian emerging market bonds recommended
- Technology sector has 40% upside potential
- Inflation risk requires duration management

## Strategic Recommendations
1. Increase emerging market bond allocation to 30%
2. Add AI infrastructure equities for technology exposure
3. Reduce commercial real estate exposure

## Risk Factors
- Elevated inflation may erode fixed income returns
- Currency fluctuation in Southeast Asian markets

## Source References
- consultant_strategy_2024.pdf
- tech_investment_outlook.pdf
- macro_risk_report.pdf"""

    with mock.patch("rag.hf_llm.call_llm", return_value=fake_llm_response):
        from agents.investment_strategist import run

        result = run("What allocation strategy is recommended?", top_k=3)

    # Verify the returned dict has all required fields
    assert result["agent"]        == "Investment Strategist", "Agent name must be correct"
    assert result["chunks_used"]  >  0,    "Must use at least one chunk"
    assert len(result["response"]) > 50,   "Response should be a full analysis"
    assert isinstance(result["sources"], list), "Sources must be a list"

    print(f"✓ Agent name    : {result['agent']}")
    print(f"✓ Chunks used   : {result['chunks_used']}")
    print(f"✓ Sources       : {result['sources']}")
    print(f"✓ Response length: {len(result['response'])} characters")
    print(f"\n  RESPONSE PREVIEW:\n{result['response'][:400]} …")


def test_agent_with_live_api():
    """
    Step 7c — Full test with REAL HuggingFace API.
    Only runs if HF_API_TOKEN is set in the environment.
    Skip this if you don't have a token yet.
    """
    print("\n── TEST 7c : Full Agent Run (live HuggingFace API) ──────────")

    token = os.getenv("HF_API_TOKEN") or __import__("dotenv").dotenv_values(".env").get("HF_API_TOKEN")

    if not token or token == "hf_your_token_here":
        print("⚠  HF_API_TOKEN not set — skipping live API test.")
        print("   Add your token to .env to run this test.")
        return

    # Inject mock data
    add_chunks_to_collection("investment_reports", MOCK_INVESTMENT_CHUNKS)

    from agents.investment_strategist import run

    result = run("Summarise the key investment opportunities and risks.", top_k=4)

    assert result["agent"] == "Investment Strategist"
    assert len(result["response"]) > 100, "Live LLM should produce a full response"
    assert "[LLM Error]" not in result["response"], \
        f"LLM returned an error: {result['response']}"

    print(f"✓ Live API test passed!")
    print(f"  Sources : {result['sources']}")
    print(f"\n  FULL RESPONSE:\n{result['response']}")


if __name__ == "__main__":
    print("=" * 60)
    print(" Investment Strategist Agent Test Suite — Step 7")
    print("=" * 60)

    test_rag_retrieval_for_agent()
    test_agent_full_run_with_mock_llm()
    test_agent_with_live_api()           # skipped automatically if no token

    print("\n" + "=" * 60)
    print(" All Investment Agent tests passed! ✓")
    print("=" * 60)
