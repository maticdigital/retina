"""Overview tab — dashboard view with Retina Score, radar chart, competitor comparison."""

from __future__ import annotations

from urllib.parse import urlparse

import streamlit as st

from app.components.charts import LENS_LABELS, LENS_ORDER, grouped_bar_chart, radar_chart
from app.components.score_display import lens_score_card, score_ring_html
from app.components.styles import COLORS, status_badge


def render(
    project: dict,
    site_data: list[dict],
    analyst_scores: list[dict],
    reports: list[dict],
) -> None:
    """Render the Overview dashboard tab."""
    primary_url = project.get("primary_url", "")

    if not site_data:
        st.info("No analysis data available. Run an analysis to see your overview.")
        return

    # --- Collect all lens scores for primary site ---
    primary_sd = _find_primary(site_data, primary_url)
    all_scores = _collect_lens_scores(primary_sd, analyst_scores, primary_url)
    total_score = sum(v for v in all_scores.values() if v is not None)
    has_analyst = any(
        all_scores.get(k) is not None
        for k in ["brand_messaging", "experience_design", "conversion_strategy"]
    )
    max_score = 100.0 if has_analyst else 40.0

    # --- Score Ring + Radar Chart ---
    col_ring, col_radar = st.columns([1, 2])

    with col_ring:
        st.markdown(
            score_ring_html(total_score, max_score, size=180, label="Retina Score"),
            unsafe_allow_html=True,
        )
        st.markdown(
            f"<div style='text-align:center;margin-top:0.5rem;'>{status_badge(project['status'])}</div>",
            unsafe_allow_html=True,
        )

    with col_radar:
        fig = radar_chart(all_scores)
        st.plotly_chart(fig, use_container_width=True, key="overview_radar")

    st.markdown("---")

    # --- Lens Score Cards ---
    cols = st.columns(5)
    for i, lens_key in enumerate(LENS_ORDER):
        with cols[i]:
            label = LENS_LABELS.get(lens_key, lens_key)
            val = all_scores.get(lens_key)
            st.markdown(lens_score_card(label, val), unsafe_allow_html=True)

    st.markdown("---")

    # --- Competitor Comparison ---
    if len(site_data) > 1:
        st.markdown("##### Competitive Comparison")
        chart_data: list[tuple[str, dict[str, float | None]]] = []

        for sd in site_data:
            url = sd.get("site_url", "Unknown")
            short_name = urlparse(url).netloc if url.startswith("http") else url
            scores = _collect_lens_scores(sd, analyst_scores, url)
            chart_data.append((short_name, scores))

        fig = grouped_bar_chart(chart_data)
        st.plotly_chart(fig, use_container_width=True, key="overview_comparison")
        st.markdown("---")

    # --- Viewport Screenshot ---
    if primary_sd:
        paths = primary_sd.get("screenshot_paths", {})
        viewport_url = paths.get("viewport")
        if viewport_url:
            st.markdown("##### Primary Site Screenshot")
            st.image(viewport_url, use_container_width=True)

    # --- Latest Report Summary ---
    if reports:
        latest = reports[0]
        ai = latest.get("ai_analysis", {})
        if ai and ai.get("executive_summary"):
            st.markdown("##### AI Executive Summary")
            st.markdown(
                f"<div class='retina-card' style='color:{COLORS['text_muted']};font-size:0.9rem;"
                f"line-height:1.6;'>{ai['executive_summary'][:800]}</div>",
                unsafe_allow_html=True,
            )


def _find_primary(site_data: list[dict], primary_url: str) -> dict | None:
    """Find the primary site data entry."""
    for sd in site_data:
        if sd.get("site_url") == primary_url:
            return sd
    return site_data[0] if site_data else None


def _collect_lens_scores(
    sd: dict | None,
    analyst_scores: list[dict],
    site_url: str,
) -> dict[str, float | None]:
    """Collect all 5 lens scores for a site."""
    scores: dict[str, float | None] = {}

    # Automated scores from project_data
    if sd:
        auto = sd.get("automated_scores", {})
        for key in ["performance_technical_health", "seo_ai_visibility"]:
            data = auto.get(key, {})
            scores[key] = data.get("score")

    # Analyst scores
    for key in ["brand_messaging", "experience_design", "conversion_strategy"]:
        scores[key] = None
        for a in analyst_scores:
            if a.get("lens_name") == key and a.get("site_url") == site_url:
                sub_scores = a.get("sub_scores", {})
                if sub_scores:
                    scores[key] = sum(float(v) for v in sub_scores.values())
                break

    return scores
