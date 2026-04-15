<div align="center">

<br/>

# FinPilot-AI

**Multi-Agent Financial Intelligence Platform**

A smart financial analysis platform powered by 5 specialized AI agents with RAG-enhanced analysis for actionable, document-grounded insights.

[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-19-61dafb?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-blueviolet?style=flat-square)](https://langgraph.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

</div>

---

## Overview

FinPilot-AI combines five domain-specialized AI agents with a shared RAG pipeline to answer financial queries using your actual documents — not generic pre-trained knowledge. The orchestrator automatically routes each query to the right agent (or agents), synthesizes results, and returns structured, citation-grounded analysis.

---

## Architecture

```
                            ╔═══════════╗
                            ║   START   ║
                            ╚═════╦═════╝
                                  ║
                                  ▼
                    ┌─────────────────────────────┐
                    │   User login / authentication│
                    │      Session validated        │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │   Upload financial documents │
                    │   PDFs, reports, spreadsheets│
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ╔═════════════════════════════╗
                    ║  RAG pipeline: chunking &   ║
                    ║       embedding             ║
                    ║  Tokenise, vectorise, index ║
                    ╚══════════════╦══════════════╝
                                   ║
                                   ▼
                    ╔═════════════════════════════╗
                    ║  Store in ChromaDB vector DB║
                    ║   Persistent vector storage  ║
                    ╚══════════════╦══════════════╝
                                   ║
                                   ▼
                    ┌─────────────────────────────┐
                    │      User submits query      │
                    │      Natural language input  │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │  Orchestrator agent routes   │
                    │  Classifies intent, selects  │
                    └──┬────────┬────────┬────┬───┘
                       │        │        │    │
           ┌───────────┘   ┌────┘    ┌───┘   └────────────┐
           │               │         │                     │
           ▼               ▼         ▼                     ▼
   ┌───────────────┐ ┌──────────┐ ┌──────────────┐ ┌─────────────┐
   │  Financial    │ │  Sales   │ │  Investment  │ │    Cloud    │
   │  analyst      │ │  data    │ │  strategist  │ │  architect  │
   │  agent        │ │scientist │ │  agent       │ │  agent      │
   └───────┬───────┘ └────┬─────┘ └──────┬───────┘ └──────┬──────┘
           │              │              │                  │
           └──────────────┴──────┬───────┴──────────────────┘
                                  │
                                  ▼
                    ╔═════════════════════════════╗
                    ║ Each agent processes via    ║
                    ║       LLM + RAG             ║
                    ║ Vector retrieval + inference ║
                    ╚══════════════╦══════════════╝
                                   ║
                                   ▼
                    ┌─────────────────────────────┐
                    │      Synthesize results      │
                    │      Merge agent outputs     │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │  Generate visualization      │
                    │  Charts, dashboards, insights│
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                    ┌─────────────────────────────┐
                    │   Display to user dashboard  │
                    │   React UI, interactive view │
                    └──────────────┬──────────────┘
                                   │
                                   ▼
                            ╔═══════════╗
                            ║    END    ║
                            ╚═══════════╝
```

> `╔══╗` **Bold border** = core pipeline stages (RAG, ChromaDB, LLM processing)  
> `┌──┐` **Thin border** = user-facing steps and agent nodes

---

## Agents

| Agent | Purpose |
|---|---|
| **Orchestrator** | Parses intent, routes to one or more agents, synthesizes results |
| **Financial Analyst** | P&L analysis, cost optimization, budget forecasting |
| **Sales Data Scientist** | Revenue trends, regional breakdowns, growth prediction |
| **Investment Strategist** | Risk profiling, portfolio analysis, strategy recommendations |
| **Cloud Architect** | Infrastructure cost analysis, scaling recommendations |

---

## Tech Stack

**Backend** — FastAPI · LangChain · LangGraph · ChromaDB · HuggingFace Embeddings  
**Frontend** — React 19 · Vite · TailwindCSS · Framer Motion · Plotly.js  
**Auth & DB** — Supabase 
**LLM** — Google Gemini  


---

## Project Structure

```
FinPilot-AI/
├── api.py                          # FastAPI server (main entry point)
├── main.py                         # CLI entry point
├── requirements.txt
│
├── agents/
│   ├── financial_agent_core/
│   │   ├── runner.py               # Financial analysis logic
│   │   ├── metrics.py              # KPI calculations
│   │   └── visualization.py        # Chart generation
│   ├── sales_agent_core/
│   │   ├── runner.py
│   │   └── metrics.py
│   ├── cloud_architect_agent/
│   │   └── cloud_agent.py
│   └── orchestrator_agent.py
│
├── rag/
│   ├── pipeline.py                 # Main RAG orchestration
│   ├── chunker.py                  # Document chunking
│   ├── embedder.py                 # Vector embeddings
│   ├── vector_store.py             # ChromaDB interface
│   ├── pdf_loader.py               # PDF parsing
│   ├── hf_llm.py                   # LLM interface
│   └── prompt_templates.py
│
├── orchestrator/
│   ├── chatbot.py
│   └── orchestrator_agent.py
│
├── mcpserver/
│   └── server.py                   # MCP Server (5 tools)
│
├── frontend/
│   ├── src/
│   │   ├── pages/                  # Dashboard, Home, Login, Register
│   │   ├── lib/supabase.js
│   │   └── App.jsx
│   └── vite.config.js
│
├── docs/
│   ├── financial_reports/          # PDFs for Financial Agent
│   ├── sales_reports/              # PDFs for Sales Agent
│   ├── investment_reports/         # PDFs for Investment Agent
│   ├── cloud_docs/                 # PDFs for Cloud Agent
│   └── routing_rules/
│
├── tests/
│   ├── test_rag_pipeline.py
│   ├── test_investment_agent.py
│   ├── test_member2_agents.py
│   ├── test_mcp.py
│   └── test_comparison.py
│
├── chroma_store/                   # Persisted vector database
├── streamlit_app.py                # Web UI (Streamlit)
└── .env                            # API keys — never commit!
```

---

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/nihira91/FinPilot-AI.git
cd FinPilot-AI

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```env
# .env
GEMINI_API_KEY=your_gemini_key      # https://aistudio.google.com/app/apikey
OPENAI_API_KEY=sk-...               # optional
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJhbGc...
DATABASE_URL=postgresql://user:pass@localhost/db
```

Get a free Gemini key at [aistudio.google.com](https://aistudio.google.com/app/apikey).

### 3. Add documents

```
docs/financial_reports/     ← Annual reports, P&L statements
docs/sales_reports/         ← Sales data, regional breakdowns
docs/investment_reports/    ← Strategy documents, consultant reports
docs/cloud_docs/            ← AWS/GCP architecture docs
```

### 4. Run

```bash
# Streamlit UI (recommended)
streamlit run streamlit_app.py
# → http://localhost:8501

# FastAPI backend
python api.py
# → http://localhost:8000

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
# → http://localhost:5173
```

---

## API Reference

```
POST   /api/chat           Submit a query to the agent system
POST   /api/upload         Upload financial documents (PDF, CSV, XLSX)
GET    /api/history        Retrieve chat history for a session
POST   /api/sessions/new   Create a new session
POST   /api/clear          Clear session data
```

Full interactive docs at `http://localhost:8000/docs`.

**Example — financial analysis:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "s1", "query": "Analyze our Q3 P&L for cost reduction opportunities"}'
```

**Example — upload documents:**
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "session_id=s1" \
  -F "collection=financial" \
  -F "files=@report.pdf"
```

---

## RAG Pipeline

```python
from rag.pipeline import build_collection, rag_query, format_context

# Index PDFs once
build_collection("financial_reports")

# Query at runtime
chunks  = rag_query("financial_reports", "What is Q3 profit?", top_k=5)
context = format_context(chunks)

# Inject into agent prompt
# context is now ready for LLM generation
```

ChromaDB data persists in `chroma_store/` — no need to rebuild unless documents change.

---

## MCP Server

Exposes all five agents as MCP tools:

```bash
python mcpserver/server.py
```

| Tool | Description |
|---|---|
| `orchestrate` | Main entry point — routes and aggregates across agents |
| `financial_agent` | Financial analysis |
| `sales_agent` | Sales trend analysis |
| `investment_agent` | Investment strategy |
| `cloud_agent` | Cloud architecture recommendations |

---

## Single LLM vs Multi-Agent RAG

| | Single LLM | FinPilot Multi-Agent RAG |
|---|---|---|
| Knowledge source | Pre-trained only | Your uploaded documents |
| Specificity | Generic answers | Document-grounded answers |
| Source citations | None | Cites exact PDFs |
| Domain expertise | General | 5 specialized agents |
| Hallucination risk | High | Significantly reduced |
| Query routing | None | Smart decomposition |

---

## Testing

```bash
pytest tests/ -v                             # All tests
pytest tests/ --cov=. --cov-report=html      # With coverage report

python tests/test_rag_pipeline.py            # RAG pipeline
python tests/test_investment_agent.py        # Investment agent
python tests/test_member2_agents.py          # Financial & Sales agents
python tests/test_mcp.py                     # MCP server tools
python tests/test_comparison.py              # Single LLM vs RAG comparison

# Code quality
black . && isort . && flake8 .
cd frontend && npm run lint
```

---



## Security

- Supabase authentication with JWT session management
- Per-user document isolation — no cross-session data access
- API keys managed via environment variables only — never in source
- CORS protection and input validation on all endpoints
- Rate limiting ready (add retry/backoff logic for production)

> **Never commit your `.env` file.**

---

## Troubleshooting

| Issue | Fix |
|---|---|
| ChromaDB error | `python clear_chromadb.py` |
| API rate limit hit | Add retry + exponential backoff |
| Document upload fails | Check file size < 100MB, format PDF/CSV/XLSX |
| Frontend won't connect | Verify backend on `:8000`, check `VITE_API_BASE_URL` |
| Backend won't start | `lsof -i :8000` to check port; `pip install -r requirements.txt` |
| First run is slow | Embedding model (~80MB) downloads once and caches |

---


## Contributing

```bash
git checkout -b feature/your-feature
git commit -m "Add your feature"
git push origin feature/your-feature
# → Open a Pull Request
```

Follow PEP 8 for Python, use functional React components, and include tests for new features.

---

## Team

| Member | Role |
|---|---|
| **Nihira** | Orchestrator, React UI, Plotly integration |
| **Yeeshika** | RAG Pipeline, Investment Agent |
| **Nishi** | Financial Agent, Sales Agent, Pandas Analysis |
| **Nikita** | Cloud Architect Agent, Infrastructure Recommendations |

---

## Documentation

- [API Reference](docs/API.md)
- [Agent Development Guide](docs/AGENT_GUIDE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Architecture Deep Dive](docs/ARCHITECTURE.md)

---

## Acknowledgements

Built with [LangChain](https://langchain.com) · Powered by [Google Gemini](https://deepmind.google/technologies/gemini/) · UI inspired by modern fintech applications

---

<div align="center">

MIT License · [Report a bug](https://github.com/nihira91/finpilot-ai/issues) · [Discussions](https://github.com/nihira91/finpilot-ai/discussions)

**Built with ❤️ by the FinPilot-AI Team**

</div>
# FinPilot-AI
# This is the project built as a multiagent rag based system.
