
from rag.pipeline import build_collection
from agents.investment_strategist import run


build_collection("investment_reports")

# Ask the agent a question
result = run("What is the future of banking and what precision strategies are recommended?")

print("\n" + "="*50)
print(f"Agent     : {result['agent']}")
print(f"Sources   : {result['sources']}")
print(f"Chunks    : {result['chunks_used']}")
print("="*50)
print(result['response'])