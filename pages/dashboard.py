"""Dashboard – Real data from system_logs.txt."""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.generator import generate_timeseries, generate_logs, generate_anomalies, get_summary_stats

DARK="#020916"; GREEN="#00ffaa"; BLUE="#00d4ff"; RED="#ff4d6d"; AMBER="#ffb800"

def _layout(**kw):
    d = dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono, monospace", color="#94a3b8", size=11),
        margin=dict(l=16,r=16,t=44,b=16),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)",showline=False,zeroline=False),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)",showline=False,zeroline=False),
        hoverlabel=dict(bgcolor="#0f172a",bordercolor="#334155",font=dict(family="JetBrains Mono")),
    ); d.update(kw); return d


def render():
    stats = get_summary_stats()
    ts    = generate_timeseries()
    anoms = generate_anomalies(200)
    logs  = generate_logs(500)

    # Derived real numbers
    total        = stats["total"]
    crit         = stats["critical_count"]
    err          = stats["error_count"]
    warn         = stats["warn_count"]
    sec_cnt      = stats["security_count"]
    db_cnt       = stats["db_count"]
    anom_cnt     = stats["anomaly_count"]
    error_pct    = round((err + crit) / total * 100, 1)

    st.markdown("""
    <div class="page-title">Command Center</div>
    <div class="page-subtitle">REAL-TIME AIOPS DASHBOARD · system_logs.txt · 2026-01-27</div>
    """, unsafe_allow_html=True)

    # ── Source file badge ──────────────────────────────────────────────────────
    st.markdown(
        f'<div style="margin-bottom:16px">'
        f'<span class="badge badge-green">● REAL DATA</span> &nbsp;'
        f'<span style="font-size:0.7rem;color:#475569">Loaded from system_logs.txt · '
        f'{total:,} events · 2026-01-27 10:00 → 11:23</span></div>',
        unsafe_allow_html=True)

    # ── KPI Row ────────────────────────────────────────────────────────────────
    c1,c2,c3,c4,c5 = st.columns(5)
    kpis = [
        (f"{total:,}",     "Total Log Events",       f"{warn} warnings",     "delta-neutral"),
        (str(crit),        "CRITICAL Events",         "Needs attention",      "delta-down"),
        (str(err),         "ERROR Events",            f"{error_pct}% of total","delta-down"),
        (str(sec_cnt),     "Security Alerts",         "Auth + Brute force",   "delta-down"),
        (str(anom_cnt),    "Anomalies (score≥0.75)",  f"{db_cnt} DB events",  "delta-neutral"),
    ]
    for col,(val,lbl,delta,dcls) in zip([c1,c2,c3,c4,c5], kpis):
        with col:
            st.markdown(f"""
            <div class="metric-card">
              <div class="metric-value">{val}</div>
              <div class="metric-label">{lbl}</div>
              <div class="metric-delta {dcls}">{delta}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Log volume + error rate over time ──────────────────────────────────────
    col_a, col_b = st.columns([2,1])
    with col_a:
        st.markdown('<div class="section-header">Log Volume & Error Rate (per minute)</div>',
                    unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ts.index, y=ts["log_volume"],
            mode="lines", name="Log Volume",
            line=dict(color=BLUE,width=2),
            fill="tozeroy", fillcolor="rgba(0,212,255,0.07)",
        ))
        fig.add_trace(go.Scatter(
            x=ts.index, y=ts["error_rate"]*3,
            mode="lines", name="Error Rate %×3",
            line=dict(color=RED,width=1.5,dash="dot"), yaxis="y2",
        ))
        # Annotate anomaly spikes
        spikes = ts[ts["error_rate"] > 20]
        for idx_ts in spikes.index:
            fig.add_vline(x=idx_ts, line_color="rgba(255,77,109,0.2)", line_width=1)
        fig.update_layout(**_layout(
            yaxis2=dict(overlaying="y",side="right",gridcolor="rgba(0,0,0,0)",
                        showline=False,zeroline=False,title=dict(text="Error %",font=dict(color=RED))),
            height=260, showlegend=True, legend=dict(bgcolor="rgba(0,0,0,0)"),
        ))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

    with col_b:
        st.markdown('<div class="section-header">Severity Distribution</div>',
                    unsafe_allow_html=True)
        lc = stats["level_counts"]
        labels = list(lc.keys()); values = list(lc.values())
        colors = {
            "INFO": BLUE, "WARNING": AMBER, "ERROR": RED, "CRITICAL": "#ff0055",
        }
        fig2 = go.Figure(go.Pie(
            labels=labels, values=values, hole=0.62,
            marker=dict(colors=[colors.get(l,"#64748b") for l in labels],
                        line=dict(color=DARK,width=3)),
            textinfo="label+percent",
            textfont=dict(family="JetBrains Mono",size=10,color="#e2e8f0"),
        ))
        fig2.add_annotation(text="SEVERITY", x=0.5,y=0.56,showarrow=False,
                            font=dict(size=9,color="#64748b",family="JetBrains Mono"))
        fig2.add_annotation(text=str(total), x=0.5,y=0.42,showarrow=False,
                            font=dict(size=26,color="#fff",family="Syne"))
        fig2.update_layout(**_layout(height=260,showlegend=False))
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar":False})

    # ── Service volume bar + Anomaly timeline ──────────────────────────────────
    col_c, col_d = st.columns([1,1])
    with col_c:
        st.markdown('<div class="section-header">Log Volume by Service</div>',
                    unsafe_allow_html=True)
        svc = pd.Series(stats["svc_counts"]).sort_values(ascending=True)
        err_by_svc = logs[logs["level"].isin(["ERROR","CRITICAL"])].groupby("service").size()
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            y=svc.index.tolist(), x=svc.values,
            orientation="h", name="Total",
            marker=dict(color=BLUE,line=dict(width=0)),
        ))
        fig3.add_trace(go.Bar(
            y=err_by_svc.index.tolist(),
            x=err_by_svc.values,
            orientation="h", name="Errors",
            marker=dict(color=RED,line=dict(width=0)),
        ))
        fig3.update_layout(**_layout(height=260, barmode="overlay",
            title=dict(text="Volume by Service",font=dict(color="#e2e8f0",size=12)),
            legend=dict(bgcolor="rgba(0,0,0,0)")))
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar":False})

    with col_d:
        st.markdown('<div class="section-header">Top 10 Log Messages (Real Data)</div>',
                    unsafe_allow_html=True)
        top_msgs = stats["top_messages"][:10]
        msgs_df = pd.DataFrame(top_msgs, columns=["message","count"])
        msgs_df["short"] = msgs_df["message"].str[:35]
        fig4 = go.Figure(go.Bar(
            y=msgs_df["short"], x=msgs_df["count"],
            orientation="h",
            marker=dict(
                color=msgs_df["count"],
                colorscale=[[0,"#0f172a"],[0.5,AMBER],[1.0,RED]],
                line=dict(width=0),
            ),
            text=msgs_df["count"], textposition="outside",
            textfont=dict(size=9,color="#94a3b8"),
        ))
        fig4.update_layout(**_layout(height=260,
            title=dict(text="Frequency Distribution",font=dict(color="#e2e8f0",size=12))))
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar":False})

    # ── Security events heatmap ────────────────────────────────────────────────
    st.markdown('<div class="section-header">🔐 Security Events Timeline</div>',
                unsafe_allow_html=True)
    import numpy as np
    sec_logs = logs[logs["message"].str.contains(
        "Unauthorized|Brute force|Failed login|account locked|Rate limit|Suspicious IP",
        case=False, regex=True)]
    if len(sec_logs) > 0:
        sec_logs = sec_logs.copy()
        sec_logs["minute"] = sec_logs["timestamp"].dt.strftime("%H:%M")
        sec_pivot = sec_logs.groupby(["message","minute"]).size().unstack(fill_value=0)
        # Keep top 8 security message types
        top_sec = sec_pivot.sum(axis=1).nlargest(8).index
        sec_pivot = sec_pivot.loc[top_sec]
        fig5 = go.Figure(go.Heatmap(
            z=sec_pivot.values,
            x=sec_pivot.columns.tolist(),
            y=[m[:40] for m in sec_pivot.index.tolist()],
            colorscale=[[0,"#020916"],[0.3,"#1a0a1a"],[0.7,AMBER],[1.0,RED]],
            showscale=True,
            colorbar=dict(thickness=8, tickfont=dict(size=9,color="#64748b")),
        ))
        fig5.update_layout(**_layout(height=280,
            title=dict(text="Security Event Frequency Over Time",
                       font=dict(color="#e2e8f0",size=12))))
        st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar":False})

    # ── Recent anomaly alerts ──────────────────────────────────────────────────
    st.markdown('<div class="section-header">🔴 Top Anomaly Events (Real Logs)</div>',
                unsafe_allow_html=True)
    display = anoms.head(12)[["timestamp","type","service","score","severity","level","resolved","ttd_min"]].copy()
    display["timestamp"] = display["timestamp"].dt.strftime("%H:%M:%S")
    display["score"]     = display["score"].apply(lambda x: f"{x:.3f}")
    display["resolved"]  = display["resolved"].apply(lambda x: "✅" if x else "🔴")
    st.dataframe(display.rename(columns={
        "timestamp":"Time","type":"Event","service":"Service",
        "score":"Score","severity":"Severity","level":"Level",
        "resolved":"Resolved","ttd_min":"TTD(min)"
    }), use_container_width=True, height=340)
