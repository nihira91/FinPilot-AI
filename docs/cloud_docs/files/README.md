# Cloud Architect Agent — Member 4

## What This Agent Does

The Cloud Architect Agent analyses cloud infrastructure requirements and produces structured recommendations covering:

- **Infrastructure Summary** — current or required system scale
- **Architecture Recommendations** — specific AWS/GCP services and configurations
- **Cost Optimisation** — actionable cost-reduction strategies
- **Scalability Roadmap** — step-by-step scaling plan
- **Source References** — documents used in the analysis

It uses the **shared RAG pipeline** (built by Member 3) to retrieve relevant chunks from cloud architecture documents before calling the LLM.

---

## File Structure

```
cloud_architect_agent/
├── __init__.py          # Public API exports
├── cloud_agent.py       # Main agent logic
├── test_cloud_agent.py  # Standalone test suite
└── README.md            # This file

rag/                     # Shared RAG pipeline (from Member 3)
├── __init__.py
├── pdf_loader.py
├── chunker.py
├── embedder.py
├── vector_store.py
├── pipeline.py
├── prompt_templates.py
└── hf_llm.py

docs/
└── cloud_docs/          # ← PUT YOUR PDFs HERE
    ├── aws_architecture.pdf
    ├── gcp_best_practices.pdf
    └── ...

chroma_store/            # Auto-created by ChromaDB (persistent index)
.env                     # GEMINI_API_KEY=your_key_here
requirements.txt
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Add your API key

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Add cloud PDFs

Place any cloud architecture / AWS / GCP documents inside:

```
docs/cloud_docs/
```

### 4. Build the index (one-time)

```python
from cloud_architect_agent import build_cloud_index
build_cloud_index()
```

This reads all PDFs in `docs/cloud_docs/`, chunks them, embeds them, and stores them in ChromaDB. **Only needs to run once** (or when you add new PDFs).

---

## Usage

### As a standalone agent

```python
from cloud_architect_agent import run_cloud_architect_agent, build_cloud_index

# One-time setup
build_cloud_index()

# Query the agent
result = run_cloud_architect_agent(
    "Design a cloud setup for a financial AI system serving 50,000 concurrent users."
)
print(result)
```

### Without RAG (baseline mode)

```python
from cloud_architect_agent import run_cloud_architect_agent_no_rag

result = run_cloud_architect_agent_no_rag(
    "What AWS services are best for a high-availability financial platform?"
)
print(result)
```

### From the Orchestrator (Member 1)

```python
from cloud_architect_agent import run_cloud_architect_agent

# The orchestrator passes a sub-task string
cloud_output = run_cloud_architect_agent(subtask_query)
```

---

## Running Tests

```bash
cd cloud_architect_agent
python test_cloud_agent.py
```

---

## How It Uses the RAG Pipeline

```
User Query
    │
    ▼
rag_query("cloud_docs", query, top_k=5)
    │   retrieves top-5 most relevant chunks from ChromaDB
    ▼
format_context(chunks)
    │   formats chunks into a readable text block with source citations
    ▼
build_user_message(context, query)
    │   injects context + query into the standard RAG prompt
    ▼
call_llm(system_prompt, user_message)
    │   sends to Gemini 2.5 Flash via Google GenAI SDK
    ▼
Structured Response (Infrastructure Summary → Scalability Roadmap)
```

---

## Output Format

Every response follows this exact structure (enforced by the system prompt):

```
## Infrastructure Summary
[2-3 sentence overview]

## Architecture Recommendations
[Bullet list of specific cloud services and configurations]

## Cost Optimisation
[Specific cost-reduction suggestions]

## Scalability Roadmap
[Numbered steps to scale over time]

## Source References
[List of documents used]
```

---

## Hand-off to Member 1 (Orchestrator)

The agent exposes a single clean function:

```python
run_cloud_architect_agent(query: str) -> str
```

Member 1 can call this directly as a node in the LangGraph graph or register it as an MCP tool.
