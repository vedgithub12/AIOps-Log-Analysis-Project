"""Model Analytics – Training curves, confusion matrix, ROC, precision-recall."""
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.generator import generate_model_metrics

GREEN="#00ffaa"; BLUE="#00d4ff"; RED="#ff4d6d"; AMBER="#ffb800"; PURPLE="#a855f7"

def _layout(**kw):
    d = dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono, monospace", color="#94a3b8", size=11),
        margin=dict(l=16, r=16, t=44, b=16),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", showline=False, zeroline=False),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", showline=False, zeroline=False),
        hoverlabel=dict(bgcolor="#0f172a", bordercolor="#334155",
                        font=dict(family="JetBrains Mono")),
    )
    d.update(kw)
    return d


def render():
    st.markdown("""
    <div class="page-title">Model Analytics</div>
    <div class="page-subtitle">TRAINING METRICS · CONFUSION MATRIX · ROC · PRECISION-RECALL</div>
    """, unsafe_allow_html=True)

    metrics = generate_model_metrics()
    rng = np.random.default_rng(55)

    # ── Model selection ──────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    with c1:
        model = st.selectbox("Model", ["IsolationForest","AutoEncoder LSTM","One-Class SVM"])
    with c2:
        st.markdown('<div style="margin-top:28px"><span class="badge badge-green">● Deployed</span></div>',
                    unsafe_allow_html=True)
    with c3:
        st.markdown('<div style="margin-top:24px;font-size:0.75rem;color:#64748b">Last trained: 2h ago · v2.1.4</div>',
                    unsafe_allow_html=True)

    # ── Performance KPIs ─────────────────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    for col, (val, lbl, color) in zip([k1,k2,k3,k4,k5], [
        ("98.1%","Accuracy",GREEN),("0.973","F1 Score",GREEN),
        ("0.971","Precision",BLUE),("0.975","Recall",BLUE),
        ("0.994","AUC-ROC",AMBER),
    ]):
        with col:
            st.markdown(f"""
            <div class="metric-card">
              <div class="metric-value" style="color:{color};font-size:1.7rem">{val}</div>
              <div class="metric-label">{lbl}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Training curves ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Training & Validation Loss</div>', unsafe_allow_html=True)
    fig_loss = go.Figure()
    fig_loss.add_trace(go.Scatter(
        x=metrics["epoch"], y=metrics["train_loss"],
        mode="lines", name="Train Loss",
        line=dict(color=BLUE, width=2),
        fill="tozeroy", fillcolor="rgba(0,212,255,0.05)",
    ))
    fig_loss.add_trace(go.Scatter(
        x=metrics["epoch"], y=metrics["val_loss"],
        mode="lines", name="Val Loss",
        line=dict(color=RED, width=2, dash="dot"),
    ))
    fig_loss.update_layout(**_layout(height=250,
        title=dict(text="Loss Curves", font=dict(color="#e2e8f0",size=12)),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    ))
    st.plotly_chart(fig_loss, use_container_width=True, config={"displayModeBar": False})

    # ── F1 / Precision / Recall ──────────────────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="section-header">Metrics Over Epochs</div>', unsafe_allow_html=True)
        fig_met = go.Figure()
        for col_name, color, name in [
            ("precision", BLUE, "Precision"),
            ("recall", GREEN, "Recall"),
            ("f1", AMBER, "F1"),
        ]:
            fig_met.add_trace(go.Scatter(
                x=metrics["epoch"], y=metrics[col_name],
                mode="lines", name=name,
                line=dict(color=color, width=2),
            ))
        fig_met.update_layout(**_layout(height=280,
            title=dict(text="Precision / Recall / F1", font=dict(color="#e2e8f0",size=12)),
            yaxis_range=[0, 1.05],
            legend=dict(bgcolor="rgba(0,0,0,0)"),
        ))
        st.plotly_chart(fig_met, use_container_width=True, config={"displayModeBar": False})

    with col_b:
        st.markdown('<div class="section-header">Confusion Matrix</div>', unsafe_allow_html=True)
        cm = np.array([[1840, 37], [28, 1095]])
        labels = ["Normal","Anomaly"]
        fig_cm = go.Figure(go.Heatmap(
            z=cm, x=labels, y=labels,
            colorscale=[[0,"#020916"],[0.5,"#1e3a5f"],[1.0,GREEN]],
            showscale=False,
            text=cm, texttemplate="<b>%{text}</b>",
            textfont=dict(size=22, color="#fff"),
        ))
        fig_cm.update_layout(**_layout(height=280,
            title=dict(text="Confusion Matrix (Test Set)", font=dict(color="#e2e8f0",size=12)),
            xaxis_title="Predicted", yaxis_title="Actual",
        ))
        st.plotly_chart(fig_cm, use_container_width=True, config={"displayModeBar": False})

    # ── ROC curve ────────────────────────────────────────────────────────────────
    col_c, col_d = st.columns(2)

    with col_c:
        st.markdown('<div class="section-header">ROC Curve (AUC = 0.994)</div>', unsafe_allow_html=True)
        fpr = np.sort(rng.uniform(0, 1, 100))
        tpr = np.clip(fpr + rng.uniform(0.1, 0.4, 100), 0, 1)
        tpr[0] = 0; tpr[-1] = 1; fpr[-1] = 1
        fig_roc = go.Figure()
        fig_roc.add_trace(go.Scatter(
            x=[0,1], y=[0,1], mode="lines",
            line=dict(color="rgba(255,255,255,0.15)", dash="dash"),
            showlegend=False,
        ))
        fig_roc.add_trace(go.Scatter(
            x=fpr, y=tpr, mode="lines", name="ROC",
            line=dict(color=GREEN, width=2),
            fill="tozeroy", fillcolor="rgba(0,255,170,0.06)",
        ))
        fig_roc.update_layout(**_layout(height=280,
            title=dict(text="Receiver Operating Characteristic", font=dict(color="#e2e8f0",size=12)),
            xaxis_title="FPR", yaxis_title="TPR",
        ))
        st.plotly_chart(fig_roc, use_container_width=True, config={"displayModeBar": False})

    with col_d:
        st.markdown('<div class="section-header">Precision-Recall Curve</div>', unsafe_allow_html=True)
        recall_pts  = np.linspace(0, 1, 100)
        precision_pts = np.clip(1 - 0.5 * recall_pts ** 1.5 + rng.normal(0, 0.02, 100), 0, 1)
        fig_pr = go.Figure()
        fig_pr.add_trace(go.Scatter(
            x=recall_pts, y=precision_pts, mode="lines",
            line=dict(color=AMBER, width=2),
            fill="tozeroy", fillcolor="rgba(255,184,0,0.05)",
        ))
        fig_pr.add_annotation(x=0.5, y=0.85,
            text=f"AP = 0.981", showarrow=False,
            font=dict(color=AMBER, size=12, family="JetBrains Mono"),
            bgcolor="rgba(255,184,0,0.1)", bordercolor=AMBER, borderwidth=1,
        )
        fig_pr.update_layout(**_layout(height=280,
            title=dict(text="Precision-Recall Curve", font=dict(color="#e2e8f0",size=12)),
            xaxis_title="Recall", yaxis_title="Precision",
        ))
        st.plotly_chart(fig_pr, use_container_width=True, config={"displayModeBar": False})

    # ── Model comparison radar ────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Model Comparison Radar</div>', unsafe_allow_html=True)
    cats = ["Precision","Recall","F1","Speed","Scalability","Interpretability"]
    models_data = {
        "IsolationForest": [0.971, 0.975, 0.973, 0.95, 0.90, 0.80],
        "AutoEncoder LSTM": [0.982, 0.968, 0.975, 0.60, 0.75, 0.55],
        "One-Class SVM":   [0.940, 0.920, 0.930, 0.70, 0.60, 0.70],
    }
    colors_r = [GREEN, BLUE, AMBER]
    fig_radar = go.Figure()
    for (mname, vals), color in zip(models_data.items(), colors_r):
        fig_radar.add_trace(go.Scatterpolar(
            r=vals + [vals[0]],
            theta=cats + [cats[0]],
            mode="lines+markers",
            name=mname,
            line=dict(color=color, width=2),
            fill="toself",
            fillcolor=color.replace("#","rgba(") + ",0.06)" if "#" in color else color,
        ))
    fig_radar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0,1],
                            gridcolor="rgba(255,255,255,0.08)",
                            tickfont=dict(size=9, color="#475569")),
            angularaxis=dict(gridcolor="rgba(255,255,255,0.08)",
                             tickfont=dict(color="#94a3b8", size=11)),
        ),
        font=dict(family="JetBrains Mono", color="#94a3b8"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        height=380,
        margin=dict(l=40, r=40, t=40, b=40),
        hoverlabel=dict(bgcolor="#0f172a", bordercolor="#334155",
                        font=dict(family="JetBrains Mono")),
    )
    st.plotly_chart(fig_radar, use_container_width=True, config={"displayModeBar": False})
