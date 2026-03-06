"""Log Explorer – Search, filter, and inspect log streams."""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.generator import generate_logs, SERVICES

GREEN = "#00ffaa"; BLUE = "#00d4ff"; RED = "#ff4d6d"; AMBER = "#ffb800"
DARK  = "#020916"

LEVEL_COLOR = {"INFO": BLUE, "WARN": AMBER, "ERROR": RED, "DEBUG": "#94a3b8"}
LEVEL_BADGE = {
    "INFO":  '<span class="badge badge-blue">INFO</span>',
    "WARN":  '<span class="badge badge-yellow">WARN</span>',
    "ERROR": '<span class="badge badge-red">ERROR</span>',
    "DEBUG": '<span class="badge" style="background:rgba(148,163,184,0.1);color:#94a3b8;border:1px solid rgba(148,163,184,0.2)">DEBUG</span>',
}

def _chart_layout():
    return dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono, monospace", color="#94a3b8", size=11),
        margin=dict(l=16, r=16, t=36, b=16),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", showline=False, zeroline=False),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", showline=False, zeroline=False),
        hoverlabel=dict(bgcolor="#0f172a", bordercolor="#334155",
                        font=dict(family="JetBrains Mono")),
    )


def render():
    st.markdown("""
    <div class="page-title">Log Explorer</div>
    <div class="page-subtitle">SEARCH · FILTER · DRILL DOWN INTO LOG STREAMS</div>
    """, unsafe_allow_html=True)

    # ── Filters ─────────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        search = st.text_input("🔍 Search logs", placeholder="keyword, pod name, error code…")
    with col2:
        sel_level = st.multiselect("Level", ["INFO","WARN","ERROR","DEBUG"],
                                   default=["INFO","WARN","ERROR"])
    with col3:
        sel_svc = st.multiselect("Service", SERVICES, default=SERVICES[:4])
    with col4:
        n_rows = st.slider("Max rows", 50, 500, 200, step=50)

    df = generate_logs(500)
    if sel_level:
        df = df[df.level.isin(sel_level)]
    if sel_svc:
        df = df[df.service.isin(sel_svc)]
    if search:
        df = df[df.message.str.contains(search, case=False)]
    df = df.head(n_rows)

    # ── Mini charts ─────────────────────────────────────────────────────────────
    ca, cb = st.columns(2)
    with ca:
        cnt = df.groupby("level").size().reset_index(name="count")
        fig = go.Figure(go.Bar(
            x=cnt["level"], y=cnt["count"],
            marker=dict(
                color=[LEVEL_COLOR.get(l, "#64748b") for l in cnt["level"]],
                line=dict(width=0),
            ),
        ))
        fig.update_layout(**_chart_layout(), title=dict(text="Log Level Distribution",
                          font=dict(color="#e2e8f0",size=12)), height=200)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with cb:
        svc_cnt = df.groupby("service").size().reset_index(name="count").sort_values("count")
        fig2 = go.Figure(go.Bar(
            x=svc_cnt["count"], y=svc_cnt["service"],
            orientation="h",
            marker=dict(color=BLUE, line=dict(width=0)),
        ))
        fig2.update_layout(**_chart_layout(), title=dict(text="Volume by Service",
                           font=dict(color="#e2e8f0",size=12)), height=200)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    # ── Latency distribution ─────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Latency Distribution</div>', unsafe_allow_html=True)
    fig3 = go.Figure()
    for svc in (sel_svc or SERVICES)[:5]:
        sub = df[df.service == svc]["latency_ms"]
        if len(sub) > 2:
            fig3.add_trace(go.Violin(
                y=sub, name=svc, box_visible=True, meanline_visible=True,
                line_color=GREEN, fillcolor="rgba(0,255,170,0.06)",
            ))
    fig3.update_layout(**_chart_layout(),
                       title=dict(text="Request Latency (ms) per Service",
                                  font=dict(color="#e2e8f0",size=12)),
                       height=300)
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    # ── Log table ────────────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Log Stream</div>', unsafe_allow_html=True)
    st.markdown('<div class="log-container">', unsafe_allow_html=True)
    log_html = ""
    for _, row in df.head(60).iterrows():
        ts  = row["timestamp"].strftime("%H:%M:%S.%f")[:-3]
        lvl = row["level"]
        svc = row["service"]
        msg = row["message"]
        score = row["anomaly_score"]
        badge = LEVEL_BADGE.get(lvl, lvl)
        score_color = RED if score > 0.75 else (AMBER if score > 0.5 else "#475569")
        log_html += (
            f'<div style="padding:2px 0;border-bottom:1px solid rgba(255,255,255,0.03)">'
            f'<span class="log-dim">{ts}</span> &nbsp;'
            f'{badge} &nbsp;'
            f'<span style="color:#7c3aed;font-size:0.7rem">{svc}</span> &nbsp;'
            f'<span style="color:#cbd5e1">{msg}</span> &nbsp;'
            f'<span style="color:{score_color};font-size:0.65rem">score:{score}</span>'
            f'</div>'
        )
    st.markdown(log_html + "</div>", unsafe_allow_html=True)
