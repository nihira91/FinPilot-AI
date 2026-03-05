# Member 2 — Financial & Sales Agents

This folder contains starter code for Member 2 in the Multi-Agent AI System (Automated Financial Decision Intelligence).

Overview
- `agents/` — contains `FinancialAnalystAgent` and `SalesDataScientistAgent` starter implementations.
- `utils/rag_connector.py` — placeholder to hook into Member 3's RAG pipeline.
- `data/` — sample data folders (`.gitkeep` placeholders).
- `tests/` — simple pytest-based tests that run without an OpenAI key.
- `comparison/` — `single_llm_vs_multiagent.py` to compare single-LLM output vs multi-agent outputs.
- `prompts/` — example prompt templates for each agent.

Quickstart
1. Create a `.env` next to this repo root or set `OPENAI_API_KEY` in your environment. A sample is provided in `.env.example`.
2. Install dependencies (recommended in a virtualenv):

```bash
pip install -r member2/requirements.txt
```

3. Run the comparison script (uses LLM only if `OPENAI_API_KEY` set):

```bash
python member2/comparison/single_llm_vs_multiagent.py
```

Notes on RAG
- The file `member2/utils/rag_connector.py` contains `get_rag_pipeline()` as a placeholder. When Member 3 provides the shared RAG pipeline, update that function to return the pipeline instance so both agents can use it.

Testing
- Tests are lightweight and avoid calling the LLM when `OPENAI_API_KEY` is not set. Run:

```bash
pytest member2/tests
```

Contact
- This folder is maintained by Member 2 (Financial & Sales agents). Coordinate with Member 3 to wire in the RAG pipeline.
