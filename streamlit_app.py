# streamlit_app.py
import streamlit as st
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from rag.pipeline import build_collection, COLLECTIONS
from orchestrator.orchestrator_agent import build_graph

load_dotenv()

# ── Page Config ───────────────────────────────────────────
st.set_page_config(
    page_title="FinPilot AI",
    page_icon="💹",
    layout="wide"
)

# ── Title ─────────────────────────────────────────────────
st.title("💹 FinPilot AI")
st.caption("Multi-Agent Financial Intelligence System powered by LLM + RAG")

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.header("📁 Upload Documents")
    st.caption("Upload PDFs for each agent")

    collection_labels = {
        "financial_reports":  "📊 Financial Reports",
        "sales_reports":      "📈 Sales Reports",
        "investment_reports": "💰 Investment Reports",
        "cloud_docs":         "☁️ Cloud Documents",
        "routing_rules":      "🔀 Routing Rules",
    }

    uploaded_any = False

    for collection, label in collection_labels.items():
        st.subheader(label)
        uploaded_files = st.file_uploader(
            f"Upload PDFs",
            type=["pdf"],
            accept_multiple_files=True,
            key=collection
        )

        if uploaded_files:
            # Save PDFs to correct docs/ folder
            folder = COLLECTIONS[collection]
            os.makedirs(folder, exist_ok=True)

            for uploaded_file in uploaded_files:
                save_path = os.path.join(folder, uploaded_file.name)
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

            uploaded_any = True

    if uploaded_any:
        if st.button("🔄 Build Knowledge Base", type="primary"):
            with st.spinner("Building knowledge base..."):
                for collection in COLLECTIONS:
                    folder = COLLECTIONS[collection]
                    if os.path.exists(folder):
                        files = [f for f in os.listdir(folder) if f.endswith('.pdf')]
                        if files:
                            st.write(f"Processing {collection}...")
                            build_collection(collection)
            st.success("✅ Knowledge base ready!")

    st.divider()
    st.caption("Built with LangGraph + RAG + Gemini")


# ── Main Area ─────────────────────────────────────────────
tab1, tab2 = st.tabs(["💬 Ask Query", "ℹ️ System Info"])

# ── Tab 1: Query ──────────────────────────────────────────
with tab1:
    st.subheader("Ask FinPilot AI")

    # Sample queries
    st.caption("Sample queries:")
    col1, col2, col3 = st.columns(3)

    sample_query = ""
    with col1:
        if st.button("📊 Q3 Financial Analysis"):
            sample_query = "Analyse our Q3 financial performance"
    with col2:
        if st.button("📈 Sales Trends"):
            sample_query = "What are our sales trends this year?"
    with col3:
        if st.button("💰 Investment Strategy"):
            sample_query = "What investment strategy is recommended?"

    col4, col5 = st.columns(2)
    with col4:
        if st.button("☁️ Cloud Infrastructure"):
            sample_query = "Recommend cloud infrastructure for scaling"
    with col5:
        if st.button("🔍 Complete Analysis"):
            sample_query = "Give complete analysis of our business"

    # Query input
    query = st.text_area(
        "Enter your financial query:",
        value=sample_query,
        height=100,
        placeholder="e.g. Analyse our Q3 financial performance..."
    )

    if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
        if not query.strip():
            st.warning("Please enter a query!")
        else:
            with st.spinner("🤖 Agents working..."):
                try:
                    # Show progress
                    progress = st.progress(0)
                    status   = st.empty()

                    status.text("🔀 Orchestrator routing query...")
                    progress.progress(20)
                    time.sleep(0.5)

                    # Run the graph
                    graph  = build_graph()
                    result = graph.invoke({"query": query})

                    progress.progress(80)
                    status.text("📝 Aggregating results...")
                    time.sleep(0.5)

                    progress.progress(100)
                    status.text("✅ Analysis complete!")
                    time.sleep(0.3)

                    # Clear progress
                    progress.empty()
                    status.empty()

                    # Show result
                    st.success("Analysis Complete!")
                    st.markdown("---")
                    st.markdown(result["final_output"])

                    # Show which agent was used
                    route = result.get("route", "unknown")
                    st.info(f"🤖 Routed to: **{route}** agent")

                except Exception as e:
                    st.error(f"Error: {str(e)}")


# ── Tab 2: System Info ────────────────────────────────────
with tab2:
    st.subheader("System Architecture")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
### 🤖 AI Agents
- **Orchestrator** — Routes queries via LangGraph
- **Financial Analyst** — P&L, Budget Analysis
- **Sales Scientist** — Trend Detection
- **Investment Strategist** — RAG on Reports
- **Cloud Architect** — Infrastructure Planning

### 🔧 Tech Stack
- **LLM** — Gemini 2.5 Flash
- **Orchestration** — LangGraph
- **RAG** — ChromaDB + HuggingFace
- **Protocol** — MCP
- **Backend** — Python + FastAPI
        """)

    with col2:
        st.markdown("""
### 📊 RAG Pipeline
- PDF Parsing → pypdf
- Chunking → RecursiveCharacterTextSplitter
- Embeddings → all-MiniLM-L6-v2
- Vector Store → ChromaDB
- Retrieval → Cosine Similarity

### 📁 Document Collections
- financial_reports/
- sales_reports/
- investment_reports/
- cloud_docs/
- routing_rules/
        """)

    st.divider()

    # Show collection stats
    st.subheader("📈 Knowledge Base Status")

    try:
        import chromadb
        client = chromadb.PersistentClient(path="./chroma_store")
        cols   = st.columns(5)

        collections = [
            "financial_reports",
            "sales_reports",
            "investment_reports",
            "cloud_docs",
            "routing_rules"
        ]

        for i, name in enumerate(collections):
            with cols[i]:
                try:
                    col  = client.get_collection(name)
                    count = col.count()
                    st.metric(name.replace("_", " ").title(), f"{count} chunks")
                except:
                    st.metric(name.replace("_", " ").title(), "Empty")
    except:
        st.info("ChromaDB not initialized yet. Upload documents first.")

streamlit_app.py
