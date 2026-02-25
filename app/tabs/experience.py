"""Experience & Design analyst tab — 5 sub-dimensions x 4pts = 20pts."""

from __future__ import annotations

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from retina.scoring.analyst import LENS_DEFINITIONS

from app.components.analyst_workspace import render_analyst_lens
from app.components.explanations import get_interpretation
from app.components.score_display import _read_lens_icon
from app.components.styles import COLORS, LENS_COLORS, LENS_DEFINITIONS as STYLE_DEFS


LENS_KEY = "experience_design"
LENS_TITLE = "Experience & Design"


def render(
    project_id: str,
    site_data: list[dict],
    analyst_scores: list[dict],
    project: dict,
) -> None:
    """Render the Experience & Design scoring workspace."""
    if not site_data:
        st.info("No analysis data available. Run an analysis first.")
        return

    primary_url = project.get("primary_url", "")
    site_url = site_data[0].get("site_url", primary_url)

    if len(site_data) > 1:
        urls = [sd.get("site_url", "") for sd in site_data]
        site_url = st.selectbox("Select site to score", urls, key="experience_site_select")

    existing = _find_existing(analyst_scores, site_url, LENS_KEY)
    current_sd = _find_site_data(site_data, site_url)

    # --- Lens Header ---
    _render_lens_header(LENS_KEY, LENS_TITLE, current_sd)

    render_analyst_lens(
        project_id=project_id,
        site_url=site_url,
        lens_name=LENS_KEY,
        sub_dimensions=LENS_DEFINITIONS[LENS_KEY],
        existing_data=existing,
        site_data=current_sd,
    )


def _render_lens_header(lens_key: str, title: str, site_data: dict | None) -> None:
    """Render the standard lens header: icon + title + definition + orientation."""
    color = LENS_COLORS.get(lens_key, COLORS["accent"])
    definition = STYLE_DEFS.get(lens_key, "")
    icon_svg = _read_lens_icon(lens_key)

    icon_html = ""
    if icon_svg:
        icon_html = f"<div style='width:28px;height:28px;flex-shrink:0;'>{icon_svg}</div>"

    st.markdown(
        f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:4px;'>"
        f"{icon_html}"
        f"<h2 style='color:{COLORS['text']};font-size:1.3rem;margin:0;font-weight:700;'>"
        f"{title}</h2></div>"
        f"<p style='color:{COLORS['text_muted']};font-size:0.85rem;margin:0 0 1rem 0;'>"
        f"{definition}</p>",
        unsafe_allow_html=True,
    )

    if site_data:
        interp = site_data.get("interpretations") or {}
        lens_interp = get_interpretation(interp, f"analyst_lenses.{lens_key}")
        if lens_interp:
            orientation = lens_interp.get("orientation", "")
            good_looks_like = lens_interp.get("what_good_looks_like", "")
            if orientation or good_looks_like:
                st.markdown(
                    f"<div class='retina-card' style='border-left:3px solid {color};padding:12px 16px;'>"
                    f"<div style='color:{color};font-size:0.72rem;text-transform:uppercase;"
                    f"letter-spacing:0.05em;font-weight:600;margin-bottom:6px;'>Lens Orientation</div>"
                    + (f"<div style='color:{COLORS['text']};font-size:0.82rem;line-height:1.5;'>{orientation}</div>" if orientation else "")
                    + (f"<div style='color:{COLORS['text_muted']};font-size:0.78rem;line-height:1.5;"
                       f"margin-top:6px;'><strong>What good looks like:</strong> {good_looks_like}</div>" if good_looks_like else "")
                    + "</div>",
                    unsafe_allow_html=True,
                )

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)


def _find_existing(analyst_scores: list[dict], site_url: str, lens_name: str) -> dict | None:
    for s in analyst_scores:
        if s.get("lens_name") == lens_name and s.get("site_url") == site_url:
            return s
    return None


def _find_site_data(site_data: list[dict], site_url: str) -> dict | None:
    for sd in site_data:
        if sd.get("site_url") == site_url:
            return sd
    return site_data[0] if site_data else None
