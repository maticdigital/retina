"""Project detail page — view analysis results."""

from __future__ import annotations

import streamlit as st

from app.components.styles import metric_card, status_badge
from app.services.projects import (
    get_project,
    get_project_data,
    get_reports,
    update_project_status,
)
from app.services.pipeline import run_analysis_sync


def render() -> None:
    """Render the project detail view."""
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

    # Header with back button
    c1, c2, c3 = st.columns([0.5, 4, 2])
    with c1:
        if st.button("Back"):
            st.session_state["page"] = "dashboard"
            st.rerun()
    with c2:
        st.markdown(
            f"### {project['name']} {status_badge(project['status'])}",
            unsafe_allow_html=True,
        )
    with c3:
        if project["status"] in ("draft", "complete"):
            label = "Run Analysis" if project["status"] == "draft" else "Re-run Analysis"
            if st.button(label, type="primary", use_container_width=True):
                _run_analysis(project)

    st.markdown(
        f"<p style='color: #8b92b3;'>Primary: {project['primary_url']}</p>",
        unsafe_allow_html=True,
    )
    competitors = project.get("competitor_urls", [])
    if competitors:
        st.markdown(
            f"<p style='color: #8b92b3;'>Competitors: {', '.join(competitors)}</p>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Load data
    site_data = get_project_data(project_id)
    reports = get_reports(project_id)

    if not site_data and project["status"] == "draft":
        st.info("This project hasn't been analyzed yet. Click 'Run Analysis' to start.")
        return

    if not site_data:
        st.info("No analysis data available yet.")
        return

    # Tabs
    tab1, tab2, tab3 = st.tabs(["Overview", "Site Details", "Reports"])

    with tab1:
        _render_overview(site_data, reports)

    with tab2:
        _render_site_details(site_data)

    with tab3:
        _render_reports(reports)


def _render_overview(site_data: list[dict], reports: list[dict]) -> None:
    """Render overview tab with key metrics."""
    if reports:
        latest = reports[0]
        score = latest.get("retina_score", 0)

        mc1, mc2, mc3 = st.columns(3)
        with mc1:
            st.markdown(
                metric_card(f"{score:.1f}", "Retina Score"),
                unsafe_allow_html=True,
            )
        with mc2:
            st.markdown(
                metric_card(str(len(site_data)), "Sites Analyzed"),
                unsafe_allow_html=True,
            )
        with mc3:
            has_ai = bool(latest.get("ai_analysis"))
            st.markdown(
                metric_card("Yes" if has_ai else "No", "AI Analysis"),
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

    # Score breakdown per site
    st.markdown("#### Scores by Site")
    for sd in site_data:
        scores = sd.get("automated_scores", {})
        url = sd.get("site_url", "Unknown")

        st.markdown(f"**{url}**")
        cols = st.columns(5)
        lens_names = [
            ("performance_technical_health", "Performance"),
            ("seo_ai_visibility", "SEO"),
            ("brand_messaging", "Brand"),
            ("experience_design", "Experience"),
            ("conversion_strategy", "Conversion"),
        ]
        for i, (key, label) in enumerate(lens_names):
            with cols[i]:
                data = scores.get(key, {})
                val = data.get("score", "-")
                if isinstance(val, (int, float)):
                    st.metric(label, f"{val:.1f}/20")
                else:
                    st.metric(label, "-/20")

    # Screenshots
    st.markdown("#### Screenshots")
    for sd in site_data:
        paths = sd.get("screenshot_paths", {})
        url = sd.get("site_url", "Unknown")
        if paths:
            st.markdown(f"**{url}**")
            sc1, sc2 = st.columns(2)
            with sc1:
                if paths.get("viewport"):
                    st.image(paths["viewport"], caption="Viewport", use_container_width=True)
            with sc2:
                if paths.get("full_page"):
                    st.image(paths["full_page"], caption="Full Page", use_container_width=True)


def _render_site_details(site_data: list[dict]) -> None:
    """Render detailed data per site."""
    for sd in site_data:
        url = sd.get("site_url", "Unknown")
        st.markdown(f"#### {url}")

        # Lighthouse data
        lh = sd.get("lighthouse_data", {})
        if lh:
            st.markdown("**Lighthouse Scores**")
            for strategy in ["mobile", "desktop"]:
                data = lh.get(strategy, {})
                scores = data.get("lighthouse_scores", {})
                if scores:
                    st.markdown(f"*{strategy.title()}*")
                    lc = st.columns(4)
                    for i, (key, label) in enumerate([
                        ("performance", "Performance"),
                        ("accessibility", "Accessibility"),
                        ("best_practices", "Best Practices"),
                        ("seo", "SEO"),
                    ]):
                        with lc[i]:
                            val = scores.get(key)
                            if val is not None:
                                st.metric(label, f"{val:.0f}")

                cwv = data.get("core_web_vitals", {})
                if cwv:
                    st.markdown(f"*{strategy.title()} Core Web Vitals*")
                    vc = st.columns(4)
                    vitals = [
                        ("largest_contentful_paint_ms", "LCP (ms)"),
                        ("first_contentful_paint_ms", "FCP (ms)"),
                        ("cumulative_layout_shift", "CLS"),
                        ("total_blocking_time_ms", "TBT (ms)"),
                    ]
                    for i, (key, label) in enumerate(vitals):
                        with vc[i]:
                            val = cwv.get(key)
                            if val is not None:
                                st.metric(label, f"{val:.1f}" if isinstance(val, float) else str(val))

        # Tech stack
        bw = sd.get("builtwith_data", {})
        techs = bw.get("technologies", [])
        if techs:
            st.markdown("**Technology Stack**")
            tech_names = [t.get("name", "") for t in techs if t.get("name")]
            st.markdown(", ".join(tech_names[:30]))
            if len(tech_names) > 30:
                st.markdown(f"*...and {len(tech_names) - 30} more*")

        st.markdown("---")


def _render_reports(reports: list[dict]) -> None:
    """Render reports list."""
    if not reports:
        st.info("No reports generated yet.")
        return

    for report in reports:
        try:
            from datetime import datetime
            gen_at = datetime.fromisoformat(report["generated_at"].replace("Z", "+00:00"))
            date_str = gen_at.strftime("%B %d, %Y at %I:%M %p")
        except (ValueError, KeyError):
            date_str = "Unknown date"

        score = report.get("retina_score", 0)
        pdf_path = report.get("pdf_path")

        rc1, rc2, rc3 = st.columns([3, 1, 1])
        with rc1:
            st.markdown(f"**Report — {date_str}**")
        with rc2:
            st.markdown(f"Score: **{score:.1f}**")
        with rc3:
            if pdf_path:
                st.markdown(f"[Download PDF]({pdf_path})")

        # AI Analysis summary
        ai = report.get("ai_analysis", {})
        if ai and ai.get("executive_summary"):
            with st.expander("AI Analysis Summary"):
                st.markdown(ai["executive_summary"][:500])

        st.markdown("---")


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
        st.rerun()
    except Exception as e:
        progress_bar.empty()
        st.error(f"Analysis failed: {e}")
