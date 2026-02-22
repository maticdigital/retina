"""Plotly-based interactive charts for the Retina web UI."""

from __future__ import annotations

import plotly.graph_objects as go

from app.components.styles import COLORS, hex_to_rgba

# Lens ordering and labels matching the scoring system
LENS_ORDER = [
    "performance_technical_health",
    "seo_ai_visibility",
    "brand_messaging",
    "experience_design",
    "conversion_strategy",
]

LENS_LABELS = {
    "performance_technical_health": "Performance",
    "seo_ai_visibility": "SEO & AI",
    "brand_messaging": "Brand",
    "experience_design": "Experience",
    "conversion_strategy": "Conversion",
}

SITE_COLORS = [
    "#076EFF",  # Primary — blue
    "#EF4444",  # Competitor 1 — red
    "#F59E0B",  # Competitor 2 — amber
    "#10B981",  # Competitor 3 — green
    "#8B5CF6",  # Competitor 4 — purple
]

_CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=COLORS["text"], family="sans-serif"),
    margin=dict(l=40, r=40, t=30, b=30),
)


def radar_chart(scores: dict[str, float | None], max_score: float = 20.0) -> go.Figure:
    """Radar/spider chart showing all 5 lens scores."""
    labels = [LENS_LABELS.get(k, k) for k in LENS_ORDER]
    values = [scores.get(k) or 0 for k in LENS_ORDER]
    # Close the polygon
    labels_closed = labels + [labels[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor=hex_to_rgba(COLORS["accent"], 0.13),
        line=dict(color=COLORS["accent"], width=2),
        marker=dict(size=6, color=COLORS["accent"]),
    ))
    fig.update_layout(
        **_CHART_LAYOUT,
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max_score],
                gridcolor=COLORS["border"],
                tickfont=dict(size=10, color=COLORS["text_dim"]),
            ),
            angularaxis=dict(
                gridcolor=COLORS["border"],
                tickfont=dict(size=12, color=COLORS["text_muted"]),
            ),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=False,
        height=350,
    )
    return fig


def grouped_bar_chart(
    site_scores: list[tuple[str, dict[str, float | None]]],
) -> go.Figure:
    """Grouped bar chart comparing lens scores across sites."""
    labels = [LENS_LABELS.get(k, k) for k in LENS_ORDER]
    fig = go.Figure()

    for i, (site_name, scores) in enumerate(site_scores):
        values = [scores.get(k) or 0 for k in LENS_ORDER]
        color = SITE_COLORS[i % len(SITE_COLORS)]
        fig.add_trace(go.Bar(
            name=site_name,
            x=labels,
            y=values,
            marker_color=color,
            marker_line_width=0,
        ))

    fig.update_layout(
        **_CHART_LAYOUT,
        barmode="group",
        yaxis=dict(
            range=[0, 20],
            gridcolor=COLORS["border"],
            tickfont=dict(size=11, color=COLORS["text_muted"]),
        ),
        xaxis=dict(tickfont=dict(size=11, color=COLORS["text_muted"])),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color=COLORS["text_muted"]),
        ),
        height=350,
    )
    return fig


def lighthouse_gauge(score: float, label: str = "") -> go.Figure:
    """Small circular gauge for a Lighthouse score (0-100)."""
    if score >= 90:
        color = COLORS["success"]
    elif score >= 50:
        color = COLORS["warning"]
    else:
        color = COLORS["error"]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number=dict(font=dict(size=28, color=COLORS["text"]), suffix=""),
        title=dict(text=label, font=dict(size=12, color=COLORS["text_muted"])),
        gauge=dict(
            axis=dict(range=[0, 100], visible=False),
            bar=dict(color=color, thickness=0.8),
            bgcolor=COLORS["border"],
            borderwidth=0,
            shape="angular",
        ),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"], family="sans-serif"),
        height=180,
        margin=dict(l=20, r=20, t=40, b=10),
    )
    return fig
