
import streamlit as st
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from rag.pipeline import build_collection, COLLECTIONS
from orchestrator.orchestrator_agent import build_graph

load_dotenv()

# ── Page Config ───────────────────────────────────────────
st.set_page_config(
    page_title="FinPilot AI",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@400;500&display=swap');

/* ── Root Variables ── */
:root {
    --gold:        #C9A84C;
    --gold-light:  #E8C97A;
    --gold-dim:    #7A6230;
    --bg-deep:     #080C10;
    --bg-card:     #0D1117;
    --bg-panel:    #111820;
    --bg-hover:    #161E28;
    --border:      rgba(201,168,76,0.15);
    --border-bright: rgba(201,168,76,0.4);
    --text-primary: #F0EAD6;
    --text-muted:  #7A8899;
    --text-dim:    #3D4F61;
    --green:       #2ECC71;
    --blue:        #3498DB;
    --red:         #E74C3C;
}

/* ── Global Reset ── */
html, body, .stApp {
    background-color: var(--bg-deep) !important;
    font-family: 'DM Sans', sans-serif;
    color: var(--text-primary);
}

/* ── Hide Streamlit Default Elements ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg-deep); }
::-webkit-scrollbar-thumb { background: var(--gold-dim); border-radius: 2px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--bg-card) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text-primary) !important; }

/* ── Sidebar Header ── */
.sidebar-logo {
    text-align: center;
    padding: 1.5rem 0 1rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.5rem;
}
.sidebar-logo h1 {
    font-family: 'Playfair Display', serif;
    font-size: 1.6rem;
    color: var(--gold) !important;
    margin: 0;
    letter-spacing: 0.05em;
}
.sidebar-logo p {
    font-size: 0.7rem;
    color: var(--text-muted) !important;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin: 0.3rem 0 0;
}

/* ── Collection Badge ── */
.collection-badge {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0.5rem 0.75rem;
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 6px;
    margin-bottom: 0.5rem;
    font-size: 0.8rem;
    color: var(--text-muted) !important;
}

/* ── Main Header ── */
.main-header {
    background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-panel) 100%);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
}
.main-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--gold), transparent);
}
.main-header::after {
    content: '◆';
    position: absolute;
    right: 2rem;
    top: 50%;
    transform: translateY(-50%);
    font-size: 4rem;
    color: rgba(201,168,76,0.06);
    font-family: 'Playfair Display', serif;
}
.main-header h1 {
    font-family: 'Playfair Display', serif;
    font-size: 2.2rem;
    color: var(--gold) !important;
    margin: 0 0 0.4rem;
    letter-spacing: 0.03em;
}
.main-header p {
    color: var(--text-muted);
    font-size: 0.85rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin: 0;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--bg-card) !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0;
    padding: 0;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-muted) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    padding: 0.8rem 1.5rem !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    transition: all 0.2s;
}
.stTabs [aria-selected="true"] {
    color: var(--gold) !important;
    border-bottom: 2px solid var(--gold) !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] {
    background: transparent !important;
    padding: 1.5rem 0 !important;
}

/* ── Query Card ── */
.query-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}
.query-card-title {
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    color: var(--gold-dim);
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 1rem;
}

/* ── Sample Query Buttons ── */
.stButton > button {
    background: var(--bg-panel) !important;
    color: var(--text-muted) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.78rem !important;
    font-weight: 400 !important;
    padding: 0.4rem 0.8rem !important;
    transition: all 0.2s !important;
    white-space: nowrap !important;
}
.stButton > button:hover {
    background: var(--bg-hover) !important;
    border-color: var(--border-bright) !important;
    color: var(--gold-light) !important;
}

/* ── Primary Run Button ── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #8B6914, var(--gold)) !important;
    color: var(--bg-deep) !important;
    border: none !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    padding: 0.7rem 1.5rem !important;
    border-radius: 6px !important;
    box-shadow: 0 4px 20px rgba(201,168,76,0.2) !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 4px 30px rgba(201,168,76,0.4) !important;
    transform: translateY(-1px) !important;
}

/* ── Text Area ── */
.stTextArea textarea {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    padding: 0.8rem 1rem !important;
    transition: border-color 0.2s !important;
}
.stTextArea textarea:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 2px rgba(201,168,76,0.1) !important;
}
.stTextArea label {
    color: var(--text-muted) !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}

