"""Dashboard page — project list view."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from app.components.styles import COLORS, metric_card, status_badge
from app.services.projects import delete_project, duplicate_project, list_projects


def render() -> None:
    """Render the dashboard/project list."""
    user = st.session_state.get("user", {})
    user_id = user.get("id", "")
    user_role = user.get("role", "analyst")

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### Welcome back, {user.get('name', 'User')}")
    with col2:
        if st.button("+ New Analysis", type="primary", use_container_width=True):
            st.session_state["page"] = "new_analysis"
            st.rerun()

    st.markdown("---")

    # Fetch projects
    projects = list_projects(user_id, user_role)

    # Summary metrics
    total = len(projects)
    complete = sum(1 for p in projects if p["status"] == "complete")
    in_progress = sum(1 for p in projects if p["status"] == "in_progress")
    drafts = sum(1 for p in projects if p["status"] == "draft")

    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        st.markdown(metric_card(str(total), "Total Projects"), unsafe_allow_html=True)
    with mc2:
        st.markdown(metric_card(str(complete), "Complete"), unsafe_allow_html=True)
    with mc3:
        st.markdown(metric_card(str(in_progress), "In Progress"), unsafe_allow_html=True)
    with mc4:
        st.markdown(metric_card(str(drafts), "Drafts"), unsafe_allow_html=True)

    st.markdown("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)

    # Search and filter
    fc1, fc2, fc3 = st.columns([3, 1, 1])
    with fc1:
        search = st.text_input("Search projects", placeholder="Search by name or URL...", label_visibility="collapsed")
    with fc2:
        sort_by = st.selectbox("Sort", ["Newest", "Oldest", "Name A-Z", "Name Z-A"], label_visibility="collapsed")
    with fc3:
        filter_status = st.selectbox("Status", ["All", "Draft", "In Progress", "Complete"], label_visibility="collapsed")

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
        filtered.sort(key=lambda p: p["updated_at"], reverse=True)
    elif sort_by == "Oldest":
        filtered.sort(key=lambda p: p["updated_at"])
    elif sort_by == "Name A-Z":
        filtered.sort(key=lambda p: p["name"].lower())
    elif sort_by == "Name Z-A":
        filtered.sort(key=lambda p: p["name"].lower(), reverse=True)

    # Project list
    if not filtered:
        st.markdown(
            f"<div style='text-align: center; padding: 3rem; color: {COLORS['text_muted']};'>"
            "<p style='font-size: 1.2rem;'>No projects found</p>"
            "<p>Create your first analysis to get started.</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    for project in filtered:
        _render_project_row(project, user_id, user_role)


def _render_project_row(project: dict, user_id: str, user_role: str) -> None:
    """Render a single project row."""
    pid = project["id"]
    badge = status_badge(project["status"])

    # Parse date
    try:
        updated = datetime.fromisoformat(project["updated_at"].replace("Z", "+00:00"))
        date_str = updated.strftime("%b %d, %Y")
    except (ValueError, KeyError):
        date_str = ""

    competitors = project.get("competitor_urls", [])
    comp_count = len(competitors) if competitors else 0

    # Creator info
    creator_name = ""
    if project.get("users"):
        creator_name = project["users"].get("name", "")

    with st.container():
        c1, c2, c3, c4, c5 = st.columns([4, 2, 1.5, 1.5, 2])
        with c1:
            st.markdown(
                f"**{project['name']}**<br/>"
                f"<span style='color: {COLORS['text_muted']}; font-size: 0.8rem;'>{project['primary_url']}</span>",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(f"<span style='color: {COLORS['text_muted']}; font-size: 0.85rem;'>{date_str}</span>", unsafe_allow_html=True)
        with c3:
            st.markdown(badge, unsafe_allow_html=True)
        with c4:
            st.markdown(
                f"<span style='color: {COLORS['text_muted']}; font-size: 0.85rem;'>{comp_count} competitor{'s' if comp_count != 1 else ''}</span>",
                unsafe_allow_html=True,
            )
        with c5:
            bc1, bc2, bc3 = st.columns(3)
            with bc1:
                if st.button("Open", key=f"open_{pid}", use_container_width=True):
                    st.session_state["page"] = "project_detail"
                    st.session_state["current_project_id"] = pid
                    st.rerun()
            with bc2:
                if st.button("Copy", key=f"dup_{pid}", use_container_width=True):
                    try:
                        duplicate_project(pid, user_id)
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
            with bc3:
                can_delete = user_role in ("owner", "admin") or project.get("created_by") == user_id
                if can_delete:
                    if st.button("Del", key=f"del_{pid}", use_container_width=True):
                        delete_project(pid)
                        st.rerun()
