"""Settings – Configuration page."""
import streamlit as st

GREEN="#00ffaa"; BLUE="#00d4ff"; RED="#ff4d6d"; AMBER="#ffb800"

def render():
    st.markdown("""
    <div class="page-title">Settings</div>
    <div class="page-subtitle">PIPELINE CONFIG · MODEL PARAMS · ALERT RULES · INTEGRATIONS</div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Pipeline", "Model Parameters", "Integrations"])

    with tab1:
        st.markdown('<div class="section-header">Log Ingestion Pipeline</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.text_input("Kafka Bootstrap Servers", "localhost:9092")
            st.text_input("Kafka Topic", "app-logs")
            st.number_input("Batch Size (events)", value=512, min_value=64, step=64)
            st.number_input("Consumer Poll Interval (ms)", value=500, min_value=100)
        with c2:
            st.text_input("Elasticsearch Host", "http://localhost:9200")
            st.text_input("Index Pattern", "logs-*")
            st.number_input("Retention Days", value=30, min_value=1)
            st.selectbox("Log Level Filter", ["DEBUG","INFO","WARN","ERROR"], index=1)

        st.markdown('<div class="section-header">Alert Rules</div>', unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        with c3:
            st.slider("Anomaly Score Alert Threshold", 0.5, 1.0, 0.75, 0.01)
            st.slider("Error Rate Alert (%)", 0.0, 20.0, 5.0, 0.5)
            st.number_input("Min Anomaly Duration (sec)", value=30)
        with c4:
            st.multiselect("Alert Channels", ["Slack","PagerDuty","Email","Webhook"],
                           default=["Slack","PagerDuty"])
            st.text_input("Slack Webhook URL", "https://hooks.slack.com/…")
            st.checkbox("Auto-remediation enabled", True)

    with tab2:
        st.markdown('<div class="section-header">Isolation Forest</div>', unsafe_allow_html=True)
        c5, c6 = st.columns(2)
        with c5:
            st.number_input("n_estimators", value=200, min_value=50)
            st.number_input("max_samples", value=256, min_value=64)
            st.slider("contamination", 0.01, 0.20, 0.05, 0.01)
        with c6:
            st.selectbox("Feature Scaler", ["StandardScaler","MinMaxScaler","RobustScaler"])
            st.number_input("Retrain every N hours", value=6, min_value=1)
            st.checkbox("Enable drift detection", True)

        st.markdown('<div class="section-header">AutoEncoder LSTM</div>', unsafe_allow_html=True)
        c7, c8 = st.columns(2)
        with c7:
            st.number_input("Sequence Length", value=32, min_value=8)
            st.number_input("Hidden Units", value=128, min_value=32)
            st.number_input("Epochs", value=50, min_value=5)
        with c8:
            st.number_input("Batch Size", value=64, min_value=16)
            st.number_input("Learning Rate (×10⁻⁴)", value=3, min_value=1)
            st.selectbox("Optimizer", ["Adam","AdamW","RMSprop"])

    with tab3:
        st.markdown('<div class="section-header">Connected Integrations</div>', unsafe_allow_html=True)
        integrations = [
            ("Kafka", "Running", GREEN),
            ("Elasticsearch", "Running", GREEN),
            ("Grafana", "Running", GREEN),
            ("Prometheus", "Running", GREEN),
            ("PagerDuty", "Connected", GREEN),
            ("Slack", "Connected", GREEN),
            ("Kubernetes", "Warning", AMBER),
            ("S3 Backup", "Disconnected", RED),
        ]
        cols = st.columns(4)
        for i, (name, status, color) in enumerate(integrations):
            with cols[i % 4]:
                st.markdown(f"""
                <div class="metric-card" style="margin-bottom:12px">
                  <div style="font-size:0.85rem;color:#e2e8f0;font-weight:700">{name}</div>
                  <div style="margin-top:8px">
                    <span style="color:{color};font-size:0.7rem">● {status}</span>
                  </div>
                </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c_save, c_reset, _ = st.columns([1,1,4])
    with c_save:
        if st.button("💾 Save Configuration", type="primary"):
            st.success("Configuration saved!")
    with c_reset:
        if st.button("↺ Reset to Defaults"):
            st.warning("Reset to defaults.")