/* ── File Uploader ── */
[data-testid="stFileUploader"] {
    background: var(--bg-panel) !important;
    border: 1px dashed var(--border-bright) !important;
    border-radius: 8px !important;
    padding: 0.5rem !important;
}
[data-testid="stFileUploader"] label {
    color: var(--text-muted) !important;
    font-size: 0.75rem !important;
}

/* ── Success / Info / Warning ── */
.stSuccess {
    background: rgba(46,204,113,0.08) !important;
    border: 1px solid rgba(46,204,113,0.2) !important;
    border-radius: 8px !important;
    color: var(--green) !important;
}
.stInfo {
    background: rgba(52,152,219,0.08) !important;
    border: 1px solid rgba(52,152,219,0.2) !important;
    border-radius: 8px !important;
}
.stWarning {
    background: rgba(201,168,76,0.08) !important;
    border: 1px solid rgba(201,168,76,0.2) !important;
    border-radius: 8px !important;
}
.stError {
    background: rgba(231,76,60,0.08) !important;
    border: 1px solid rgba(231,76,60,0.2) !important;
    border-radius: 8px !important;
}

/* ── Result Output ── */
.result-wrapper {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 2rem;
    margin-top: 1rem;
    position: relative;
}
.result-wrapper::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--gold), transparent);
}
.result-wrapper h2, .result-wrapper h3 {
    font-family: 'Playfair Display', serif !important;
    color: var(--gold-light) !important;
}
.result-wrapper p, .result-wrapper li {
    color: var(--text-primary) !important;
    line-height: 1.8 !important;
}
.result-wrapper strong {
    color: var(--gold-light) !important;
}

/* ── Agent Route Badge ── */
.route-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(201,168,76,0.08);
    border: 1px solid var(--border-bright);
    border-radius: 20px;
    padding: 0.35rem 1rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    color: var(--gold);
    margin-top: 1.5rem;
}
.route-dot {
    width: 6px; height: 6px;
    background: var(--gold);
    border-radius: 50%;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    padding: 1rem !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.65rem !important;
    color: var(--text-muted) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.15em !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Playfair Display', serif !important;
    color: var(--gold) !important;
    font-size: 1.4rem !important;
}

/* ── Divider ── */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 1.5rem 0 !important;
}

/* ── Subheaders ── */
h2, h3 {
    font-family: 'Playfair Display', serif !important;
    color: var(--text-primary) !important;
}
h2 { font-size: 1.4rem !important; }
h3 { font-size: 1.1rem !important; }

/* ── Progress Bar ── */
.stProgress > div > div {
    background: linear-gradient(90deg, var(--gold-dim), var(--gold)) !important;
    border-radius: 4px !important;
}
.stProgress > div {
    background: var(--bg-panel) !important;
    border-radius: 4px !important;
}

/* ── Spinner ── */
.stSpinner > div {
    border-color: var(--gold) transparent transparent transparent !important;
}

/* ── Architecture Cards ── */
.arch-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.5rem;
    height: 100%;
}
.arch-card-title {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: var(--gold-dim);
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
}
.arch-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0.4rem 0;
    font-size: 0.82rem;
    color: var(--text-muted);
    border-bottom: 1px solid rgba(255,255,255,0.03);
}
.arch-item-dot {
    width: 4px; height: 4px;
    background: var(--gold-dim);
    border-radius: 50%;
    flex-shrink: 0;
}
.arch-item strong {
    color: var(--text-primary);
}

/* ── Sidebar Sections ── */
.sidebar-section-title {
    font-family: 'DM Mono', monospace;
    font-size: 0.6rem;
    color: var(--gold-dim);
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin: 1rem 0 0.5rem;
}

