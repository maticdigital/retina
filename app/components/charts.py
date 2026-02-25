"""Plotly-based interactive charts for the Retina web UI."""

from __future__ import annotations

import plotly.graph_objects as go

from app.components.styles import COLORS, LENS_COLORS, LENS_SHORT_LABELS, hex_to_rgba

# Lens ordering
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
    "#076EFF",
    "#E74C3C",
    "#FF8C00",
    "#00C864",
    "#9B59B6",
]

_CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=COLORS["text"], family="sans-serif"),
    margin=dict(l=40, r=40, t=30, b=30),
)


def segmented_donut_chart(
    scores: dict[str, float | None],
    max_per_lens: float = 20.0,
) -> go.Figure:
    """Segmented 5-arc donut chart for composite Retina Score.

    Each lens occupies exactly 1/5 of the circle. Within each fifth,
    the colored arc fills proportionally to the lens score out of 20.
    """
    values: list[float] = []
    colors: list[str] = []
    custom_labels: list[str] = []

    for key in LENS_ORDER:
        score = scores.get(key) or 0
        remainder = max_per_lens - score
        values.extend([max(score, 0.01), max(remainder, 0.01)])
        colors.extend([LENS_COLORS.get(key, COLORS["accent"]), "#F0F2F5"])
        label = LENS_LABELS.get(key, key)
        custom_labels.extend([f"{label}: {score:.1f}/20", ""])

    total = sum(scores.get(k) or 0 for k in LENS_ORDER)

    fig = go.Figure(
        go.Pie(
            values=values,
            labels=custom_labels,
            hole=0.72,
            sort=False,
            direction="clockwise",
            rotation=90,
            marker=dict(colors=colors, line=dict(color="#F0F2F5", width=2)),
            textinfo="none",
            hoverinfo="label",
            hovertemplate="%{label}<extra></extra>",
        )
    )

    # Center text — total score
    fig.add_annotation(
        text=(
            f"<b style='font-size:42px;color:{COLORS['text']};'>{total:.1f}</b>"
            f"<br><span style='font-size:13px;color:{COLORS['text_muted']};'>/100</span>"
        ),
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14),
    )

    fig.update_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        height=300,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
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
