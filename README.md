# 💹 FinPilot AI
### Multi-Agent Financial Intelligence System

> An autonomous AI-powered financial management system that leverages **LLM + RAG** to deliver intelligent, document-grounded financial analysis through a team of specialized agents coordinated by a LangGraph orchestrator.

---

## 📌 Project Overview

FinPilot AI transforms fragmented financial decision-making into a unified, intelligent workflow. Instead of relying on a single LLM with generic knowledge, FinPilot deploys **5 specialized AI agents** — each grounded in domain-specific documents via a shared RAG pipeline — coordinated by an orchestrator that routes queries intelligently.

**Key Achievement:** Reduces manual financial analysis effort by 70–80% through autonomous multi-agent coordination.

---

## 🏗️ System Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────┐
│              Orchestrator Agent                  │
│   LangGraph · RAG Routing · Query Decomposition  │
└───────────┬─────────────────────────────────────┘
            │  Routes to relevant agent(s)
    ┌───────┴────────────────────────────┐
    │                                    │
    ▼                                    ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│Financial │  │  Sales   │  │Investment│  │  Cloud   │
│ Analyst  │  │Scientist │  │Strategist│  │Architect │
│  Agent   │  │  Agent   │  │  Agent   │  │  Agent   │
└────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
     │              │              │              │
     └──────────────┴──────────────┴──────────────┘
                         │
                         ▼
                ┌────────────────┐
                │   Aggregator   │
                │ Final Report   │
                └────────────────┘
                         │
                         ▼
                  User gets unified
                  Executive Summary
```

---

## 🤖 AI Agents

| Agent | Responsibility | RAG Collection | Member |
|-------|---------------|----------------|--------|
| **Orchestrator** | Query routing, task decomposition, result aggregation | `routing_rules` | Member 1 |
| **Financial Analyst** | P&L analysis, budget forecasting, cost analysis | `financial_reports` | Member 2 |
| **Sales Data Scientist** | Trend detection, growth prediction, pattern analysis | `sales_reports` | Member 2 |
| **Investment Strategist** | Strategic insights from consultant reports | `investment_reports` | Member 3 |
| **Cloud Architect** | Infrastructure recommendations, cost optimization | `cloud_docs` | Member 4 |

---

## 🔧 Technology Stack

| Component | Technology |
|-----------|-----------|
| **LLM** | Google Gemini 2.5 Flash |
| **Orchestration** | LangGraph |
| **RAG Pipeline** | ChromaDB + HuggingFace Embeddings |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` |
| **PDF Parsing** | pypdf |
| **Text Splitting** | LangChain RecursiveCharacterTextSplitter |
| **Agent Protocol** | MCP (Model Context Protocol) |
| **Frontend** | Streamlit |
| **Backend** | Python 3.10+ |

---

## 📁 Project Structure

```
FinPilot-AI/
├── agents/
│   ├── financial_agent.py          # Financial Analyst Agent
│   ├── sales_agent.py              # Sales & Data Scientist Agent
│   ├── investment_strategist.py    # Investment Strategist Agent
│   └── cloud_agent.py              # Cloud Architect Agent
│
├── orchestrator/
│   └── orchestrator_agent.py       # LangGraph Orchestrator
│
├── rag/
│   ├── pipeline.py                 # Shared RAG Pipeline
│   ├── chunker.py                  # Text chunking
│   ├── embedder.py                 # HuggingFace embeddings
│   ├── vector_store.py             # ChromaDB operations
│   ├── pdf_loader.py               # PDF text extraction
│   ├── hf_llm.py                   # Gemini LLM client
│   └── prompt_templates.py         # Shared prompt templates
│
├── mcpserver/
│   └── server.py                   # MCP Server (5 tools)
│
├── docs/
│   ├── financial_reports/          # PDFs for Financial Agent
│   ├── sales_reports/              # PDFs for Sales Agent
│   ├── investment_reports/         # PDFs for Investment Agent
│   ├── cloud_docs/                 # PDFs for Cloud Agent
│   └── routing_rules/              # PDFs for Orchestrator
│
├── tests/
│   ├── test_rag_pipeline.py        # RAG pipeline tests
│   ├── test_investment_agent.py    # Investment agent tests
│   ├── test_member2_agents.py      # Financial & Sales tests
│   ├── test_mcp.py                 # MCP server tests
│   └── test_comparison.py         # Single LLM vs RAG comparison
│
├── streamlit_app.py                # Web UI
├── main.py                         # CLI entry point
├── requirements.txt
├── .env                            # API keys (never commit!)
└── .gitignore
```

---

## ⚡ Quick Start

### 1. Clone & Setup