/* ── Status indicator ── */
.status-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.4rem 0;
    font-size: 0.78rem;
    border-bottom: 1px solid rgba(255,255,255,0.03);
}
.status-online {
    color: var(--green);
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
}
</style>
""", unsafe_allow_html=True)


# ── Main Header ───────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>FinPilot AI</h1>
    <p>Multi-Agent Financial Intelligence System &nbsp;·&nbsp; LLM + RAG + LangGraph</p>
</div>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <h1>💹 FinPilot</h1>
        <p>Knowledge Base</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section-title">Upload Documents</div>', unsafe_allow_html=True)

    collection_labels = {
        "financial_reports":  ("📊", "Financial Reports"),
        "sales_reports":      ("📈", "Sales Reports"),
        "investment_reports": ("💰", "Investment Reports"),
        "cloud_docs":         ("☁️", "Cloud Documents"),
    }

    uploaded_any = False
    collections_to_rebuild = []
    import pandas as pd

    for collection, (icon, label) in collection_labels.items():
        with st.expander(f"{icon} {label}"):
            # Financial & Sales allow both PDF and CSV
            if collection in ["financial_reports", "sales_reports"]:
                file_types = ["pdf", "csv"]
                accept_label = "Drop files here (PDF or CSV)"
            else:
                file_types = ["pdf"]
                accept_label = "Drop PDF files here"
            
            uploaded_files = st.file_uploader(
                accept_label,
                type=file_types,
                accept_multiple_files=True,
                key=collection,
                label_visibility="collapsed"
            )
            
            if uploaded_files:
                folder = COLLECTIONS[collection]
                os.makedirs(folder, exist_ok=True)
                
                has_pdf = False
                for uploaded_file in uploaded_files:
                    # Handle CSV files
                    if uploaded_file.name.endswith(".csv"):
                        try:
                            df = pd.read_csv(uploaded_file)
                            if collection == "financial_reports":
                                st.session_state.financial_csv = df
                            elif collection == "sales_reports":
                                st.session_state.sales_csv = df
                            st.caption(f"✓ {uploaded_file.name}: {df.shape[0]} rows × {df.shape[1]} columns")
                        except Exception as e:
                            st.error(f"Error reading {uploaded_file.name}: {str(e)}")
                    else:
                        # Handle PDF files
                        save_path = os.path.join(folder, uploaded_file.name)
                        with open(save_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        st.caption(f"✓ {uploaded_file.name} saved")
                        has_pdf = True
                
                # Track collections with new PDFs to rebuild embeddings
                if has_pdf and collection not in collections_to_rebuild:
                    collections_to_rebuild.append(collection)
                
                uploaded_any = True
            
            # Show CSV status if loaded
            if collection == "financial_reports" and "financial_csv" in st.session_state:
                df = st.session_state.financial_csv
                st.caption(f"📋 CSV data ready ({df.shape[0]}R × {df.shape[1]}C)")
                with st.expander("Preview Financial Data"):
                    st.dataframe(df.head(5), use_container_width=True)
                
                with st.expander("Map Columns", expanded=False):
                    col_options = ["-- Skip --"] + list(df.columns)
                    c1, c2 = st.columns(2)
                    with c1:
                        fin_revenue = st.selectbox("Revenue column:", col_options, key="fin_revenue_col")
                        fin_cogs = st.selectbox("COGS/Cost column:", col_options, key="fin_cogs_col")
                    with c2:
                        fin_expenses = st.selectbox("Expenses column:", col_options, key="fin_expenses_col")
                    
                    mapping = {}
                    if fin_revenue != "-- Skip --":
                        mapping["revenue"] = fin_revenue
                    if fin_cogs != "-- Skip --":
                        mapping["cogs"] = fin_cogs
                    if fin_expenses != "-- Skip --":
                        mapping["expenses"] = fin_expenses
                    
                    if mapping:
                        st.session_state.financial_column_mapping = mapping
                        st.caption(f"✓ Mapping: {mapping}")
                    
            elif collection == "sales_reports" and "sales_csv" in st.session_state:
                df = st.session_state.sales_csv
                st.caption(f"📋 CSV data ready ({df.shape[0]}R × {df.shape[1]}C)")
                with st.expander("Preview Sales Data"):
                    st.dataframe(df.head(5), use_container_width=True)
                
                with st.expander("Map Columns", expanded=False):
                    col_options = ["-- Skip --"] + list(df.columns)
                    sales_col = st.selectbox("Sales/Revenue column:", col_options, key="sales_col")
                    
                    if sales_col != "-- Skip --":
                        st.session_state.sales_column_mapping = {"sales": sales_col}
                        st.caption(f"✓ Mapping: sales → {sales_col}")

    # ── Build Embeddings for New PDFs ──────────────────────────
    if collections_to_rebuild:
        st.markdown("---")
        st.markdown('<div class="sidebar-section-title">Building Embeddings</div>', unsafe_allow_html=True)

        with st.spinner("🔄 Creating embeddings for uploaded documents..."):
            for collection in collections_to_rebuild:
                try:
                    build_collection(collection)
                    st.info(f"✓ {collection}: embeddings created")
                except Exception as e:
                    st.error(f"✗ {collection}: {str(e)}")

    # ── Always ensure routing rules collection exists on disk (persistent) 
    try:
        routing_folder = COLLECTIONS.get("routing_rules")
        if routing_folder and os.path.isdir(routing_folder):
            pdf_files = [f for f in os.listdir(routing_folder) if f.lower().endswith('.pdf')]
            if pdf_files:
                build_collection("routing_rules")
    except Exception as e:
        st.warning(f"Routing rules embedding check failed: {str(e)}")

    st.markdown("---")

    # System Status
    st.markdown('<div class="sidebar-section-title">System Status</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="status-row"><span>Gemini 2.5 Flash</span><span class="status-online">● ONLINE</span></div>
    <div class="status-row"><span>LangGraph</span><span class="status-online">● ACTIVE</span></div>
    <div class="status-row"><span>ChromaDB</span><span class="status-online">● READY</span></div>
    <div class="status-row"><span>MCP Server</span><span class="status-online">● READY</span></div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption("FinPilot AI · v1.0 · LLM+RAG Project")


# ── Main Tabs ─────────────────────────────────────────────
tab1, tab2 = st.tabs(["◈  INTELLIGENCE QUERY", "◈  SYSTEM ARCHITECTURE"])


# ── Tab 1: Query ──────────────────────────────────────────
with tab1:

    # Sample Query Buttons
    st.markdown('<p style="font-family:\'DM Mono\',monospace;font-size:0.65rem;color:#7A6230;letter-spacing:0.2em;text-transform:uppercase;margin-bottom:0.8rem;">Quick Queries</p>', unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)
    sample_query = ""

    with col1:
        if st.button("📊 Financial Analysis"):
            sample_query = "Analyse our Q3 financial performance"
    with col2:
        if st.button("📈 Sales Trends"):
            sample_query = "What are our sales trends this year?"
    with col3:
        if st.button("💰 Investment Strategy"):
            sample_query = "What investment strategy is recommended?"
    with col4:
        if st.button("☁️ Cloud Infrastructure"):
            sample_query = "Recommend cloud infrastructure for scaling"
    with col5:
        if st.button("🔍 Complete Analysis"):
            sample_query = "Give complete analysis of our business performance and suggest expansion strategy"

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # Query Input
    query = st.text_area(
        "ENTER YOUR QUERY",
        value=sample_query,
        height=120,
        placeholder="e.g. Analyze our financial performance and suggest strategic investment opportunities based on consultant reports...",
    )

    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        run_clicked = st.button("⚡ RUN ANALYSIS", type="primary", use_container_width=True)

    if run_clicked:
        if not query.strip():
            st.warning("Please enter a query to analyse.")
        else:
            # ── Validate query has content ──
            if not query or not str(query).strip():
                st.warning("Please enter a query to analyze.")
            else:
                query = str(query).strip()  # Clean whitespace only
                progress = st.progress(0)
                status   = st.empty()

                status.markdown('<p style="color:#C9A84C;font-family:\'DM Mono\',monospace;font-size:0.8rem;">⟳ &nbsp;Orchestrator routing query...</p>', unsafe_allow_html=True)
                progress.progress(15)
                time.sleep(0.4)

                status.markdown('<p style="color:#C9A84C;font-family:\'DM Mono\',monospace;font-size:0.8rem;">⟳ &nbsp;Agents processing...</p>', unsafe_allow_html=True)
                progress.progress(40)

                try:
                    graph  = build_graph()
                    input_data = {"query": query}
                    if "financial_csv" in st.session_state:
                        input_data["financial_csv"] = st.session_state.financial_csv
                    if "sales_csv" in st.session_state:
                        input_data["sales_csv"] = st.session_state.sales_csv
                    if "financial_column_mapping" in st.session_state:
                        input_data["financial_column_mapping"] = st.session_state.financial_column_mapping
                    if "sales_column_mapping" in st.session_state:
                        input_data["sales_column_mapping"] = st.session_state.sales_column_mapping
                    result = graph.invoke(input_data)

                    progress.progress(85)
                    status.markdown('<p style="color:#C9A84C;font-family:\'DM Mono\',monospace;font-size:0.8rem;">⟳ &nbsp;Aggregating intelligence...</p>', unsafe_allow_html=True)
                    time.sleep(0.3)

                    progress.progress(100)
                    time.sleep(0.2)
                    progress.empty()
                    status.empty()

                    # ── Result Display ──
                    st.markdown("""
                    <div style="display:flex;align-items:center;gap:10px;margin:1.5rem 0 1rem;">
                        <div style="height:1px;flex:1;background:linear-gradient(90deg,transparent,rgba(201,168,76,0.3));"></div>
                        <span style="font-family:'DM Mono',monospace;font-size:0.65rem;color:#7A6230;letter-spacing:0.2em;">INTELLIGENCE REPORT</span>
                        <div style="height:1px;flex:1;background:linear-gradient(90deg,rgba(201,168,76,0.3),transparent);"></div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f'<div class="result-wrapper">{result["final_output"]}</div>', unsafe_allow_html=True)

                    # Agent route badge
                    routes = result.get("routes", [result.get("route", "unknown")])
                    if isinstance(routes, list):
                        agents_str = " · ".join([r.upper() for r in routes])
                    else:
                        agents_str = str(routes).upper()

                    st.markdown(f"""
                    <div class="route-badge">
                        <div class="route-dot"></div>
                        ROUTED → {agents_str}
                    </div>
                    """, unsafe_allow_html=True)

                except Exception as e:
                    progress.empty()
                    status.empty()
                    st.error(f"**Analysis Error:** {str(e)}")


