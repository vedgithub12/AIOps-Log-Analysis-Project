"""Log Explorer – Search real system_logs.txt data."""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.generator import generate_logs, SERVICES

GREEN="#00ffaa"; BLUE="#00d4ff"; RED="#ff4d6d"; AMBER="#ffb800"
LEVEL_COLOR = {"INFO":BLUE,"WARN":AMBER,"WARNING":AMBER,"ERROR":RED,"DEBUG":"#94a3b8","CRITICAL":"#ff0055"}
LEVEL_BADGE = {
    "INFO":     '<span class="badge badge-blue">INFO</span>',
    "WARNING":  '<span class="badge badge-yellow">WARN</span>',
    "WARN":     '<span class="badge badge-yellow">WARN</span>',
    "ERROR":    '<span class="badge badge-red">ERROR</span>',
    "CRITICAL": '<span class="badge badge-red" style="background:rgba(255,0,85,0.15);color:#ff0055;border-color:rgba(255,0,85,0.3)">CRIT</span>',
    "DEBUG":    '<span class="badge" style="background:rgba(148,163,184,0.1);color:#94a3b8;border:1px solid rgba(148,163,184,0.2)">DEBUG</span>',
}

def _layout(**kw):
    d = dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono, monospace", color="#94a3b8", size=11),
        margin=dict(l=16,r=16,t=36,b=16),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)",showline=False,zeroline=False),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)",showline=False,zeroline=False),
        hoverlabel=dict(bgcolor="#0f172a",bordercolor="#334155",font=dict(family="JetBrains Mono")),
    ); d.update(kw); return d


def render():
    st.markdown("""
    <div class="page-title">Log Explorer</div>
    <div class="page-subtitle">SEARCH · FILTER · DRILL DOWN · 1,000 REAL EVENTS LOADED</div>
    """, unsafe_allow_html=True)

    df_all = generate_logs(1000)

    col1,col2,col3,col4 = st.columns([2,1,1,1])
    with col1: search = st.text_input("🔍 Search logs", placeholder="e.g. Database, Brute force, CPU…")
    with col2: sel_level = st.multiselect("Level",
                   ["INFO","WARNING","ERROR","CRITICAL"],
                   default=["WARNING","ERROR","CRITICAL"])
    with col3: sel_svc = st.multiselect("Service", SERVICES, default=SERVICES)
    with col4: n_rows = st.slider("Max rows", 50, 1000, 200, step=50)

    df = df_all.copy()
    if sel_level: df = df[df["level"].isin(sel_level)]
    if sel_svc:   df = df[df["service"].isin(sel_svc)]
    if search:    df = df[df["message"].str.contains(search, case=False)]
    df = df.head(n_rows)

    # Stats row
    s1,s2,s3,s4 = st.columns(4)
    for col,(val,lbl,c) in zip([s1,s2,s3,s4],[
        (len(df),              "Matching Events", "#e2e8f0"),
        (len(df[df.level=="ERROR"]),   "Errors",  RED),
        (len(df[df.level=="CRITICAL"]),"Criticals","#ff0055"),
        (len(df[df.level=="WARNING"]), "Warnings", AMBER),
    ]):
        with col:
            st.markdown(f"""<div class="metric-card">
              <div class="metric-value" style="color:{c};font-size:1.6rem">{val}</div>
              <div class="metric-label">{lbl}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    ca,cb = st.columns(2)
    with ca:
        cnt = df.groupby("level").size().reset_index(name="count")
        fig = go.Figure(go.Bar(
            x=cnt["level"], y=cnt["count"],
            marker=dict(color=[LEVEL_COLOR.get(l,"#64748b") for l in cnt["level"]],
                        line=dict(width=0)),
            text=cnt["count"], textposition="outside",
            textfont=dict(size=10,color="#94a3b8"),
        ))
        fig.update_layout(**_layout(height=200,
            title=dict(text="Log Level Distribution (Filtered)",
                       font=dict(color="#e2e8f0",size=12))))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

    with cb:
        svc_cnt = df.groupby("service").size().reset_index(name="count").sort_values("count")
        fig2 = go.Figure(go.Bar(
            x=svc_cnt["count"], y=svc_cnt["service"], orientation="h",
            marker=dict(color=BLUE,line=dict(width=0)),
        ))
        fig2.update_layout(**_layout(height=200,
            title=dict(text="Volume by Service",font=dict(color="#e2e8f0",size=12))))
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})

    # Anomaly score distribution
    st.markdown('<div class="section-header">Anomaly Score Distribution</div>',
                unsafe_allow_html=True)
    fig3 = go.Figure()
    for lvl, color in [("INFO",BLUE),("WARNING",AMBER),("ERROR",RED),("CRITICAL","#ff0055")]:
        sub = df[df["level"]==lvl]["anomaly_score"]
        if len(sub)>1:
            fig3.add_trace(go.Histogram(
                x=sub, name=lvl, nbinsx=20, opacity=0.7,
                marker=dict(color=color,line=dict(width=0)),
            ))
    fig3.update_layout(**_layout(height=220,barmode="overlay",
        title=dict(text="Score Distribution by Log Level",font=dict(color="#e2e8f0",size=12)),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    ))
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar":False})

    # Live log stream
    st.markdown('<div class="section-header">Log Stream</div>', unsafe_allow_html=True)
    st.markdown('<div class="log-container">', unsafe_allow_html=True)
    log_html = ""
    for _, row in df.head(80).iterrows():
        ts_str = row["timestamp"].strftime("%H:%M:%S")
        lvl    = row["level"]
        svc    = row["service"]
        msg    = row["message"]
        score  = row["anomaly_score"]
        badge  = LEVEL_BADGE.get(lvl, lvl)
        sc_col = "#ff0055" if score>0.85 else (RED if score>0.75 else (AMBER if score>0.5 else "#475569"))
        log_html += (
            f'<div style="padding:3px 0;border-bottom:1px solid rgba(255,255,255,0.03)">'
            f'<span class="log-dim">{ts_str}</span> &nbsp;'
            f'{badge} &nbsp;'
            f'<span style="color:#7c3aed;font-size:0.7rem">{svc}</span> &nbsp;'
            f'<span style="color:#cbd5e1">{msg}</span> &nbsp;'
            f'<span style="color:{sc_col};font-size:0.65rem">▸ {score}</span>'
            f'</div>'
        )
    st.markdown(log_html+"</div>", unsafe_allow_html=True)
