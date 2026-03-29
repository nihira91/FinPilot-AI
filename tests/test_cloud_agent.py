

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.cloud_agent import (
    build_cloud_index,
    run_cloud_architect_agent,
    run_cloud_architect_agent_no_rag,
)
from rag.pipeline import rag_query

DIVIDER = "=" * 70

TEST_QUERIES = [
    "What cloud services should we use to host and scale a multi-agent AI system?",
    "How can we reduce cloud infrastructure costs for a high-traffic financial platform?",
    "Design a scalable deployment strategy for processing 1 million financial documents per day.",
]


def run_tests():
    print(DIVIDER)
    print("CLOUD ARCHITECT AGENT — TEST SUITE")
    print(DIVIDER)

    #  Build index
    print("\n[TEST] Step 1: Ensuring cloud_docs collection is indexed…")
    build_cloud_index()

    #  Step 2: Test each query 
    for i, query in enumerate(TEST_QUERIES, start=1):
        print(f"\n{DIVIDER}")
        print(f"[TEST {i}] Query: {query}")
        print(DIVIDER)

        # Check if collection has data
        chunks = rag_query("cloud_docs", query, top_k=1)

        if chunks:
            print("\n--- RAG-POWERED OUTPUT ---")
            rag_result = run_cloud_architect_agent(query)
            print(rag_result)
        else:
            print("\n[TEST] cloud_docs collection empty — running baseline mode.")
            baseline_result = run_cloud_architect_agent_no_rag(query)
            print("\n--- BASELINE (No RAG) OUTPUT ---")
            print(baseline_result)

    #  Step 3: Comparison test 
    print(f"\n{DIVIDER}")
    print("[TEST] Step 3: RAG vs Baseline Comparison (Query 1)")
    print(DIVIDER)

    compare_query = TEST_QUERIES[0]
    chunks = rag_query("cloud_docs", compare_query, top_k=1)

    if chunks:
        print("\n=== WITH RAG CONTEXT ===")
        rag_out = run_cloud_architect_agent(compare_query)
        print(rag_out)

        print("\n=== WITHOUT RAG CONTEXT (Baseline) ===")
        baseline_out = run_cloud_architect_agent_no_rag(compare_query)
        print(baseline_out)
    else:
        print("[TEST] Skipping comparison — no cloud_docs indexed. Add PDFs to docs/cloud_docs/")

    print(f"\n{DIVIDER}")
    print("ALL TESTS COMPLETE")
    print(DIVIDER)


if __name__ == "__main__":
    run_tests()