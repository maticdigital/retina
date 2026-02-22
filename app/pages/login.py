"""Login page."""

from __future__ import annotations

import streamlit as st

from app.components.styles import COLORS
from app.services.auth import sign_in


def render() -> None:
    """Render the login page."""
    # Center the login form
    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
        st.markdown("<div style='height: 60px'></div>", unsafe_allow_html=True)

        # Logo
        st.markdown(
            f"<div style='text-align: center; margin-bottom: 2rem;'>"
            f"<h1 style='font-size: 2rem; font-weight: 700; letter-spacing: 0.1em; "
            f"color: {COLORS['text']};'>RETINA</h1>"
            f"<p style='color: {COLORS['text_muted']}; font-size: 0.9rem;'>"
            f"Website Intelligence Platform</p>"
            f"</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            "<div class='retina-card'>",
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            st.markdown("##### Sign In")
            email = st.text_input("Email", placeholder="you@company.com")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")

            if submitted:
                if not email or not password:
                    st.error("Please enter both email and password.")
                else:
                    try:
                        user = sign_in(email, password)
                        st.session_state["user"] = user
                        st.session_state["authenticated"] = True
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error(f"Login failed: {e}")

        st.markdown("</div>", unsafe_allow_html=True)


def render_change_password() -> None:
    """Render password change form (in settings or profile)."""
    st.markdown("#### Change Password")
    with st.form("change_password_form"):
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Update Password", type="primary")

        if submitted:
            if not new_password:
                st.error("Please enter a new password.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                try:
                    from app.services.auth import update_password
                    user = st.session_state.get("user", {})
                    update_password(user["id"], new_password)
                    st.success("Password updated successfully.")
                except Exception as e:
                    st.error(f"Failed to update password: {e}")
