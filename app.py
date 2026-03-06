import streamlit as st

st.set_page_config(
    page_title="AIOps Log Analysis",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Syne:wght@700;800&display=swap');

/* Global */
html, body, [class*="css"] {
    font-family: 'JetBrains Mono', monospace !important;
    background-color: #020916;
    color: #e2e8f0;
}

/* Hide default header */
#MainMenu, footer, header { visibility: hidden; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #050f1f 0%, #020916 100%);
    border-right: 1px solid rgba(0,255,170,0.1);
}
[data-testid="stSidebar"] * { color: #94a3b8; }
[data-testid="stSidebar"] .stRadio label { 
    padding: 8px 12px; border-radius: 6px; cursor: pointer;
    transition: all 0.2s;
}
[data-testid="stSidebar"] .stRadio label:hover { 
    background: rgba(0,255,170,0.06); color: #00ffaa;
}

/* Metric cards */
.metric-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(0,255,170,0.15);
    border-radius: 12px;
    padding: 20px 24px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.3s;
}
.metric-card:hover { border-color: rgba(0,255,170,0.4); }
.metric-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #00ffaa, #00d4ff);
}
.metric-value {
    font-family: 'Syne', sans-serif;
    font-size: 2.4rem; font-weight: 800;
    color: #fff; line-height: 1;
}
.metric-label { font-size: 0.7rem; color: #64748b; letter-spacing: 0.12em; text-transform: uppercase; margin-top: 6px; }
.metric-delta { font-size: 0.75rem; margin-top: 8px; }
.delta-up { color: #00ffaa; }
.delta-down { color: #ff4d6d; }
.delta-neutral { color: #ffb800; }

/* Section headers */
.section-header {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem; font-weight: 700;
    color: #fff; letter-spacing: 0.05em;
    border-left: 3px solid #00ffaa;
    padding-left: 12px; margin: 24px 0 16px;
}

/* Log line styles */
.log-container {
    background: #020916;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
    padding: 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    max-height: 320px;
    overflow-y: auto;
    line-height: 1.8;
}
.log-error   { color: #ff4d6d; }
.log-warn    { color: #ffb800; }
.log-info    { color: #00d4ff; }
.log-ok      { color: #00ffaa; }
.log-dim     { color: #475569; }

/* Status badges */
.badge {
    display: inline-block; padding: 2px 10px; border-radius: 20px;
    font-size: 0.65rem; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase;
}
.badge-red    { background: rgba(255,77,109,0.15); color: #ff4d6d; border: 1px solid rgba(255,77,109,0.3); }
.badge-green  { background: rgba(0,255,170,0.1);  color: #00ffaa;  border: 1px solid rgba(0,255,170,0.25); }
.badge-yellow { background: rgba(255,184,0,0.1);  color: #ffb800;  border: 1px solid rgba(255,184,0,0.25); }
.badge-blue   { background: rgba(0,212,255,0.1);  color: #00d4ff;  border: 1px solid rgba(0,212,255,0.25); }

/* Nav logo */
.nav-logo {
    font-family: 'Syne', sans-serif;
    font-size: 1.3rem; font-weight: 800;
    color: #fff; padding: 12px 0 24px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 20px;
}
.nav-logo span { color: #00ffaa; }
.nav-version { font-size: 0.6rem; color: #334155; letter-spacing: 0.1em; display: block; margin-top: 2px; }

/* Page title */
.page-title {
    font-family: 'Syne', sans-serif;
    font-size: 2rem; font-weight: 800;
    color: #fff; margin-bottom: 4px;
}
.page-subtitle { font-size: 0.75rem; color: #475569; letter-spacing: 0.1em; margin-bottom: 28px; }

/* Divider */
hr { border-color: rgba(255,255,255,0.06) !important; }

/* Plotly chart background override */
.js-plotly-plot { border-radius: 10px; }

/* Streamlit overrides */
.stSelectbox > div > div { background: rgba(255,255,255,0.04) !important; border-color: rgba(255,255,255,0.1) !important; }
.stSlider > div { color: #00ffaa; }
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(0,255,170,0.15);
    border-radius: 10px;
    padding: 16px;
}
div[data-testid="stMetricValue"] { color: #fff !important; font-family: 'Syne', sans-serif !important; }
div[data-testid="stMetricDelta"] svg { display: none; }

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.02);
    border-radius: 8px; padding: 4px; gap: 4px;
    border: 1px solid rgba(255,255,255,0.06);
}
.stTabs [data-baseweb="tab"] {
    background: transparent; color: #475569;
    border-radius: 6px; padding: 8px 20px;
    font-size: 0.75rem; letter-spacing: 0.08em;
}
.stTabs [aria-selected="true"] {
    background: rgba(0,255,170,0.1) !important;
    color: #00ffaa !important;
}

button[kind="primary"] {
    background: linear-gradient(135deg,#00ffaa,#00d4ff) !important;
    color: #020916 !important; font-weight: 700 !important;
    border: none !important;
}
</style>
""", unsafe_allow_html=True)

# ── Sidebar Navigation ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="nav-logo">
        <span>AI</span>Ops <span>⬡</span>
        <span class="nav-version">LOG ANALYSIS PLATFORM v2.0</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Navigation**")
    page = st.radio(
        "",
        ["🏠  Dashboard", "📋  Log Explorer", "🔍  Anomaly Detection",
         "📊  Model Analytics", "🌐  Infrastructure 3D", "⚙️  Settings"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("**System Status**")
    st.markdown('<span class="badge badge-green">● LIVE</span> &nbsp; Kafka Connected', unsafe_allow_html=True)
    st.markdown('<span class="badge badge-green">● OK</span> &nbsp; ML Model Loaded', unsafe_allow_html=True)
    st.markdown('<span class="badge badge-yellow">⚠ WARN</span> &nbsp; 3 Active Alerts', unsafe_allow_html=True)
    st.markdown("---")
    st.caption("github.com/vedgithub12/AIOps-Log-Analysis-Project")

# ── Route Pages ────────────────────────────────────────────────────────────────
if "Dashboard" in page:
    from pages import dashboard
    dashboard.render()
elif "Log Explorer" in page:
    from pages import log_explorer
    log_explorer.render()
elif "Anomaly" in page:
    from pages import anomaly_detection
    anomaly_detection.render()
elif "Model Analytics" in page:
    from pages import model_analytics
    model_analytics.render()
elif "Infrastructure 3D" in page:
    from pages import infra_3d
    infra_3d.render()
elif "Settings" in page:
    from pages import settings
    settings.render()
