"""Dashboard page — project card grid with welcome header and copilot placeholder."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from app.components.styles import COLORS, status_badge
from app.services.projects import delete_project, duplicate_project, list_projects


def render() -> None:
    """Render the dashboard/project list."""
    user = st.session_state.get("user", {})
    user_id = user.get("id", "")
    user_role = user.get("role", "analyst")
    first_name = user.get("name", "User").split()[0] if user.get("name") else "User"

    # Header row
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            f"<h1 style='color:{COLORS['text']};font-size:1.8rem;margin:0 0 4px 0;'>"
            f"Welcome back, {first_name}</h1>"
            f"<p style='color:{COLORS['text_muted']};font-size:0.88rem;margin:0;'>"
            f"{datetime.now().strftime('%A, %B %d, %Y')}</p>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("+ New Analysis", type="primary", use_container_width=True):
            st.session_state["page"] = "new_analysis"
            st.rerun()

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    # Fetch projects
    projects = list_projects(user_id, user_role)

    # Section label
    st.markdown(
        f"<p style='color:{COLORS['text_muted']};font-size:0.88rem;font-weight:500;"
        f"margin-bottom:1rem;'>Your Analyses</p>",
        unsafe_allow_html=True,
    )

    # Show Quick Start inline if zero projects
    if not projects:
        _render_empty_state()
        _render_copilot_placeholder()
        return

    # Search and filter
    fc1, fc2, fc3 = st.columns([3, 1, 1])
    with fc1:
        search = st.text_input(
            "Search projects",
            placeholder="Search by name or URL...",
            label_visibility="collapsed",
        )
    with fc2:
        sort_by = st.selectbox(
            "Sort",
            ["Newest", "Oldest", "Name A-Z", "Name Z-A"],
            label_visibility="collapsed",
        )
    with fc3:
        filter_status = st.selectbox(
            "Status",
            ["All", "Draft", "In Progress", "Complete"],
            label_visibility="collapsed",
        )

    # Filter
    filtered = projects
    if search:
        q = search.lower()
        filtered = [
            p for p in filtered
            if q in p["name"].lower() or q in p["primary_url"].lower()
        ]
    if filter_status != "All":
        status_map = {"Draft": "draft", "In Progress": "in_progress", "Complete": "complete"}
        filtered = [p for p in filtered if p["status"] == status_map[filter_status]]

    # Sort
    if sort_by == "Newest":
        filtered.sort(key=lambda p: p.get("updated_at", ""), reverse=True)
    elif sort_by == "Oldest":
        filtered.sort(key=lambda p: p.get("updated_at", ""))
    elif sort_by == "Name A-Z":
        filtered.sort(key=lambda p: p["name"].lower())
    elif sort_by == "Name Z-A":
        filtered.sort(key=lambda p: p["name"].lower(), reverse=True)

    if not filtered:
        st.markdown(
            f"<div style='text-align:center;padding:3rem;color:{COLORS['text_muted']};'>"
            f"<p style='font-size:1.1rem;'>No matching projects found</p>"
            f"</div>",
            unsafe_allow_html=True,
        )
        _render_copilot_placeholder()
        return

    # 2-column card grid
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    for i in range(0, len(filtered), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(filtered):
                with col:
                    _render_project_card(filtered[idx])

    _render_copilot_placeholder()


def _render_project_card(project: dict) -> None:
    """Render a single project as a card."""
    pid = project["id"]
    badge = status_badge(project["status"])

    # Parse date
    try:
        updated = datetime.fromisoformat(project["updated_at"].replace("Z", "+00:00"))
        date_str = updated.strftime("%b %d, %Y")
    except (ValueError, KeyError):
        date_str = ""

    # Retina Score — from the latest report if available
    score_display = "—"
    score_label = "Not scored"

    st.markdown(
        f"""<div class="project-card">
  <div class="project-arrow">→</div>
  <div class="project-name">{project['name']}</div>
  <div class="project-url">{project['primary_url']}</div>
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
    {badge}
    <span style="color:{COLORS['text_dim']};font-size:0.78rem;">{date_str}</span>
  </div>
  <div style="display:flex;align-items:baseline;gap:6px;">
    <span class="project-score">{score_display}</span>
    <span class="project-score-label">Retina Score</span>
  </div>
</div>""",
        unsafe_allow_html=True,
    )

    # Invisible button to handle click
    if st.button("Open", key=f"open_{pid}", use_container_width=True):
        st.session_state["page"] = "project_detail"
        st.session_state["current_project_id"] = pid
        st.rerun()


def _render_empty_state() -> None:
    """Render the empty state with inline Quick Start steps."""
    from app.components.quick_start import render_quick_start_inline

    st.markdown(
        f"""<div style="text-align:center;padding:3rem 2rem;">
  <div style="font-size:3rem;margin-bottom:1rem;">📊</div>
  <h3 style="color:{COLORS['text']};margin-bottom:0.5rem;">No analyses yet</h3>
  <p style="color:{COLORS['text_muted']};margin-bottom:2rem;">
    Start your first analysis to evaluate a website's digital readiness.
  </p>
</div>""",
        unsafe_allow_html=True,
    )

    render_quick_start_inline()

    if st.button("Start your first analysis", type="primary"):
        st.session_state["page"] = "new_analysis"
        st.rerun()


def _render_copilot_placeholder() -> None:
    """Render the Retina Copilot placeholder at the bottom of the dashboard."""
    # RETINA COPILOT — UI PLACEHOLDER, NOT YET WIRED
    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
    st.markdown(
        f"""<div class="copilot-label">
  <span>Retina Copilot</span>
  <span class="copilot-badge">Coming Soon</span>
</div>
<div class="copilot-bar">
  <span style="font-size:1.1rem;color:{COLORS['text_dim']};">💬</span>
  <span style="flex:1;color:{COLORS['text_dim']};font-size:0.88rem;">Ask Retina anything about your reports...</span>
  <span style="font-size:1rem;color:{COLORS['text_dim']};">→</span>
</div>""",
        unsafe_allow_html=True,
    )
