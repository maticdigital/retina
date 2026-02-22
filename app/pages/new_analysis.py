"""New Analysis page — create a project and trigger analysis."""

from __future__ import annotations

import streamlit as st

from app.components.styles import COLORS
from app.services.projects import create_project
from app.services.pipeline import run_analysis_sync


def render() -> None:
    """Render the new analysis creation page."""
    user = st.session_state.get("user", {})

    st.markdown("### New Analysis")
    st.markdown(
        f"<p style='color: {COLORS['text_muted']};'>Create a new competitive analysis project.</p>",
        unsafe_allow_html=True,
    )

    with st.form("new_project_form"):
        name = st.text_input("Project Name", placeholder="e.g., Q1 2026 Competitive Audit")
        primary_url = st.text_input("Primary URL", placeholder="https://yoursite.com")

        st.markdown(
            f"<p style='color: {COLORS['text_muted']}; font-size: 0.85rem; margin-top: 0.5rem;'>"
            "Add up to 3 competitor URLs for comparative analysis.</p>",
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            comp1 = st.text_input("Competitor 1", placeholder="https://competitor1.com", key="comp1")
        with c2:
            comp2 = st.text_input("Competitor 2", placeholder="https://competitor2.com", key="comp2")
        with c3:
            comp3 = st.text_input("Competitor 3", placeholder="https://competitor3.com", key="comp3")

        col1, col2 = st.columns([1, 3])
        with col1:
            submitted = st.form_submit_button("Create & Run Analysis", type="primary", use_container_width=True)
        with col2:
            save_draft = st.form_submit_button("Save as Draft", use_container_width=True)

    if submitted or save_draft:
        if not name:
            st.error("Project name is required.")
            return
        if not primary_url:
            st.error("Primary URL is required.")
            return

        # Collect competitors
        competitors = [u.strip() for u in [comp1, comp2, comp3] if u and u.strip()]

        # Create project
        try:
            project = create_project(
                name=name,
                primary_url=primary_url,
                competitor_urls=competitors,
                created_by=user["id"],
            )
            st.success(f"Project **{name}** created.")
        except Exception as e:
            st.error(f"Failed to create project: {e}")
            return

        if save_draft:
            st.session_state["page"] = "dashboard"
            st.rerun()
            return

        # Run analysis
        project_id = project["id"]
        st.session_state["current_project_id"] = project_id

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

            st.markdown("---")
            st.markdown("#### Analysis Complete")

            rc1, rc2, rc3 = st.columns(3)
            with rc1:
                st.metric("Retina Score", f"{result['retina_score']:.1f}")
            with rc2:
                st.metric("Sites Analyzed", result["sites_analyzed"])
            with rc3:
                st.metric("AI Analysis", "Yes" if result["ai_analysis"] else "No")

            if result.get("pdf_url"):
                st.markdown(f"[Download PDF Report]({result['pdf_url']})")

            if st.button("View Project Details", type="primary"):
                st.session_state["page"] = "project_detail"
                st.rerun()

        except Exception as e:
            progress_bar.empty()
            st.error(f"Analysis failed: {e}")
            st.markdown("The project has been saved as draft. You can retry from the dashboard.")
