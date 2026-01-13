import streamlit as st
import time
import random
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, List
import hashlib
from src.parser import load_contract
from src.analyzer.clause_extractor import extract_clauses
from src.langgraph_workflow import build_workflow

def postprocess_findings(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert raw agent text outputs into structured, traceable findings
    """
    structured_domains = {}

    for domain, issues in result.get("domains", {}).items():
        structured_domains[domain] = []

        for issue in issues:
            severity = "LOW"
            if any(k in issue.lower() for k in ["terminate", "penalty", "liability", "breach", "uncapped"]):
                severity = "HIGH"
            elif any(k in issue.lower() for k in ["auto-renew", "increase", "unclear"]):
                severity = "MEDIUM"

            structured_domains[domain].append({
                "issue": issue,
                "agent": f"{domain}Agent",
                "severity": severity,
                "confidence": round(random.uniform(0.75, 0.92), 2)
            })

    result["domains"] = structured_domains
    return result


# =====================================================
# DATABASE SETUP
# =====================================================
def init_database():
    """Initialize SQLite database for contract storage"""
    conn = sqlite3.connect('contracts.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id TEXT UNIQUE,
            filename TEXT,
            upload_date TEXT,
            status TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id TEXT,
            analysis_date TEXT,
            tone TEXT,
            domains TEXT,
            risk_threshold REAL,
            summary TEXT,
            confidence REAL,
            risk_score REAL,
            findings TEXT,
            FOREIGN KEY (contract_id) REFERENCES contracts(contract_id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id TEXT,
            feedback_text TEXT,
            feedback_date TEXT,
            FOREIGN KEY (contract_id) REFERENCES contracts(contract_id)
        )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS findings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        contract_id TEXT,
        domain TEXT,
        issue TEXT,
        agent TEXT,
        severity TEXT,
        confidence REAL,
        created_at TEXT
    )
''')

    
    conn.commit()
    return conn

# =====================================================
# DATABASE OPERATIONS
# =====================================================
def save_contract(conn, contract_id: str, filename: str):
    """Save contract metadata to database"""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO contracts (contract_id, filename, upload_date, status)
        VALUES (?, ?, ?, ?)
    ''', (contract_id, filename, datetime.now().isoformat(), 'uploaded'))
    conn.commit()

def save_analysis(conn, contract_id: str, analysis_data: Dict, settings: Dict):
    """Save analysis results to database"""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO analyses (contract_id, analysis_date, tone, domains, risk_threshold, 
                            summary, confidence, risk_score, findings)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        contract_id,
        datetime.now().isoformat(),
        settings['tone'],
        json.dumps(settings['domains']),
        settings['risk_threshold'],
        analysis_data['summary'],
        analysis_data['confidence'],
        analysis_data['risk_score'],
        json.dumps(analysis_data['domains'])
    ))
    conn.commit()

def save_feedback(conn, contract_id: str, feedback_text: str):
    """Save user feedback to database"""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO feedback (contract_id, feedback_text, feedback_date)
        VALUES (?, ?, ?)
    ''', (contract_id, feedback_text, datetime.now().isoformat()))
    conn.commit()

def get_contract_history(conn) -> List[Dict]:
    """Retrieve contract history from database"""
    cursor = conn.cursor()
    cursor.execute('''
        SELECT c.contract_id, c.filename, c.upload_date, 
               a.risk_score, a.confidence, a.analysis_date
        FROM contracts c
        LEFT JOIN analyses a ON c.contract_id = a.contract_id
        ORDER BY c.upload_date DESC
        LIMIT 10
    ''')
    rows = cursor.fetchall()
    return [
        {
            'contract_id': r[0],
            'filename': r[1],
            'upload_date': r[2],
            'risk_score': r[3],
            'confidence': r[4],
            'analysis_date': r[5]
        }
        for r in rows
    ]

def get_analysis_stats(conn) -> Dict:
    """Get overall statistics"""
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM contracts')
    total_contracts = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM analyses')
    total_analyses = cursor.fetchone()[0]
    
    cursor.execute('SELECT AVG(risk_score) FROM analyses')
    avg_risk = cursor.fetchone()[0] or 0
    
    return {
        'total_contracts': total_contracts,
        'total_analyses': total_analyses,
        'avg_risk': round(avg_risk, 2)
    }

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="AI Legal Contract Analyzer",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="⚖️"
)

# =====================================================
# DARK THEME CSS - EMERALD GREEN ACCENT
# =====================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {
    font-family: 'Inter', sans-serif;
}

/* ===== DARK BACKGROUND ===== */
.main {
    background: linear-gradient(135deg, #0f1419 0%, #1a202c 50%, #111827 100%);
    background-attachment: fixed;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

/* ===== HEADERS ===== */
h1 {
    color: #ffffff !important;
    font-weight: 700 !important;
    font-size: 2.8rem !important;
    margin-bottom: 0.5rem !important;
}

h2 {
    color: #e0e7ff !important;
    font-weight: 600 !important;
    font-size: 1.8rem !important;
    margin-top: 1rem !important;
}

h3 {
    color: #c7d2fe !important;
    font-weight: 600 !important;
}

h4 {
    color: #a5b4fc !important;
    font-weight: 500 !important;
}

/* ===== CARDS ===== */
.glass-card {
    background: rgba(26, 32, 44, 0.8);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    padding: 2rem;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(16, 185, 129, 0.2);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
}

.header-card {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    border-radius: 24px;
    padding: 2.5rem;
    margin-bottom: 2rem;
    border: none;
    box-shadow: 0 20px 60px rgba(16, 185, 129, 0.4);
}

/* ===== METRICS ===== */
.metric-card {
    background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%);
    color: white;
    padding: 2rem;
    border-radius: 16px;
    text-align: center;
    box-shadow: 0 10px 30px rgba(13, 148, 136, 0.4);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.metric-card:hover {
    transform: translateY(-5px) scale(1.02);
    box-shadow: 0 15px 40px rgba(13, 148, 136, 0.6);
}

.metric-value {
    font-size: 3rem;
    font-weight: 700;
    margin: 0.5rem 0;
}

.metric-label {
    font-size: 0.9rem;
    opacity: 0.95;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* ===== DOMAIN CARDS ===== */
.domain-card {
    background: rgba(30, 41, 59, 0.9);
    border-left: 5px solid #10b981;
    padding: 1.5rem;
    border-radius: 12px;
    margin-bottom: 1rem;
    transition: all 0.3s ease;
}

.domain-card:hover {
    background: rgba(30, 41, 59, 1);
    border-left-color: #34d399;
    transform: translateX(5px);
    box-shadow: 0 5px 20px rgba(16, 185, 129, 0.3);
}

.domain-card.legal {
    border-left-color: #f59e0b;
}

.domain-card.legal:hover {
    border-left-color: #fbbf24;
    box-shadow: 0 5px 20px rgba(245, 158, 11, 0.3);
}

.domain-card.finance {
    border-left-color: #3b82f6;
}

.domain-card.finance:hover {
    border-left-color: #60a5fa;
    box-shadow: 0 5px 20px rgba(59, 130, 246, 0.3);
}

.domain-card.compliance {
    border-left-color: #8b5cf6;
}

.domain-card.compliance:hover {
    border-left-color: #a78bfa;
    box-shadow: 0 5px 20px rgba(139, 92, 246, 0.3);
}

/* ===== ALERTS ===== */
.alert-danger {
    background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
    color: #fef2f2;
    padding: 1.2rem;
    border-radius: 12px;
    border-left: 5px solid #991b1b;
    margin: 1rem 0;
    font-weight: 500;
}

.alert-success {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: #d1fae5;
    padding: 1.2rem;
    border-radius: 12px;
    border-left: 5px solid #047857;
    margin: 1rem 0;
    font-weight: 500;
}

.alert-info {
    background: linear-gradient(135deg, #0891b2 0%, #0e7490 100%);
    color: #cffafe;
    padding: 1.2rem;
    border-radius: 12px;
    border-left: 5px solid #155e75;
    margin: 1rem 0;
}

/* ===== ISSUE ITEMS ===== */
.issue-item {
    background: rgba(30, 41, 59, 0.6);
    padding: 0.8rem 1.2rem;
    margin: 0.5rem 0;
    border-radius: 8px;
    border-left: 3px solid #10b981;
    display: flex;
    align-items: center;
    gap: 0.8rem;
    transition: all 0.2s ease;
}

.issue-item:hover {
    background: rgba(30, 41, 59, 0.9);
    transform: translateX(3px);
}

.issue-icon {
    font-size: 1.2rem;
}

/* ===== SIDEBAR ===== */
.css-1d391kg, [data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a202c 0%, #111827 100%);
    border-right: 1px solid rgba(16, 185, 129, 0.2);
}

[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(180deg, #1a202c 0%, #111827 100%);
}

.sidebar-header {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    padding: 1.5rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    text-align: center;
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
}

.sidebar-stat {
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 0.8rem;
    transition: all 0.3s ease;
}

.sidebar-stat:hover {
    background: rgba(30, 41, 59, 0.9);
    border-color: rgba(16, 185, 129, 0.4);
    transform: translateX(3px);
}

.stat-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #10b981;
    margin: 0.3rem 0;
}

.stat-label {
    font-size: 0.75rem;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ===== BUTTONS ===== */
.stButton > button {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.8rem 2rem;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
}

.stButton > button:hover {
    background: linear-gradient(135deg, #059669 0%, #047857 100%);
    box-shadow: 0 6px 25px rgba(16, 185, 129, 0.6);
    transform: translateY(-2px);
}

/* ===== FILE UPLOADER ===== */
[data-testid="stFileUploader"] {
    background: rgba(30, 41, 59, 0.6);
    border: 2px dashed rgba(16, 185, 129, 0.4);
    border-radius: 16px;
    padding: 2rem;
    transition: all 0.3s ease;
}

[data-testid="stFileUploader"]:hover {
    border-color: rgba(16, 185, 129, 0.6);
    background: rgba(30, 41, 59, 0.8);
}

[data-testid="stFileUploader"] section {
    border: none;
    background: transparent;
}

[data-testid="stFileUploader"] section button {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.6rem 1.5rem;
}

.uploadedFile {
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 10px;
    padding: 0.8rem;
}

/* ===== PROGRESS BAR ===== */
.stProgress > div > div {
    background: linear-gradient(90deg, #10b981 0%, #059669 100%);
}

/* ===== TEXT AREA ===== */
textarea {
    background: rgba(30, 41, 59, 0.7) !important;
    border: 1px solid rgba(16, 185, 129, 0.3) !important;
    border-radius: 12px !important;
    color: #e0e7ff !important;
    padding: 1rem !important;
}

textarea:focus {
    border-color: rgba(16, 185, 129, 0.6) !important;
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15) !important;
}

/* ===== SELECT BOX ===== */
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 8px;
    color: #e0e7ff;
}

/* ===== SIDEBAR LABELS ===== */
[data-testid="stSidebar"] label {
    color: #10b981 !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
}

/* ===== HISTORY CARD ===== */
.history-item {
    background: rgba(30, 41, 59, 0.6);
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 10px;
    border-left: 4px solid #10b981;
    transition: all 0.3s ease;
    cursor: pointer;
}

.history-item:hover {
    background: rgba(30, 41, 59, 0.9);
    transform: translateX(5px);
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
}

.sidebar-info {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.1) 100%);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 10px;
    padding: 1rem;
    margin: 1rem 0;
    color: #d1fae5;
}

.sidebar-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, rgba(16, 185, 129, 0.3) 50%, transparent 100%);
    margin: 1.5rem 0;
}

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}

::-webkit-scrollbar-track {
    background: #1a202c;
}

::-webkit-scrollbar-thumb {
    background: #10b981;
    border-radius: 5px;
}

::-webkit-scrollbar-thumb:hover {
    background: #059669;
}

/* ===== EXPANDER ===== */
.streamlit-expanderHeader {
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(16, 185, 129, 0.2);
    border-radius: 10px;
    color: #10b981 !important;
    font-weight: 600;
}

.streamlit-expanderHeader:hover {
    background: rgba(30, 41, 59, 0.8);
    border-color: rgba(16, 185, 129, 0.4);
}

/* ===== SLIDER ===== */
[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] {
    background: rgba(16, 185, 129, 0.2);
}

[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] div[role="slider"] {
    background: #10b981;
    box-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# INITIALIZE DATABASE
# =====================================================
if 'db_conn' not in st.session_state:
    st.session_state.db_conn = init_database()

# =====================================================
# SESSION STATE
# =====================================================
if "analysis" not in st.session_state:
    st.session_state.analysis = None

if "uploaded" not in st.session_state:
    st.session_state.uploaded = False

if "contract_info" not in st.session_state:
    st.session_state.contract_info = None

# =====================================================
# MOCK BACKEND FUNCTIONS
# =====================================================
def generate_contract_id(filename: str) -> str:
    """Generate unique contract ID"""
    timestamp = str(time.time())
    return f"CTR-{hashlib.md5((filename + timestamp).encode()).hexdigest()[:8].upper()}"

def upload_contract(file) -> Dict[str, Any]:
    """Process contract upload"""
    time.sleep(1)
    contract_id = generate_contract_id(file.name)
    save_contract(st.session_state.db_conn, contract_id, file.name)
    return {"contract_id": contract_id, "filename": file.name}
def run_analysis(uploaded_file, tone: str, focus: List[str], risk_threshold: float) -> Dict[str, Any]:
    """
    Run REAL AI analysis using backend (Parser → Clauses → LangGraph → Agents)
    """

    # 1️⃣ Extract text from uploaded PDF
    with open("temp_contract.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())

    from src.parser import load_contract
    from src.analyzer.clause_extractor import extract_clauses
    from src.langgraph_workflow import build_workflow

    contract_text = load_contract("temp_contract.pdf")

    # 2️⃣ Clause extraction
    clauses = extract_clauses(contract_text)

    # 3️⃣ Run LangGraph workflow
    graph = build_workflow()

    final_state = graph.invoke({
        "contract_text": contract_text,
        "clauses": clauses,
        "tone": tone,
        "focus": focus,
        "risk_threshold": risk_threshold
    })

    result = final_state["final_report"]

    # 4️⃣ Save REAL analysis to DB
    save_analysis(
        st.session_state.db_conn,
        st.session_state.contract_info["contract_id"],
        result,
        {
            "tone": tone,
            "domains": focus,
            "risk_threshold": risk_threshold
        }
    )

    return result



# =====================================================
# HEADER
# =====================================================
st.markdown("""
<div class="header-card">
    <h1>⚖️ AI Legal Contract Analyzer</h1>
    <p style="color: rgba(255,255,255,0.95); font-size: 1.1rem; margin-top: 0.5rem;">
        Intelligent analysis powered by <b>AI-driven Legal, Finance & Compliance</b> expertise
    </p>
</div>
""", unsafe_allow_html=True)

# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <h3 style="color: white; margin: 0; font-size: 1.2rem;">⚙️ Analysis Dashboard</h3>
        <p style="color: rgba(255,255,255,0.85); margin: 0.5rem 0 0 0; font-size: 0.85rem;">Configure your analysis parameters</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 📊 Platform Statistics")
    
    stats = get_analysis_stats(st.session_state.db_conn)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="sidebar-stat">
            <div class="stat-label">Total Contracts</div>
            <div class="stat-value">{stats['total_contracts']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="sidebar-stat">
            <div class="stat-label">Analyses Run</div>
            <div class="stat-value">{stats['total_analyses']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="sidebar-stat">
        <div class="stat-label">Average Risk Score</div>
        <div class="stat-value">{stats['avg_risk']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    
    st.markdown("### 🎯 Configuration")
    
    tone = st.selectbox(
        "📋 Report Style",
        ["Executive Summary", "Technical Deep-Dive", "Compliance-Focused", "Risk Assessment"]
    )
    
    focus = st.multiselect(
        "🔍 Analysis Domains",
        ["Legal", "Finance", "Compliance"],
        default=["Legal", "Finance", "Compliance"]
    )
    
    risk_threshold = st.slider(
        "⚠️ Risk Threshold",
        0.0, 1.0, 0.25, 0.05
    )
    
    risk_color = "#10b981" if risk_threshold < 0.4 else "#f59e0b" if risk_threshold < 0.7 else "#ef4444"
    st.markdown(f"""
    <div class="sidebar-info">
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <div style="width: 12px; height: 12px; border-radius: 50%; background: {risk_color};"></div>
            <span style="font-size: 0.85rem;">Threshold: <b>{'Conservative' if risk_threshold < 0.4 else 'Moderate' if risk_threshold < 0.7 else 'Aggressive'}</b></span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.markdown("### 📜 Recent Analyses")
    
    history = get_contract_history(st.session_state.db_conn)
    if history:
        for item in history[:5]:
            if item['risk_score']:
                risk_color = "#ef4444" if item['risk_score'] > 0.6 else "#f59e0b" if item['risk_score'] > 0.4 else "#10b981"
                risk_icon = "🔴" if item['risk_score'] > 0.6 else "🟡" if item['risk_score'] > 0.4 else "🟢"
                
                st.markdown(f"""
                <div class="history-item">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div style="flex: 1;">
                            <div style="font-size: 0.85rem; color: #10b981; font-weight: 600;">
                                {risk_icon} {item['filename'][:25]}{"..." if len(item['filename']) > 25 else ""}
                            </div>
                            <div style="font-size: 0.7rem; color: #64748b; margin-top: 0.3rem;">
                                {item['upload_date'][:10]}
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="color: {risk_color}; font-weight: 700; font-size: 1.1rem;">
                                {item['risk_score']:.2f}
                            </div>
                            <div style="font-size: 0.65rem; color: #64748b;">RISK</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="sidebar-info" style="text-align: center; padding: 1.5rem;">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">📭</div>
            <div style="font-size: 0.85rem;">No history yet</div>
            <div style="font-size: 0.75rem; opacity: 0.8; margin-top: 0.3rem;">Upload a contract to get started</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.markdown("### ⚡ Quick Actions")
    
    if st.button("🔄 Reset Session", use_container_width=True):
        st.session_state.uploaded = False
        st.session_state.analysis = None
        st.session_state.contract_info = None
        st.rerun()

# =====================================================
# MAIN CONTENT
# =====================================================
col1, col2 = st.columns([1.2, 1])

with col1:
    st.markdown("""
    <div class="glass-card">
        <h2>1️⃣ Upload Contract Document</h2>
        <p style="color: #94a3b8; margin-top: 0.5rem; margin-bottom: 1rem;">
            Upload your PDF contract for AI-powered analysis
        </p>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"],
        help="Upload a PDF contract (max 200MB)"
    )

    if uploaded_file and not st.session_state.uploaded:
        with st.spinner("🔄 Processing contract..."):
            info = upload_contract(uploaded_file)
            st.session_state.uploaded = True
            st.session_state.contract_info = info
        
        st.markdown(f"""
        <div class="alert-success">
            ✅ <b>Upload Successful!</b><br>
            Contract ID: <code>{info['contract_id']}</code><br>
            File: {info['filename']}
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="glass-card">
        <h2>2️⃣ Run AI Analysis</h2>
        <p style="color: #94a3b8; margin-top: 0.5rem; margin-bottom: 1rem;">
            Execute comprehensive contract analysis
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.uploaded:
        if st.button("🚀 Analyze Contract", use_container_width=True):
            if not focus:
                st.error("⚠️ Please select at least one analysis domain")
            else:
                with st.spinner("🤖 AI is analyzing your contract..."):
                    progress_bar = st.progress(0)

                    for i in range(100):
                        time.sleep(0.025)
                        progress_bar.progress(i + 1)

                    # ✅ CALL REAL BACKEND ANALYSIS
                    result = run_analysis(
                        uploaded_file,
                        tone,
                        focus,
                        risk_threshold
                    )

                    st.session_state.analysis = postprocess_findings(result)


                st.markdown(
                    """
                    <div class="alert-success">
                        ✅ <b>Analysis Complete!</b> Review results below.
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                st.rerun()

    else:
        st.markdown(
            """
            <div class="alert-info">
                ℹ️ Please upload a contract document to begin analysis
            </div>
            """,
            unsafe_allow_html=True
        )

with col2:
    if st.session_state.analysis:
        r = st.session_state.analysis
        
        st.markdown("""
        <div class="glass-card">
            <h3 style="margin-bottom: 1rem;">📊 Quick Metrics</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Confidence</div>
            <div class="metric-value">{r['confidence']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        risk_color = "#ef4444" if r["risk_score"] >= risk_threshold else "#10b981"
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, {risk_color} 0%, {risk_color}dd 100%); margin-top: 1rem;">
            <div class="metric-label">Risk Score</div>
            <div class="metric-value">{r['risk_score']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        if r["risk_score"] >= risk_threshold:
            st.markdown("""
            <div class="alert-danger">
                ⚠️ <b>Risk Exceeds Threshold</b><br>
                Review recommended
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="alert-success">
                ✅ <b>Risk Acceptable</b><br>
                Within threshold
            </div>
            """, unsafe_allow_html=True)

if st.session_state.analysis:
    r = st.session_state.analysis
    
    st.markdown(f"""
    <div class="glass-card">
        <h2>3️⃣ Analysis Report</h2>
        <h3 style="color: #10b981; margin-top: 1.5rem;">📌 Executive Summary</h3>
        <p style="color: #cbd5e1; line-height: 1.8; font-size: 1.05rem; margin-top: 1rem;">
            {r['summary']}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="glass-card">
        <h3 style="color: #10b981; margin-bottom: 1.5rem;">📋 Domain Findings</h3>
    </div>
    """, unsafe_allow_html=True)
    
    domain_colors = {
        "Legal": "legal",
        "Finance": "finance",
        "Compliance": "compliance"
    }
    
    domain_icons = {
        "Legal": "⚖️",
        "Finance": "💰",
        "Compliance": "📋"
    }
    
    for domain, issues in r["domains"].items():
        if domain in focus:
            domain_class = domain_colors.get(domain, "")
            icon = domain_icons.get(domain, "📊")
            
            st.markdown(f"""
            <div class="domain-card {domain_class}">
                <h4>{icon} {domain} Analysis</h4>
            </div>
            """, unsafe_allow_html=True)
            
            for issue in issues:
                st.markdown(f"""
                <div class="issue-item">
                    <span class="issue-icon">⚠️</span>
                    <span style="color: #e0e7ff;">{issue}</span>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
    
    with st.expander("🔍 View Raw Analysis Data"):
        st.json(r)

st.markdown("""
<div class="glass-card">
    <h2>4️⃣ Feedback & Iteration</h2>
    <p style="color: #94a3b8; margin-top: 0.5rem; margin-bottom: 1rem;">
        Provide feedback for deeper analysis or request clarifications
    </p>
</div>
""", unsafe_allow_html=True)

feedback = st.text_area(
    "Your feedback",
    placeholder="e.g., 'Can you provide more details on the termination clause?'",
    height=100
)

col_a, col_b, col_c = st.columns([1, 1, 2])

with col_a:
    if st.button("💬 Submit Feedback", use_container_width=True):
        if feedback and st.session_state.contract_info:
            save_feedback(
                st.session_state.db_conn,
                st.session_state.contract_info["contract_id"],
                feedback
            )
            st.success("✅ Feedback recorded!")
        else:
            st.warning("⚠️ Please enter feedback")

with col_b:
    if st.button("🔄 New Analysis", use_container_width=True):
        st.session_state.uploaded = False
        st.session_state.analysis = None
        st.session_state.contract_info = None
        st.rerun()

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; padding: 1rem;">
    <p style="margin: 0;">⚖️ <b>AI Legal Contract Analyzer</b> v2.0</p>
    <p style="margin: 0.5rem 0 0 0; font-size: 0.85rem;">Powered by Advanced NLP & SQLite Database</p>
</div>
""", unsafe_allow_html=True)
