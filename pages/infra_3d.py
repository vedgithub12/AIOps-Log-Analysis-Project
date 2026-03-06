"""Infrastructure 3D – 3-D network graph, surface, scatter, and topology."""
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.generator import generate_nodes, SERVICES

GREEN="#00ffaa"; BLUE="#00d4ff"; RED="#ff4d6d"; AMBER="#ffb800"; PURPLE="#a855f7"
DARK="#020916"

HEALTH_COLOR = {"healthy": GREEN, "warn": AMBER, "critical": RED}

# Edges between services (dependency graph)
EDGES = [
    ("api-gateway","auth-service"),
    ("api-gateway","ml-pipeline"),
    ("api-gateway","db-proxy"),
    ("auth-service","db-proxy"),
    ("ml-pipeline","kafka-broker"),
    ("ml-pipeline","log-collector"),
    ("kafka-broker","log-collector"),
    ("log-collector","alert-manager"),
    ("alert-manager","grafana"),
    ("db-proxy","log-collector"),
]

def _base_layout3d(title=""):
    scene = dict(
        bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   backgroundcolor="rgba(0,0,0,0)"),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   backgroundcolor="rgba(0,0,0,0)"),
        zaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                   backgroundcolor="rgba(0,0,0,0)"),
    )
    return dict(
        scene=scene,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="JetBrains Mono, monospace", color="#94a3b8", size=11),
        margin=dict(l=0, r=0, t=40, b=0),
        title=dict(text=title, font=dict(color="#e2e8f0", size=13), x=0.02),
        hoverlabel=dict(bgcolor="#0f172a", bordercolor="#334155",
                        font=dict(family="JetBrains Mono")),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10)),
    )


