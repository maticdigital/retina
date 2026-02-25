"""Retina — Main Streamlit Application."""

from __future__ import annotations

import os
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from app.components.styles import COLORS, inject_css
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
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "page" not in st.session_state:
        st.session_state["page"] = "dashboard"

    # Auth gate
    if not st.session_state["authenticated"]:
        login.render()
        return

    # Icon sidebar
    _render_sidebar()

    # Quick Start panel (toggled by ? icon)
    if st.session_state.get("show_quick_start"):
        from app.components.quick_start import render_quick_start_panel
        render_quick_start_panel()

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

    # Footer
    _render_footer()


def _render_sidebar() -> None:
    """Render the narrow icon sidebar."""
    user = st.session_state.get("user", {})
    role = user.get("role", "analyst")
    current_page = st.session_state.get("page", "dashboard")

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
            st.markdown(
                f"<div class='sidebar-logo'>{svg_content}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='sidebar-logo' style='font-weight:700;font-size:1.2rem;color:#0A0A2E;'>R</div>",
                unsafe_allow_html=True,
            )

        st.markdown(
            f"<div style='height:0.5rem'></div>",
            unsafe_allow_html=True,
        )

        # Navigation icons
        if st.button(
            "🏠",
            key="nav_dashboard",
            help="Dashboard",
            use_container_width=True,
        ):
            st.session_state["page"] = "dashboard"
            st.rerun()

        if st.button(
            "➕",
            key="nav_new",
            help="New Analysis",
            use_container_width=True,
        ):
            st.session_state["page"] = "new_analysis"
            st.rerun()

        if role in ("owner", "admin"):
            if st.button(
                "⚙️",
                key="nav_admin",
                help="Admin",
                use_container_width=True,
            ):
                st.session_state["page"] = "admin"
                st.rerun()

        # Spacer — push remaining items to bottom
        st.markdown(
            "<div style='flex-grow:1;min-height:200px;'></div>",
            unsafe_allow_html=True,
        )

        # Quick Start / Help
        if st.button(
            "❓",
            key="nav_help",
            help="Quick Start Guide",
            use_container_width=True,
        ):
            st.session_state["show_quick_start"] = not st.session_state.get(
                "show_quick_start", False
            )
            st.rerun()

        # User avatar with popover dropdown
        name = user.get("name", "User")
        initials = "".join(w[0].upper() for w in name.split()[:2]) if name else "U"

        with st.popover(f"**{initials}**", use_container_width=True):
            st.markdown(
                f"<div style='font-weight:600;font-size:0.9rem;color:{COLORS['text']};'>"
                f"{name}</div>"
                f"<div style='font-size:0.78rem;color:{COLORS['text_muted']};margin-bottom:0.75rem;'>"
                f"{user.get('email', '')}</div>",
                unsafe_allow_html=True,
            )
            if st.button("Change Password", key="user_settings", use_container_width=True):
                st.session_state["page"] = "settings"
                st.rerun()
            if st.button("Sign Out", key="user_signout", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()


def _render_footer() -> None:
    """Render the page footer with Matic branding."""
    logo_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "assets",
        "Matic-Logo.svg",
    )
    logo_svg = ""
    if os.path.exists(logo_path):
        with open(logo_path) as f:
            logo_svg = f.read()

    st.markdown(
        f"<div class='retina-footer'>"
        f"<span>Powered by</span> {logo_svg}"
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_settings() -> None:
    """Render settings page with password change."""
    st.markdown(
        f"<h2 style='color:{COLORS['text']};margin-bottom:0.5rem;'>Settings</h2>",
        unsafe_allow_html=True,
    )

    if st.button("← Back to Dashboard"):
        st.session_state["page"] = "dashboard"
        st.rerun()

    st.markdown("---")
    render_change_password()


if __name__ == "__main__":
    main()
