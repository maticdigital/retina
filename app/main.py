"""Retina — Main Streamlit Application."""

from __future__ import annotations

import os
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from app.components.styles import inject_css
from app.pages import admin, dashboard, login, new_analysis, project_detail
from app.pages.login import render_change_password

# Page config
st.set_page_config(
    page_title="Retina — Website Intelligence",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom CSS
st.markdown(inject_css(), unsafe_allow_html=True)


def main() -> None:
    """Main app router."""
    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "page" not in st.session_state:
        st.session_state["page"] = "dashboard"

    # Auth gate
    if not st.session_state["authenticated"]:
        login.render()
        return

    # Sidebar navigation
    _render_sidebar()

    # Page routing
    page = st.session_state.get("page", "dashboard")
    if page == "dashboard":
        dashboard.render()
    elif page == "new_analysis":
        new_analysis.render()
    elif page == "project_detail":
        project_detail.render()
    elif page == "admin":
        admin.render()
    elif page == "settings":
        _render_settings()
    else:
        dashboard.render()


def _render_sidebar() -> None:
    """Render the sidebar with navigation."""
    user = st.session_state.get("user", {})
    role = user.get("role", "analyst")

    with st.sidebar:
        # Logo
        logo_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "assets",
            "Matic-Retina.svg",
        )
        if os.path.exists(logo_path):
            with open(logo_path) as f:
                svg_content = f.read()
            # Recolor SVG for dark background
            svg_content = svg_content.replace('fill="#000227"', 'fill="#FFFFFF"')
            st.markdown(
                f"<div class='sidebar-logo'>{svg_content}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div style='text-align: center; padding: 1rem 0 1.5rem;'>"
                "<h2 style='letter-spacing: 0.1em; margin: 0;'>RETINA</h2>"
                "</div>",
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # Nav buttons
        if st.button("📊  Dashboard", use_container_width=True, key="nav_dashboard"):
            st.session_state["page"] = "dashboard"
            st.rerun()

        if st.button("➕  New Analysis", use_container_width=True, key="nav_new"):
            st.session_state["page"] = "new_analysis"
            st.rerun()

        if role in ("owner", "admin"):
            if st.button("⚙️  Admin", use_container_width=True, key="nav_admin"):
                st.session_state["page"] = "admin"
                st.rerun()

        # Spacer
        st.markdown("<div style='height: 2rem'></div>", unsafe_allow_html=True)
        st.markdown("---")

        # User info
        st.markdown(
            f"<div style='padding: 0.5rem; color: #8b92b3; font-size: 0.85rem;'>"
            f"<strong>{user.get('name', 'User')}</strong><br/>"
            f"{user.get('email', '')}<br/>"
            f"<span style='text-transform: capitalize;'>{role}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Settings", use_container_width=True, key="nav_settings"):
                st.session_state["page"] = "settings"
                st.rerun()
        with c2:
            if st.button("Sign Out", use_container_width=True, key="nav_signout"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()


def _render_settings() -> None:
    """Render settings page with password change."""
    st.markdown("### Settings")

    c1, c2 = st.columns([0.5, 3])
    with c1:
        if st.button("Back"):
            st.session_state["page"] = "dashboard"
            st.rerun()

    st.markdown("---")
    render_change_password()


if __name__ == "__main__":
    main()