def render():
    st.markdown("""
    <div class="page-title">Infrastructure 3D</div>
    <div class="page-subtitle">INTERACTIVE 3D TOPOLOGY · METRIC SURFACE · DEPENDENCY GRAPH</div>
    """, unsafe_allow_html=True)

    nodes = generate_nodes()
    rng   = np.random.default_rng(33)

    tabs = st.tabs(["🌐 Service Topology", "🏔️ Metric Surface", "📡 Live Scatter 3D",
                    "🕸️ Dependency Network"])

    # ── Tab 1 : 3-D Service Topology ─────────────────────────────────────────────
    with tabs[0]:
        st.markdown('<div class="section-header">3D Service Topology with Health Status</div>',
                    unsafe_allow_html=True)
        st.caption("Drag to rotate · Scroll to zoom · Hover for details")

        fig = go.Figure()

        # Draw edges
        node_pos = {row.id: (row.x, row.y, row.z) for _, row in nodes.iterrows()}
        for src, dst in EDGES:
            if src in node_pos and dst in node_pos:
                x0,y0,z0 = node_pos[src]
                x1,y1,z1 = node_pos[dst]
                fig.add_trace(go.Scatter3d(
                    x=[x0,x1,None], y=[y0,y1,None], z=[z0,z1,None],
                    mode="lines",
                    line=dict(color="rgba(148,163,184,0.15)", width=2),
                    showlegend=False, hoverinfo="skip",
                ))

        # Draw nodes by health
        for health, color in HEALTH_COLOR.items():
            sub = nodes[nodes.health == health]
            if len(sub) == 0:
                continue
            fig.add_trace(go.Scatter3d(
                x=sub.x, y=sub.y, z=sub.z,
                mode="markers+text",
                name=health.upper(),
                text=sub.id,
                textposition="top center",
                textfont=dict(size=9, color=color),
                marker=dict(
                    size=14,
                    color=color,
                    opacity=0.85,
                    line=dict(color=DARK, width=2),
                    symbol="circle",
                ),
                customdata=sub[["cpu","mem"]].values,
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "CPU: %{customdata[0]}%<br>"
                    "Memory: %{customdata[1]}%<br>"
                    f"Status: {health.upper()}<extra></extra>"
                ),
            ))

        # Tier rings (visual guides)
        for r, label in [(1.5,"Frontend"),(3.0,"Backend"),(4.5,"Data Layer")]:
            theta = np.linspace(0, 2*np.pi, 80)
            fig.add_trace(go.Scatter3d(
                x=r*np.cos(theta), y=r*np.sin(theta),
                z=np.zeros(80),
                mode="lines",
                line=dict(color="rgba(255,255,255,0.04)", width=1),
                showlegend=False, hoverinfo="skip",
            ))

        fig.update_layout(**_base_layout3d("Live Service Topology"),
                          height=560,
                          scene_camera=dict(eye=dict(x=1.4, y=1.4, z=0.8)))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True})

        # Legend
        lc1, lc2, lc3 = st.columns(3)
        for col, (label, color) in zip([lc1,lc2,lc3], [
            ("Healthy", GREEN), ("Warning", AMBER), ("Critical", RED)
        ]):
            with col:
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;font-size:0.75rem;">'
                    f'<div style="width:12px;height:12px;border-radius:50%;background:{color}"></div>'
                    f'<span style="color:{color}">{label}</span></div>',
                    unsafe_allow_html=True)

    # ── Tab 2 : 3-D Metric Surface ───────────────────────────────────────────────
    with tabs[1]:
        st.markdown('<div class="section-header">Anomaly Score Surface (Time × Service × Score)</div>',
                    unsafe_allow_html=True)
        st.caption("This surface shows anomaly score intensity across services and time periods")

        col1, col2 = st.columns([3,1])
        with col2:
            colormap = st.selectbox("Colormap",
                ["Plasma","Inferno","Turbo","RdYlGn","Viridis"], index=1)
            smooth = st.checkbox("Smooth surface", True)
            wireframe = st.checkbox("Show wireframe", False)

        with col1:
            hours   = np.arange(0, 25)
            svc_idx = np.arange(len(SERVICES))
            H, S    = np.meshgrid(hours, svc_idx)
            Z = (0.4
                 + 0.3 * np.sin(H / 4 + S[:, None] * 0.7)
                 + 0.15 * rng.uniform(-1, 1, H.shape)
                 + 0.1 * np.exp(-((H - 12)**2) / 10))
            Z = np.clip(Z, 0, 1)

            fig2 = go.Figure(go.Surface(
                x=hours, y=SERVICES, z=Z,
                colorscale=colormap,
                opacity=0.88,
                showscale=True,
                colorbar=dict(thickness=10, tickfont=dict(size=9,color="#64748b"),
                              title=dict(text="Score",font=dict(color="#94a3b8",size=10))),
                contours=dict(
                    z=dict(show=True, usecolormap=True,
                           highlightcolor=GREEN, project_z=True) if smooth else dict(),
                ) if smooth else {},
                lighting=dict(ambient=0.7, diffuse=0.5, roughness=0.6, specular=0.2),
            ))
            if wireframe:
                fig2.add_trace(go.Surface(
                    x=hours, y=SERVICES, z=Z,
                    colorscale=[[0,"rgba(255,255,255,0.03)"],[1,"rgba(255,255,255,0.03)"]],
                    opacity=0.2, showscale=False,
                    surfacecolor=np.zeros_like(Z),
                ))
            fig2.update_layout(**_base_layout3d("Anomaly Score Surface"),
                               height=520,
                               scene=dict(
                                   bgcolor="rgba(0,0,0,0)",
                                   xaxis=dict(title="Hour", showgrid=True,
                                              gridcolor="rgba(255,255,255,0.05)",
                                              tickfont=dict(color="#64748b")),
                                   yaxis=dict(title="Service", showgrid=True,
                                              gridcolor="rgba(255,255,255,0.05)",
                                              tickfont=dict(color="#64748b",size=9)),
                                   zaxis=dict(title="Anomaly Score", showgrid=True,
                                              gridcolor="rgba(255,255,255,0.05)",
                                              tickfont=dict(color="#64748b"),
                                              range=[0,1]),
                               ))
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": True})

    # ── Tab 3 : Live Scatter 3D ───────────────────────────────────────────────────
    with tabs[2]:
        st.markdown('<div class="section-header">CPU × Memory × Latency 3D Scatter</div>',
                    unsafe_allow_html=True)
        st.caption("Each point represents one service observation over 48 hours")

        n_pts = 600
        svc_ids   = rng.choice(SERVICES, n_pts)
        cpu_vals  = rng.uniform(10, 95, n_pts)
        mem_vals  = rng.uniform(20, 90, n_pts)
        lat_vals  = rng.uniform(20, 800, n_pts) + 300 * (cpu_vals > 80).astype(float)
        scores    = np.clip(0.3 + 0.5*(cpu_vals/100) + 0.3*(mem_vals/100) +
                            rng.normal(0, 0.1, n_pts), 0, 1)
        colors_pt = [RED if s > 0.75 else (AMBER if s > 0.5 else GREEN) for s in scores]

        col_x, col_y = st.columns([3,1])
        with col_y:
            threshold3d = st.slider("Score threshold highlight", 0.5, 1.0, 0.75, 0.01,
                                    key="scatter3d_thresh")
            size_by = st.selectbox("Bubble size", ["Score","Latency","CPU"])

        bubble_size = {
            "Score": scores * 12 + 4,
            "Latency": lat_vals / 80,
            "CPU": cpu_vals / 8,
        }[size_by]

        with col_x:
            fig3 = go.Figure()
            # Below threshold
            mask_ok  = scores < threshold3d
            mask_bad = ~mask_ok
            for mask, color, name in [(mask_ok, BLUE, "Normal"), (mask_bad, RED, "Anomaly")]:
                fig3.add_trace(go.Scatter3d(
                    x=cpu_vals[mask], y=mem_vals[mask], z=lat_vals[mask],
                    mode="markers",
                    name=name,
                    marker=dict(
                        size=bubble_size[mask],
                        color=color,
                        opacity=0.65,
                        line=dict(width=0),
                    ),
                    text=[f"{s} · score:{scores[i]:.2f}" for i, s in enumerate(svc_ids) if (mask_ok if name=="Normal" else mask_bad)[i]],
                    hovertemplate="<b>%{text}</b><br>CPU:%{x:.1f}% Mem:%{y:.1f}% Lat:%{z:.0f}ms<extra></extra>",
                ))
            fig3.update_layout(
                **_base_layout3d("CPU × Memory × Latency"),
                height=520,
                scene=dict(
                    bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(title="CPU %", gridcolor="rgba(255,255,255,0.05)",
                               tickfont=dict(color="#64748b")),
                    yaxis=dict(title="Memory %", gridcolor="rgba(255,255,255,0.05)",
                               tickfont=dict(color="#64748b")),
                    zaxis=dict(title="Latency ms", gridcolor="rgba(255,255,255,0.05)",
                               tickfont=dict(color="#64748b")),
                ),
                legend=dict(bgcolor="rgba(0,0,0,0)"),
            )
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": True})

    # ── Tab 4 : Dependency Network ────────────────────────────────────────────────
    with tabs[3]:
        st.markdown('<div class="section-header">3D Service Dependency Network (Force-Directed)</div>',
                    unsafe_allow_html=True)

        # Generate a denser random 3-D force-directed layout
        n = len(SERVICES)
        theta = np.linspace(0, 2*np.pi, n, endpoint=False)
        phi   = rng.uniform(0.5, 2.5, n)
        r     = rng.uniform(2, 5, n)
        xs = r * np.sin(phi) * np.cos(theta)
        ys = r * np.sin(phi) * np.sin(theta)
        zs = r * np.cos(phi)

        node_xyz = dict(zip(SERVICES, zip(xs, ys, zs)))

        fig4 = go.Figure()

        # All edges with glow
        for src, dst in EDGES:
            x0,y0,z0 = node_xyz[src]
            x1,y1,z1 = node_xyz[dst]
            # glow
            fig4.add_trace(go.Scatter3d(
                x=[x0,x1,None], y=[y0,y1,None], z=[z0,z1,None],
                mode="lines",
                line=dict(color="rgba(0,212,255,0.25)", width=3),
                showlegend=False, hoverinfo="skip",
            ))

        # Nodes
        node_df  = nodes.set_index("id")
        for i, svc in enumerate(SERVICES):
            x,y,z = node_xyz[svc]
            health = node_df.loc[svc, "health"] if svc in node_df.index else "healthy"
            color  = HEALTH_COLOR.get(health, GREEN)
            cpu    = node_df.loc[svc, "cpu"] if svc in node_df.index else 50
            mem    = node_df.loc[svc, "mem"] if svc in node_df.index else 50
            fig4.add_trace(go.Scatter3d(
                x=[x], y=[y], z=[z],
                mode="markers+text",
                text=[svc], textposition="top center",
                textfont=dict(size=9, color=color),
                marker=dict(size=16, color=color,
                            line=dict(color=DARK, width=2)),
                hovertemplate=(
                    f"<b>{svc}</b><br>Status: {health}<br>"
                    f"CPU: {cpu}%  Mem: {mem}%<extra></extra>"
                ),
                showlegend=False,
            ))

        fig4.update_layout(
            **_base_layout3d("Service Dependency Network"),
            height=560,
            scene=dict(
                bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False,zeroline=False,showticklabels=False,
                           backgroundcolor="rgba(0,0,0,0)"),
                yaxis=dict(showgrid=False,zeroline=False,showticklabels=False,
                           backgroundcolor="rgba(0,0,0,0)"),
                zaxis=dict(showgrid=False,zeroline=False,showticklabels=False,
                           backgroundcolor="rgba(0,0,0,0)"),
            ),
        )
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": True})

        # Info
        st.markdown("""
        <div style="display:flex;gap:24px;margin-top:8px;font-size:0.7rem;">
            <span style="color:#00ffaa">● Healthy nodes</span>
            <span style="color:#ffb800">● Warning nodes</span>
            <span style="color:#ff4d6d">● Critical nodes</span>
            <span style="color:#00d4ff">— Active data flow</span>
        </div>
        """, unsafe_allow_html=True)
