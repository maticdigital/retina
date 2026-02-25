"""Project detail page — 7-tab interface for analysis, scoring, and export."""

from __future__ import annotations

import streamlit as st

from app.components.styles import COLORS, status_badge
from app.services.pipeline import run_analysis_sync
from app.services.projects import (
    get_analyst_scores,
    get_project,
    get_project_data,
    get_reports,
)
from app.tabs import brand, conversion, experience, export, overview, performance, seo


def render() -> None:
    """Render the project detail view with 7-tab navigation."""
    project_id = st.session_state.get("current_project_id")
    if not project_id:
        st.warning("No project selected.")
        if st.button("Back to Dashboard"):
            st.session_state["page"] = "dashboard"
            st.rerun()
        return

    project = get_project(project_id)
    if not project:
        st.error("Project not found.")
        return

    # --- Header ---
    hdr_left, hdr_right = st.columns([4, 2])

    with hdr_left:
        # Back link
        if st.button("← Back to Dashboard", key="back_dash"):
            _clear_analyst_state()
            st.session_state["page"] = "dashboard"
            st.rerun()

        # Project name
        st.markdown(
            f"<h1 style='color:{COLORS['text']};font-size:1.6rem;margin:0.25rem 0 4px 0;"
            f"font-weight:700;'>{project['name']}</h1>",
            unsafe_allow_html=True,
        )

        # Primary URL + competitors
        competitors = project.get("competitor_urls", [])
        comp_text = ""
        if competitors:
            comp_text = (
                f"<span style='margin-left:12px;color:{COLORS['text_dim']};font-size:0.82rem;'>"
                f"+ {len(competitors)} competitor{'s' if len(competitors) > 1 else ''}</span>"
            )
        st.markdown(
            f"<p style='color:{COLORS['text_muted']};font-size:0.88rem;margin:0;'>"
            f"{project['primary_url']}{comp_text}</p>",
            unsafe_allow_html=True,
        )

    with hdr_right:
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        # Status badge
        st.markdown(
            f"<div style='text-align:right;margin-bottom:12px;'>{status_badge(project['status'])}</div>",
            unsafe_allow_html=True,
        )
        # Run / Re-run button
        if project["status"] in ("draft", "complete"):
            label = "Run Analysis" if project["status"] == "draft" else "Re-run Analysis"
            if st.button(label, type="primary", use_container_width=True):
                _run_analysis(project)

    st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

    # --- Load all data once ---
    site_data = _load_cached(f"site_data_{project_id}", lambda: get_project_data(project_id))
    analyst_scores = _load_cached(f"analyst_scores_{project_id}", lambda: get_analyst_scores(project_id))
    reports = _load_cached(f"reports_{project_id}", lambda: get_reports(project_id))

    if not site_data and project["status"] == "draft":
        st.info("This project hasn't been analyzed yet. Click 'Run Analysis' to start.")
        return

    # --- 7 Tabs ---
    tab_names = [
        "Overview",
        "Performance",
        "SEO & AI",
        "Brand",
        "Experience",
        "Conversion",
        "Export",
    ]
    tabs = st.tabs(tab_names)

    with tabs[0]:
        overview.render(project, site_data, analyst_scores, reports)

    with tabs[1]:
        performance.render(site_data, project)

    with tabs[2]:
        seo.render(site_data, project)

    with tabs[3]:
        brand.render(project_id, site_data, analyst_scores, project)

    with tabs[4]:
        experience.render(project_id, site_data, analyst_scores, project)

    with tabs[5]:
        conversion.render(project_id, site_data, analyst_scores, project)

    with tabs[6]:
        export.render(project, site_data, analyst_scores, reports)


def _load_cached(key: str, loader):
    """Load data and cache in session_state to avoid repeated Supabase calls."""
    cache_key = f"_cache_{key}"
    if cache_key not in st.session_state:
        st.session_state[cache_key] = loader()
    return st.session_state[cache_key]


def _clear_analyst_state() -> None:
    """Clear analyst scoring session state when leaving project."""
    keys_to_clear = [
        k for k in st.session_state
        if k.startswith(("analyst_", "_loaded_", "_saved_", "_screenshots_", "_cache_",
                         "_save_status_", "_last_save_time"))
    ]
    for k in keys_to_clear:
        del st.session_state[k]


def _run_analysis(project: dict) -> None:
    """Trigger analysis run with progress display."""
    project_id = project["id"]
    primary_url = project["primary_url"]
    competitors = project.get("competitor_urls", [])

    progress_bar = st.progress(0, text="Starting analysis...")
    status_text = st.empty()
    steps = []

    def progress_callback(msg: str) -> None:
        steps.append(msg)
        pct = min(len(steps) / 10, 0.95)
        progress_bar.progress(pct, text=msg)
        status_text.markdown(f"*{msg}*")

    try:
        result = run_analysis_sync(
            project_id=project_id,
            primary_url=primary_url,
            competitor_urls=competitors,
            progress_callback=progress_callback,
        )
        progress_bar.progress(1.0, text="Complete!")
        st.success(f"Analysis complete! Retina Score: {result['retina_score']:.1f}")
        # Clear cache to reload fresh data
        _clear_analyst_state()
        st.rerun()
    except Exception as e:
        progress_bar.empty()
        st.error(f"Analysis failed: {e}")