# ── Tab 2: System Architecture ────────────────────────────
with tab2:

    # Architecture Grid
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="arch-card">
            <div class="arch-card-title">AI Agents</div>
            <div class="arch-item"><div class="arch-item-dot"></div><div><strong>Orchestrator</strong> — LangGraph routing</div></div>
            <div class="arch-item"><div class="arch-item-dot"></div><div><strong>Financial Analyst</strong> — P&L, Budget</div></div>
            <div class="arch-item"><div class="arch-item-dot"></div><div><strong>Sales Scientist</strong> — Trends, Patterns</div></div>
            <div class="arch-item"><div class="arch-item-dot"></div><div><strong>Investment Strategist</strong> — RAG Reports</div></div>
            <div class="arch-item"><div class="arch-item-dot"></div><div><strong>Cloud Architect</strong> — Infrastructure</div></div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="arch-card">
            <div class="arch-card-title">Technology Stack</div>
            <div class="arch-item"><div class="arch-item-dot"></div><div><strong>LLM</strong> — Gemini 2.5 Flash</div></div>
            <div class="arch-item"><div class="arch-item-dot"></div><div><strong>Orchestration</strong> — LangGraph</div></div>
            <div class="arch-item"><div class="arch-item-dot"></div><div><strong>Embeddings</strong> — all-MiniLM-L6-v2</div></div>
            <div class="arch-item"><div class="arch-item-dot"></div><div><strong>Vector DB</strong> — ChromaDB</div></div>
            <div class="arch-item"><div class="arch-item-dot"></div><div><strong>Protocol</strong> — MCP</div></div>
            <div class="arch-item"><div class="arch-item-dot"></div><div><strong>Backend</strong> — Python + FastAPI</div></div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="arch-card">
            <div class="arch-card-title">RAG Pipeline</div>
            <div class="arch-item"><div class="arch-item-dot"></div><div><strong>PDF Parsing</strong> — pypdf</div></div>
            <div class="arch-item"><div class="arch-item-dot"></div><div><strong>Chunking</strong> — Recursive Splitter</div></div>
            <div class="arch-item"><div class="arch-item-dot"></div><div><strong>Embeddings</strong> — HuggingFace</div></div>
            <div class="arch-item"><div class="arch-item-dot"></div><div><strong>Retrieval</strong> — Cosine Similarity</div></div>
            <div class="arch-item"><div class="arch-item-dot"></div><div><strong>Collections</strong> — 5 Specialized</div></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    # Knowledge Base Status
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem;">
        <div style="height:1px;flex:1;background:linear-gradient(90deg,transparent,rgba(201,168,76,0.3));"></div>
        <span style="font-family:'DM Mono',monospace;font-size:0.65rem;color:#7A6230;letter-spacing:0.2em;">KNOWLEDGE BASE STATUS</span>
        <div style="height:1px;flex:1;background:linear-gradient(90deg,rgba(201,168,76,0.3),transparent);"></div>
    </div>
    """, unsafe_allow_html=True)

    try:
        import chromadb
        from chromadb.config import Settings

        chroma_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chroma_store")
        CHROMA_PERSISTENT = os.getenv("CHROMA_PERSISTENT", "0") in ["1", "true", "True"]

        if not CHROMA_PERSISTENT and not os.path.exists(chroma_path):
            # In-memory mode does not require a folder; just show existing memory metrics (may be 0 until update).
            pass

        if CHROMA_PERSISTENT and not os.path.exists(chroma_path):
            st.warning("chroma_store/ not found. Upload documents via sidebar first or set CHROMA_PERSISTENT=0.")

        client = chromadb.Client(settings=Settings(anonymized_telemetry=False)) if not CHROMA_PERSISTENT else chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )
        metric_cols = st.columns(6)
        collections = [
            "financial_reports",
            "sales_reports",
            "investment_reports",
            "cloud_docs"
        ]
        for i, name in enumerate(collections):
            with metric_cols[i]:
                try:
                    col   = client.get_collection(name)
                    count = col.count()
                    label = name.replace("_", " ").title()
                    st.metric(label, f"{count}", delta="chunks indexed")
                except Exception:
                    label = name.replace("_", " ").title()
                    st.metric(label, "—", delta="empty")
    except Exception as e:
        st.error(f"ChromaDB error: {str(e)}")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # Document Collections
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem;">
        <div style="height:1px;flex:1;background:linear-gradient(90deg,transparent,rgba(201,168,76,0.3));"></div>
        <span style="font-family:'DM Mono',monospace;font-size:0.65rem;color:#7A6230;letter-spacing:0.2em;">DOCUMENT COLLECTIONS</span>
        <div style="height:1px;flex:1;background:linear-gradient(90deg,rgba(201,168,76,0.3),transparent);"></div>
    </div>
    """, unsafe_allow_html=True)

    doc_cols = st.columns(5)
    doc_collections = [
        ("📊", "financial_reports/", "Financial Analyst Agent"),
        ("📈", "sales_reports/", "Sales Agent"),
        ("💰", "investment_reports/", "Investment Strategist"),
        ("☁️", "cloud_docs/", "Cloud Architect Agent"),
    ]
    for i, (icon, folder, agent) in enumerate(doc_collections):
        with doc_cols[i]:
            st.markdown(f"""
            <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:8px;padding:0.8rem;text-align:center;">
                <div style="font-size:1.4rem;margin-bottom:0.4rem;">{icon}</div>
                <div style="font-family:'DM Mono',monospace;font-size:0.6rem;color:#C9A84C;margin-bottom:0.3rem;">{folder}</div>
                <div style="font-size:0.65rem;color:#3D4F61;">{agent}</div>
            </div>
            """, unsafe_allow_html=True)