```bash
git clone https://github.com/nihira91/FinPilot-AI.git
cd FinPilot-AI/FinPilot-AI

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Key

Create a `.env` file in the root directory:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your free Gemini API key at: https://aistudio.google.com/app/apikey

### 3. Add Documents

Place PDF files in the appropriate folders:

```
docs/financial_reports/     ← Financial PDFs (annual reports, P&L statements)
docs/sales_reports/         ← Sales PDFs (sales data, regional reports)
docs/investment_reports/    ← Consultant reports, strategy documents
docs/cloud_docs/            ← AWS/GCP documentation
docs/routing_rules/         ← Routing instructions (optional)
```

### 4. Run the Application

```bash
# Web UI (Recommended)
streamlit run streamlit_app.py

# OR Command Line
python main.py
```

---

## 🚀 Usage

### Web Interface

1. Open `http://localhost:8501` in your browser
2. Upload PDFs via the sidebar for each collection
3. Click **"Build Knowledge Base"** to index documents
4. Enter your query or use sample query buttons
5. Click **"Run Analysis"** to get AI-powered insights

### Sample Queries

**Single Agent:**
```
"Analyse our Q3 financial performance"
"What are our sales trends this year?"
"What investment strategy is recommended?"
"Recommend cloud infrastructure for scaling"
```

**Multi-Agent:**
```
"Based on financial data, suggest investment opportunities"
"Analyze sales trends and recommend expansion strategy"
"Give complete business intelligence report"
```

---

## 🧠 RAG Pipeline

The shared RAG pipeline powers all 5 agents:

```python
from rag.pipeline import build_collection, rag_query, format_context

# Step 1: Build index from PDFs (one time)
build_collection("financial_reports")

# Step 2: Query at runtime
chunks  = rag_query("financial_reports", "What is Q3 profit?", top_k=5)
context = format_context(chunks)

# Step 3: Inject into LLM prompt
# context is now ready to use in your agent
```

**Pipeline Flow:**
```
PDF Files → Text Extraction → Chunking (500 chars, 50 overlap)
         → Embeddings (384-dim) → ChromaDB Storage
         → Cosine Similarity Search → Top-K Retrieval
         → Context Injection → Gemini LLM → Structured Response
```

---

## 🔌 MCP Server

FinPilot exposes all agents as MCP tools:

```bash
python mcpserver/server.py
```

**Available Tools:**

| Tool | Description |
|------|-------------|
| `orchestrate` | Main entry point — routes and aggregates |
| `financial_agent` | Financial analysis tool |
| `sales_agent` | Sales trend analysis tool |
| `investment_agent` | Investment strategy tool |
| `cloud_agent` | Cloud architecture tool |

---

## 🧪 Testing

```bash
# Test RAG Pipeline
python tests/test_rag_pipeline.py

# Test Investment Agent
python tests/test_investment_agent.py

# Test Financial & Sales Agents
python tests/test_member2_agents.py

# Test MCP Tools
python tests/test_mcp.py

# Compare Single LLM vs Multi-Agent RAG
python tests/test_comparison.py
```

---

## 📊 Single LLM vs Multi-Agent RAG

| Feature | Single LLM | FinPilot Multi-Agent RAG |
|---------|-----------|--------------------------|
| **Knowledge Source** | Pre-trained only | Your actual documents |
| **Specificity** | Generic answers | Document-grounded answers |
| **Source Citations** | None | Cites exact PDFs |
| **Domain Expertise** | General | 5 specialized agents |
| **Hallucination Risk** | High | Significantly reduced |
| **Routing Intelligence** | None | Smart query decomposition |

---

## 👥 Team

| Member | Role | Responsibility |
|--------|------|---------------|
| **Member 1** | Orchestrator Lead | LangGraph, MCP, Integration, Streamlit UI |
| **Member 2** | Financial & Sales | Financial Agent, Sales Agent, Pandas Analysis |
| **Member 3** | RAG Pipeline | Shared RAG Pipeline, Investment Agent |
| **Member 4** | Cloud Architect | Cloud Agent, Infrastructure Recommendations |

---

## 📋 Requirements

```
Python 3.10+
langchain
langgraph
langchain-google-genai
google-genai
sentence-transformers
chromadb
pypdf
streamlit
pandas
numpy
python-dotenv
mcp
faiss-cpu
```

---

## ⚠️ Important Notes

- **Never commit `.env` file** — it contains your API keys
- **Rate Limits** — Gemini free tier allows 5 requests/minute on gemini-2.5-flash
- **ChromaDB** — Data persists in `chroma_store/` — no need to rebuild unless PDFs change
- **First Run** — Embedding model downloads ~80MB on first use (cached after)

---



<div align="center">
<strong>Built with ❤️ using LLM + RAG + LangGraph + MCP</strong>
</div>
