
import streamlit as st
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from rag.pipeline import build_collection, COLLECTIONS
from rag.session_store import clear_session
from orchestrator.orchestrator_agent import build_graph
from orchestrator.chatbot import process_chat_question
import shutil

load_dotenv()

# ── Session Upload Folder (Temporary) ─────────────────────
TEMP_UPLOADS_ROOT = "temp_uploads"
os.makedirs(TEMP_UPLOADS_ROOT, exist_ok=True)

# ── Page Config ───────────────────────────────────────────
st.set_page_config(
    page_title="FinPilot AI",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Session Management ─────────────────────────────────────
if "session_initialized" not in st.session_state:
    st.session_state.session_initialized = False
    st.session_state.uploaded_collections = {}
    st.session_state.session_id = str(int(time.time() * 1000))  # Unique session ID
    st.session_state.chat_history = []  # Chat message history for chatbot

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

    # ── Session Management Section ──
    st.markdown("---")
    st.markdown(
        '<div class="sidebar-section-title">Session</div>',
        unsafe_allow_html=True
    )
    
    if st.button(
        "🔄 New Session / Clear Data",
        use_container_width=True
    ):
        # Clear ChromaDB session collections
        clear_session()
        
        # Clear temp uploads for this session
        session_temp_folder = os.path.join(TEMP_UPLOADS_ROOT, st.session_state.session_id)
        if os.path.exists(session_temp_folder):
            shutil.rmtree(session_temp_folder)
            print(f"[Streamlit] Cleaned up: {session_temp_folder}")
        
        # Reset session state
        st.session_state.session_initialized = False
        st.session_state.uploaded_collections = {}
        st.session_state.session_id = str(int(time.time() * 1000))  # New session ID
        st.success("✓ Session cleared! Fresh start.")
        st.rerun()

    # Show uploaded files in current session
    if st.session_state.uploaded_collections:
        st.markdown(
            '<div style="font-size:0.7rem;'
            'color:#7A8899;margin-top:0.5rem;">'
            'Current session data:</div>',
            unsafe_allow_html=True
        )
        for col, files in st.session_state.uploaded_collections.items():
            for f in files:
                st.markdown(
                    f'<div style="font-size:0.65rem;'
                    f'color:#C9A84C;">📄 {f}</div>',
                    unsafe_allow_html=True
                )

    st.markdown("---")
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
                # Create session-specific temp folder for user uploads (NOT docs/)
                temp_collection_folder = os.path.join(TEMP_UPLOADS_ROOT, st.session_state.session_id, collection)
                os.makedirs(temp_collection_folder, exist_ok=True)
                
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
                        # Handle PDF files - Save to TEMP folder, NOT docs/
                        save_path = os.path.join(temp_collection_folder, uploaded_file.name)
                        with open(save_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        st.caption(f"✓ {uploaded_file.name} saved (session-only)")
                        has_pdf = True
                        
                        # Track in session state (user collections only)
                        if collection not in st.session_state.uploaded_collections:
                            st.session_state.uploaded_collections[collection] = []
                        if uploaded_file.name not in st.session_state.uploaded_collections[collection]:
                            st.session_state.uploaded_collections[collection].append(uploaded_file.name)
                
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

    # ── Build Embeddings for New PDFs & System Collections ──────────────────────────
    if collections_to_rebuild:
        st.markdown("---")
        st.markdown('<div class="sidebar-section-title">Building User Collections</div>', unsafe_allow_html=True)

        with st.spinner("🔄 Creating embeddings for user documents..."):
            for collection in collections_to_rebuild:
                try:
                    # Pass session_id to use temp_uploads folder
                    build_collection(collection, session_id=st.session_state.session_id)
                    st.info(f"✓ {collection}: embeddings created (user session)")
                except Exception as e:
                    error_str = str(e).lower()
                    if "already exists" in error_str or "ephemeral" in error_str:
                        st.info(f"✓ {collection}: collection ready")
                    else:
                        st.error(f"✗ {collection}: {str(e)}")

    # ── Build System Collections Only ONCE per App Start ──────────────────────────
    # Routing rules = permanent, disk-based. Build once, use forever.
    try:
        routing_folder = COLLECTIONS.get("routing_rules")
        if routing_folder and os.path.isdir(routing_folder):
            pdf_files = [f for f in os.listdir(routing_folder) if f.lower().endswith('.pdf')]
            if pdf_files and not st.session_state.session_initialized:
                with st.spinner("⚡ Initializing system collections (one-time)..."):
                    try:
                        build_collection("routing_rules")
                        st.info("✓ Routing rules: persistent embeddings ready")
                        st.session_state.session_initialized = True
                    except Exception as build_err:
                        if "already exists" in str(build_err).lower():
                            st.info("✓ Routing rules: already initialized")
                            st.session_state.session_initialized = True
                        else:
                            st.error(f"Build error: {str(build_err)}")
    except Exception as e:
        st.warning(f"System collection setup failed: {str(e)}")




# ── Main Content ──────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:1.5rem;">
    <div style="height:1px;flex:1;background:linear-gradient(90deg,transparent,rgba(201,168,76,0.3));"></div>
    <span style="font-family:'DM Mono',monospace;font-size:0.65rem;color:#7A6230;letter-spacing:0.2em;">AI-POWERED ANALYSIS ASSISTANT</span>
    <div style="height:1px;flex:1;background:linear-gradient(90deg,rgba(201,168,76,0.3),transparent);"></div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
**Ask questions about your business data.** Our AI will:
- Analyze your financial, sales, and investment documents
- Provide detailed insights tailored to your questions
- Support follow-up conversations for deeper analysis
""")

st.markdown("---")

# Chat message display area
chat_container = st.container()

# Display chat history
with chat_container:
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"""
            <div style="display:flex;justify-content:flex-end;margin-bottom:0.5rem;">
                <div style="background:rgba(201,168,76,0.15);border:1px solid rgba(201,168,76,0.3);border-radius:8px;padding:0.8rem 1rem;max-width:70%;text-align:right;">
                    <span style="font-family:'DM Mono',monospace;font-size:0.65rem;color:#7A6230;letter-spacing:0.1em;text-transform:uppercase;">YOU</span>
                    <p style="margin:0.3rem 0 0;">{msg['content']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            agents_badge = f"<span style='font-family:\"DM Mono\",monospace;font-size:0.6rem;color:#7A6230;letter-spacing:0.1em;'>{msg.get('agents_used', 'AGENTS')}</span>"
            st.markdown(f"""
            <div style="display:flex;justify-content:flex-start;margin-bottom:1rem;">
                <div style="background:rgba(13,17,23,0.8);border:1px solid rgba(201,168,76,0.2);border-radius:8px;padding:1rem;max-width:85%;">
                    <div style="margin-bottom:0.5rem;font-size:0.75rem;color:#C9A84C;">{agents_badge}</div>
                    <p style="margin:0;color:#F0EAD6;line-height:1.6;">{msg['content']}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Display visualizations if available
            if msg.get("visualizations"):
                for agent, fig in msg["visualizations"].items():
                    with st.expander(f"📊 {agent.title()} Chart", expanded=True):
                        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Input area
col_input, col_send = st.columns([5, 1])

with col_input:
    user_question = st.text_input(
        "Ask a question about your data...",
        placeholder="e.g., What are our sales trends? Show me revenue breakdown. How profitable are we?",
        label_visibility="collapsed"
    )

with col_send:
    send_button = st.button("🚀 Send", use_container_width=True, type="primary")

# Process user question
if send_button and user_question.strip():
    user_question = user_question.strip()
    
    # Add user message to history
    st.session_state.chat_history.append({
        "role": "user",
        "content": user_question
    })
    
    # Show loading state
    with st.spinner("🔄 Processing your question..."):
        try:
            # Get previous agents for context (from last assistant message)
            previous_agents = None
            for msg in reversed(st.session_state.chat_history):
                if msg["role"] == "assistant" and msg.get("agents"):
                    previous_agents = msg["agents"]
                    break
            
            # Process the question using chatbot orchestrator
            result = process_chat_question(
                question=user_question,
                financial_csv=st.session_state.get("financial_csv"),
                sales_csv=st.session_state.get("sales_csv"),
                financial_column_mapping=st.session_state.get("financial_column_mapping"),
                sales_column_mapping=st.session_state.get("sales_column_mapping"),
                previous_agents=previous_agents,
            )
            
            # Add assistant response to history
            assistant_msg = {
                "role": "assistant",
                "content": result["final_answer"],
                "agents_used": result["agents_summary"],
                "agents": result["agents"]
            }
            
            # Add visualizations if any
            if result.get("visualization_data"):
                assistant_msg["visualizations"] = result["visualization_data"]
            
            st.session_state.chat_history.append(assistant_msg)
            
            # Rerun to display new messages
            st.rerun()
            
        except Exception as e:
            error_msg = f"❌ Error processing question: {str(e)}"
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": error_msg,
                "agents_used": "ERROR"
            })
            st.rerun()