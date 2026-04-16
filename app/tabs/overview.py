"""Overview tab — segmented donut, lens summary cards, competitor comparison."""

from __future__ import annotations

import math
import os
from urllib.parse import urlparse

import streamlit as st

from app.components.charts import LENS_ORDER, grouped_bar_chart, segmented_donut_chart
from app.components.explanations import get_interpretation, interpretation_html, section_narrative_html
from app.components.score_display import lens_legend_html, lens_summary_card, _read_lens_icon
from app.components.styles import COLORS, LENS_COLORS, LENS_DEFINITIONS, LENS_SHORT_LABELS, status_badge


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

    # Extract interpretations from primary site data
    interp = primary_sd.get("interpretations") or {} if primary_sd else {}

    # --- Top Section: Donut + Lens Cards ---
    col_donut, col_cards = st.columns([1, 1])

    with col_donut:
        # Segmented donut chart
        fig = segmented_donut_chart(all_scores)
        st.plotly_chart(fig, use_container_width=True, key="overview_donut")

        # Legend row
        st.markdown(lens_legend_html(all_scores), unsafe_allow_html=True)

        # Status badge
        st.markdown(
            f"<div style='text-align:center;margin-top:0.5rem;'>{status_badge(project['status'])}</div>",
            unsafe_allow_html=True,
        )

    with col_cards:
        st.markdown(
            f"<p style='color:{COLORS['text_muted']};font-size:0.82rem;font-weight:500;"
            f"margin-bottom:0.75rem;'>Lens Scores</p>",
            unsafe_allow_html=True,
        )
        # Render 5 lens summary cards
        for lens_key in LENS_ORDER:
            score = all_scores.get(lens_key)
            icon_svg = _read_lens_icon(lens_key)
            st.markdown(
                lens_summary_card(lens_key, score, icon_svg),
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # --- AI Summary Card ---
    score_interp = get_interpretation(interp, "overall.retina_score")
    if score_interp:
        st.markdown(
            f"<div class='retina-card'>"
            f"<div style='color:{COLORS['accent']};font-size:0.72rem;text-transform:uppercase;"
            f"letter-spacing:0.05em;font-weight:600;margin-bottom:8px;'>AI Summary</div>",
            unsafe_allow_html=True,
        )
        st.markdown(interpretation_html(score_interp), unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    elif reports:
        # Fall back to executive summary from latest report
        latest = reports[0]
        ai = latest.get("ai_analysis", {})
        if ai and ai.get("executive_summary"):
            st.markdown(
                f"<div class='retina-card'>"
                f"<div style='color:{COLORS['accent']};font-size:0.72rem;text-transform:uppercase;"
                f"letter-spacing:0.05em;font-weight:600;margin-bottom:8px;'>AI Executive Summary</div>"
                f"<div style='color:{COLORS['text_muted']};font-size:0.88rem;line-height:1.6;'>"
                f"{ai['executive_summary'][:800]}</div></div>",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # --- Competitor Comparison ---
    if len(site_data) > 1:
        st.markdown(
            f"<p style='color:{COLORS['text']};font-size:1.1rem;font-weight:600;"
            f"margin-bottom:0.75rem;'>Competitive Comparison</p>",
            unsafe_allow_html=True,
        )

        chart_data: list[tuple[str, dict[str, float | None]]] = []
        for sd in site_data:
            url = sd.get("site_url", "Unknown")
            short_name = urlparse(url).netloc if url.startswith("http") else url
            scores = _collect_lens_scores(sd, analyst_scores, url)
            chart_data.append((short_name, scores))

        fig = grouped_bar_chart(chart_data)
        st.plotly_chart(fig, use_container_width=True, key="overview_comparison")

        # Competitive narrative from interpretations
        comp_narrative = interp.get("competitive_narrative", "")
        if comp_narrative:
            st.markdown(section_narrative_html(comp_narrative), unsafe_allow_html=True)
    else:
        # No competitors callout
        st.markdown(
            f"<div class='retina-card' style='text-align:center;padding:2rem;'>"
            f"<p style='color:{COLORS['text_dim']};font-size:0.88rem;margin:0;'>"
            f"No competitor URLs added. Add competitors to see a comparison chart.</p></div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # --- Viewport Screenshot ---
    if primary_sd:
        paths = primary_sd.get("screenshot_paths", {})
        viewport_url = paths.get("viewport")
        if viewport_url:
            st.markdown(
                f"<p style='color:{COLORS['text']};font-size:1.1rem;font-weight:600;"
                f"margin-bottom:0.75rem;'>Primary Site Screenshot</p>",
                unsafe_allow_html=True,
            )
            st.image(viewport_url, use_container_width=True)


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
            raw = data.get("score")
            scores[key] = math.floor(raw + 0.5) if raw is not None else None

    # Analyst scores
    for key in ["brand_messaging", "experience_design", "conversion_strategy"]:
        scores[key] = None
        for a in analyst_scores:
            if a.get("lens_name") == key and a.get("site_url") == site_url:
                sub_scores = a.get("sub_scores", {})
                if sub_scores:
                    scores[key] = math.floor(sum(float(v) for v in sub_scores.values()) + 0.5)
                break

    return scores
