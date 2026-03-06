"""Dashboard – Overview page."""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.generator import generate_timeseries, generate_logs, generate_anomalies

DARK = "#020916"
CARD = "rgba(255,255,255,0.03)"
GREEN = "#00ffaa"
BLUE  = "#00d4ff"
RED   = "#ff4d6d"
AMBER = "#ffb800"

def _chart_layout(title=""):
    return dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono, monospace", color="#94a3b8", size=11),
        title=dict(text=title, font=dict(color="#e2e8f0", size=13), x=0.02),
        margin=dict(l=16, r=16, t=40, b=16),
        xaxis=dict(gridcolor="rgba(255,255,255,0.04)", showline=False, zeroline=False),
        yaxis=dict(gridcolor="rgba(255,255,255,0.04)", showline=False, zeroline=False),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
        hoverlabel=dict(bgcolor="#0f172a", bordercolor="#334155", font=dict(family="JetBrains Mono")),
    )


def render():
    ts   = generate_timeseries(hours=24)
    logs = generate_logs(200)
    anoms = generate_anomalies(80)

    # ── Page title ──────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="page-title">Command Center</div>
    <div class="page-subtitle">REAL-TIME AIOPS MONITORING DASHBOARD · LAST 24 HOURS</div>
    """, unsafe_allow_html=True)

    # ── KPI Row ─────────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    kpis = [
        ("11,240", "Logs / Second", "+8.2%", "delta-up"),
        ("98.1%", "Detection Rate", "+0.4%", "delta-up"),
        (str(int(anoms[~anoms.resolved].shape[0])), "Active Anomalies", "3 critical", "delta-down"),
        (f"{ts['latency_p99'].iloc[-1]}ms", "P99 Latency", "-12ms", "delta-up"),
        (f"{ts['cpu_usage'].iloc[-1]}%", "Avg CPU", "+2.1%", "delta-neutral"),
    ]
    for col, (val, lbl, delta, dcls) in zip([c1,c2,c3,c4,c5], kpis):
        with col:
            st.markdown(f"""
            <div class="metric-card">
              <div class="metric-value">{val}</div>
              <div class="metric-label">{lbl}</div>
              <div class="metric-delta {dcls}">{delta}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 1 : Log volume + Error rate ────────────────────────────────────────
    col_a, col_b = st.columns([2, 1])

    with col_a:
        st.markdown('<div class="section-header">Log Volume & Error Rate</div>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=ts.index, y=ts["log_volume"],
            mode="lines", name="Log Volume",
            line=dict(color=BLUE, width=2),
            fill="tozeroy",
            fillcolor="rgba(0,212,255,0.07)",
        ))
        fig.add_trace(go.Scatter(
            x=ts.index, y=ts["error_rate"] * 150,
            mode="lines", name="Error Rate (×150)",
            line=dict(color=RED, width=1.5, dash="dot"),
            yaxis="y2",
        ))
        fig.update_layout(
            **_chart_layout(),
            yaxis2=dict(overlaying="y", side="right",
                        gridcolor="rgba(0,0,0,0)", showline=False, zeroline=False,
                        title=dict(text="Error Rate %", font=dict(color=RED))),
            height=260,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with col_b:
        st.markdown('<div class="section-header">Anomaly Breakdown</div>', unsafe_allow_html=True)
        sev_counts = anoms["severity"].value_counts().reset_index()
        fig2 = go.Figure(go.Pie(
            labels=sev_counts["severity"],
            values=sev_counts["count"],
            hole=0.65,
            marker=dict(colors=[RED, AMBER, "#7c3aed"],
                        line=dict(color=DARK, width=3)),
            textinfo="label+percent",
            textfont=dict(family="JetBrains Mono", size=10, color="#e2e8f0"),
        ))
        fig2.add_annotation(text="ANOMALIES", x=0.5, y=0.55, showarrow=False,
                            font=dict(size=10, color="#64748b", family="JetBrains Mono"))
        fig2.add_annotation(text=str(len(anoms)), x=0.5, y=0.42, showarrow=False,
                            font=dict(size=28, color="#fff", family="Syne"))
        fig2.update_layout(**_chart_layout(), height=260, showlegend=False)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    # ── Row 2 : Heatmap + Service health ───────────────────────────────────────
    col_c, col_d = st.columns([1, 1])

    with col_c:
        st.markdown('<div class="section-header">Anomaly Heatmap by Service & Hour</div>', unsafe_allow_html=True)
        import numpy as np
        services = ["api-gateway","auth-service","db-proxy","ml-pipeline","kafka-broker","log-collector"]
        hours    = [f"{h:02d}:00" for h in range(0, 24, 2)]
        rng2     = np.random.default_rng(99)
        heat_z   = rng2.integers(0, 20, size=(len(services), len(hours)))
        fig3 = go.Figure(go.Heatmap(
            z=heat_z, x=hours, y=services,
            colorscale=[[0,"#020916"],[0.3,"#0f2d3b"],[0.6,AMBER],[1.0,RED]],
            showscale=True,
            colorbar=dict(thickness=8, tickfont=dict(size=9, color="#64748b")),
        ))
        fig3.update_layout(**_chart_layout(), height=260)
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    with col_d:
        st.markdown('<div class="section-header">CPU vs Memory Usage (Services)</div>', unsafe_allow_html=True)
        scatter_data = pd.DataFrame({
            "service": services,
            "cpu":  np.random.default_rng(10).integers(20, 92, len(services)),
            "mem":  np.random.default_rng(20).integers(30, 88, len(services)),
            "rps":  np.random.default_rng(30).integers(100, 3000, len(services)),
            "health": ["healthy","warn","healthy","critical","healthy","warn"],
        })
        color_map = {"healthy": GREEN, "warn": AMBER, "critical": RED}
        fig4 = go.Figure()
        for h, color in color_map.items():
            sub = scatter_data[scatter_data.health == h]
            if len(sub):
                fig4.add_trace(go.Scatter(
                    x=sub["cpu"], y=sub["mem"],
                    mode="markers+text",
                    name=h.upper(),
                    text=sub["service"],
                    textposition="top center",
                    textfont=dict(size=9, color=color),
                    marker=dict(size=sub["rps"]/80, color=color,
                                line=dict(width=1, color="rgba(0,0,0,0.3)")),
                ))
        fig4.update_layout(**_chart_layout(), height=260,
                           xaxis_title="CPU %", yaxis_title="Memory %")
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})

    # ── Row 3 : Recent alerts table ─────────────────────────────────────────────
    st.markdown('<div class="section-header">Recent Anomaly Alerts</div>', unsafe_allow_html=True)
    display = anoms.head(8)[["timestamp","type","service","score","severity","resolved","ttd_min"]].copy()
    display["timestamp"] = display["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    display["score"]     = display["score"].apply(lambda x: f"{x:.3f}")
    display["resolved"]  = display["resolved"].apply(lambda x: "✅ Yes" if x else "🔴 No")

    def _color_sev(val):
        m = {"CRITICAL":"color:#ff4d6d","HIGH":"color:#ffb800","MEDIUM":"color:#00d4ff"}
        return m.get(val, "")

    st.dataframe(
        display.rename(columns={
            "timestamp":"Timestamp","type":"Anomaly Type","service":"Service",
            "score":"Score","severity":"Severity","resolved":"Resolved","ttd_min":"TTD (min)"
        }),
        use_container_width=True,
        height=280,
    )
