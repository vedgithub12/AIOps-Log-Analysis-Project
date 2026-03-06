"""Anomaly Detection – ML scores, timeline, SHAP-style feature importance."""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.generator import generate_anomalies, generate_timeseries, SERVICES

GREEN="#00ffaa"; BLUE="#00d4ff"; RED="#ff4d6d"; AMBER="#ffb800"; PURPLE="#a855f7"
DARK="#020916"

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
    <div class="page-title">Anomaly Detection</div>
    <div class="page-subtitle">ML-POWERED ANOMALY SCORES · FEATURE IMPORTANCE · TIMELINE ANALYSIS</div>
    """, unsafe_allow_html=True)

    anoms = generate_anomalies(120)
    ts    = generate_timeseries(48)

    # ── Controls ─────────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        threshold = st.slider("Anomaly Score Threshold", 0.5, 1.0, 0.75, 0.01)
    with col2:
        model_name = st.selectbox("Detection Model",
            ["IsolationForest", "AutoEncoder LSTM", "One-Class SVM", "DBSCAN"])
    with col3:
        time_window = st.selectbox("Time Window", ["Last 1h","Last 6h","Last 24h","Last 48h"],
                                   index=2)

    # KPIs
    triggered = anoms[anoms.score >= threshold]
    ka, kb, kc, kd = st.columns(4)
    for col, (val, lbl, color) in zip([ka,kb,kc,kd], [
        (str(len(triggered)), "Anomalies Detected", RED),
        (f"{len(triggered[triggered.resolved])/max(len(triggered),1)*100:.0f}%", "Resolution Rate", GREEN),
        (f"{triggered['ttd_min'].mean():.1f}m", "Avg TTD", AMBER),
        (f"{triggered['score'].mean():.3f}", "Avg Score", BLUE),
    ]):
        with col:
            st.markdown(f"""
            <div class="metric-card">
              <div class="metric-value" style="color:{color};font-size:1.8rem">{val}</div>
              <div class="metric-label">{lbl}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Anomaly Timeline scatter ─────────────────────────────────────────────────
    st.markdown('<div class="section-header">Anomaly Score Timeline</div>', unsafe_allow_html=True)
    fig = go.Figure()
    # Background log volume
    fig.add_trace(go.Scatter(
        x=ts.index, y=ts["log_volume"] / ts["log_volume"].max(),
        mode="lines", name="Log Volume (norm.)",
        line=dict(color="rgba(255,255,255,0.08)", width=1),
        fill="tozeroy", fillcolor="rgba(255,255,255,0.02)",
        hoverinfo="skip",
    ))
    # Below threshold
    normal = anoms[anoms.score < threshold]
    fig.add_trace(go.Scatter(
        x=normal["timestamp"], y=normal["score"],
        mode="markers", name="Normal",
        marker=dict(size=6, color=GREEN, opacity=0.5,
                    line=dict(width=0)),
    ))
    # Above threshold
    fig.add_trace(go.Scatter(
        x=triggered["timestamp"], y=triggered["score"],
        mode="markers", name="Anomaly",
        text=triggered["type"] + " | " + triggered["service"],
        marker=dict(size=10, color=RED,
                    symbol="diamond",
                    line=dict(color="rgba(255,77,109,0.4)", width=2)),
    ))
    fig.add_hline(y=threshold, line_color=AMBER, line_dash="dash",
                  annotation_text=f"Threshold: {threshold}",
                  annotation_font=dict(color=AMBER, size=10))
    fig.update_layout(**_layout(height=300,
        title=dict(text="Anomaly Scores Over Time", font=dict(color="#e2e8f0",size=13)),
        yaxis_title="Score", showlegend=True,
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
    ))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── Feature importance + Confusion-ish ──────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="section-header">Feature Importance (SHAP)</div>', unsafe_allow_html=True)
        features = ["CPU usage","Memory usage","Log error rate",
                    "Request latency","Kafka lag","Disk I/O","Pod restarts","Auth failures"]
        shap_vals = np.array([0.31, 0.24, 0.18, 0.14, 0.07, 0.03, 0.02, 0.01])
        colors = [RED if v > 0.2 else (AMBER if v > 0.1 else BLUE) for v in shap_vals]
        fig_shap = go.Figure(go.Bar(
            x=shap_vals[::-1], y=features[::-1],
            orientation="h",
            marker=dict(color=colors[::-1], line=dict(width=0)),
            text=[f"{v:.2f}" for v in shap_vals[::-1]],
            textposition="outside",
            textfont=dict(size=10, color="#94a3b8"),
        ))
        fig_shap.update_layout(**_layout(height=300,
            title=dict(text="Feature Contribution to Anomaly Score",
                       font=dict(color="#e2e8f0",size=12))))
        st.plotly_chart(fig_shap, use_container_width=True, config={"displayModeBar": False})

    with col_b:
        st.markdown('<div class="section-header">Anomaly Type Distribution</div>', unsafe_allow_html=True)
        type_cnt = anoms[anoms.score >= threshold]["type"].value_counts().reset_index()
        fig_types = go.Figure(go.Bar(
            x=type_cnt["count"], y=type_cnt["type"],
            orientation="h",
            marker=dict(
                color=type_cnt["count"],
                colorscale=[[0, "#0f172a"],[0.5, AMBER],[1.0, RED]],
                line=dict(width=0),
            ),
        ))
        fig_types.update_layout(**_layout(height=300,
            title=dict(text="Detected Anomaly Types",
                       font=dict(color="#e2e8f0",size=12))))
        st.plotly_chart(fig_types, use_container_width=True, config={"displayModeBar": False})

    # ── Score distribution heatmap ───────────────────────────────────────────────
    st.markdown('<div class="section-header">Score Distribution by Service</div>', unsafe_allow_html=True)
    rng2 = np.random.default_rng(77)
    score_bins = ["0.0-0.2","0.2-0.4","0.4-0.6","0.6-0.75","0.75-0.9","0.9-1.0"]
    heat = rng2.integers(0, 30, size=(len(SERVICES), len(score_bins)))
    fig_heat = go.Figure(go.Heatmap(
        z=heat, x=score_bins, y=SERVICES,
        colorscale=[[0,"#020916"],[0.4,"#0f2d3b"],[0.7,AMBER],[1.0,RED]],
        showscale=True,
        colorbar=dict(thickness=8, tickfont=dict(size=9, color="#64748b")),
        text=heat, texttemplate="%{text}", textfont=dict(size=9),
    ))
    fig_heat.update_layout(**_layout(height=280))
    st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False})

    # ── Active alerts ────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">🔴 Active Unresolved Anomalies</div>', unsafe_allow_html=True)
    active = anoms[(anoms.score >= threshold) & (~anoms.resolved)][
        ["timestamp","type","service","score","severity","ttd_min","ttr_min"]
    ].head(10)
    active["timestamp"] = active["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
    st.dataframe(active, use_container_width=True, height=280)
