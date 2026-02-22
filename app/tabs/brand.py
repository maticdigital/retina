"""Brand & Messaging analyst tab — 4 sub-dimensions x 5pts = 20pts."""

from __future__ import annotations

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from retina.scoring.analyst import LENS_DEFINITIONS

from app.components.analyst_workspace import render_analyst_lens


def render(
    project_id: str,
    site_data: list[dict],
    analyst_scores: list[dict],
    project: dict,
) -> None:
    """Render the Brand & Messaging scoring workspace."""
    if not site_data:
        st.info("No analysis data available. Run an analysis first.")
        return

    primary_url = project.get("primary_url", "")
    site_url = site_data[0].get("site_url", primary_url)

    # Site selector if multiple sites
    if len(site_data) > 1:
        urls = [sd.get("site_url", "") for sd in site_data]
        site_url = st.selectbox("Select site to score", urls, key="brand_site_select")

    # Find existing scores for this lens + site
    existing = _find_existing(analyst_scores, site_url, "brand_messaging")

    # Find the site_data dict for the selected URL (for AI re-evaluate)
    current_sd = _find_site_data(site_data, site_url)

    render_analyst_lens(
        project_id=project_id,
        site_url=site_url,
        lens_name="brand_messaging",
        sub_dimensions=LENS_DEFINITIONS["brand_messaging"],
        existing_data=existing,
        site_data=current_sd,
    )


def _find_existing(
    analyst_scores: list[dict],
    site_url: str,
    lens_name: str,
) -> dict | None:
    """Find existing analyst score for a specific lens and URL."""
    for s in analyst_scores:
        if s.get("lens_name") == lens_name and s.get("site_url") == site_url:
            return s
    return None


def _find_site_data(site_data: list[dict], site_url: str) -> dict | None:
    """Find site_data dict for a given URL."""
    for sd in site_data:
        if sd.get("site_url") == site_url:
            return sd
    return site_data[0] if site_data else None
