# FinPilot-AI

# Multi-Agent AI System — Member 3: Shared RAG Pipeline + Investment Strategist

## My Responsibilities (Steps 1–9)
| Step | Task | Status |
|------|------|--------|
| 1 | Install dependencies | `requirements.txt` ready |
| 2 | Collect sample PDFs | Add to `docs/investment_reports/` |
| 3 | Build shared RAG pipeline | `rag/pipeline.py` |
| 4 | Investment Strategist Agent | `agents/investment_strategist.py` |
| 5 | Shared prompt templates | `rag/prompt_templates.py` |
| 6 | Test RAG pipeline | `tests/test_rag_pipeline.py` |
| 7 | Test Investment Agent | `tests/test_investment_agent.py` |
| 8 | Share with team | See "For Teammates" below |
| 9 | Single-LLM vs RAG comparison | `tests/test_comparison.py` |

---

## Setup
```bash
# 1. Install all dependencies
pip install -r requirements.txt

# 2. Add your FREE HuggingFace token
# Get one at: https://huggingface.co/settings/tokens
echo "HF_API_TOKEN=hf_your_token_here" > .env

# 3. Add your PDFs to the correct folders
mkdir -p docs/investment_reports docs/financial_reports docs/sales_reports docs/cloud_docs docs/routing_rules
# → copy your consultant PDFs into docs/investment_reports/

# 4. Build the RAG index (one time only)
python -c "from rag.pipeline import build_collection; build_collection('investment_reports')"

# 5. Run tests
python tests/test_rag_pipeline.py
python tests/test_investment_agent.py
python tests/test_comparison.py
```

---

## For Teammates — How to Use the Shared RAG Pipeline
```python
# In your agent file, just import these two functions:
from rag.pipeline import build_collection, rag_query, format_context
from rag.prompt_templates import AGENT_SYSTEM_PROMPTS, build_user_message
from rag.hf_llm import call_llm

# Step 1 (one time): build your collection
build_collection("financial_reports")   # Member 1
build_collection("sales_reports")       # Member 2
build_collection("cloud_docs")          # Member 4

# Step 2 (every query): get relevant chunks
chunks  = rag_query("financial_reports", "What is the Q3 profit trend?")
context = format_context(chunks)

# Step 3: call the LLM with context
system   = AGENT_SYSTEM_PROMPTS["financial_analyst"]
user_msg = build_user_message(context, "What is the Q3 profit trend?")
response = call_llm(system, user_msg)
```

## Collection → Folder Mapping
| Collection | PDF Folder | Used By |
|------------|-----------|---------|
| `financial_reports` | `docs/financial_reports/` | Member 1 — Financial Analyst |
| `sales_reports` | `docs/sales_reports/` | Member 2 — Sales & Data Scientist |
| `investment_reports` | `docs/investment_reports/` | **Member 3 — Investment Strategist (YOU)** |
| `cloud_docs` | `docs/cloud_docs/` | Member 4 — Cloud Architect |
| `routing_rules` | `docs/routing_rules/` | Orchestrator |