"""Admin panel — user management (owner/admin only)."""

from __future__ import annotations

import streamlit as st

from app.components.styles import metric_card
from app.services.auth import (
    deactivate_user,
    list_users,
    reactivate_user,
    reset_user_password,
    sign_up,
    update_user_role,
)


def render() -> None:
    """Render the admin panel."""
    user = st.session_state.get("user", {})
    role = user.get("role", "analyst")

    if role not in ("owner", "admin"):
        st.error("Access denied. Admin privileges required.")
        return

    st.markdown("### Admin Panel")
    st.markdown(
        "<p style='color: #8b92b3;'>Manage users and view system-wide data.</p>",
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(["Users", "Add User"])

    with tab1:
        _render_user_list(user)

    with tab2:
        _render_add_user(role)


def _render_user_list(current_user: dict) -> None:
    """Render the user management list."""
    users = list_users()

    # Summary
    total = len(users)
    active = sum(1 for u in users if u.get("is_active", True))
    owners = sum(1 for u in users if u.get("role") == "owner")
    admins = sum(1 for u in users if u.get("role") == "admin")

    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        st.markdown(metric_card(str(total), "Total Users"), unsafe_allow_html=True)
    with mc2:
        st.markdown(metric_card(str(active), "Active"), unsafe_allow_html=True)
    with mc3:
        st.markdown(metric_card(str(owners), "Owners"), unsafe_allow_html=True)
    with mc4:
        st.markdown(metric_card(str(admins), "Admins"), unsafe_allow_html=True)

    st.markdown("<div style='height: 1rem'></div>", unsafe_allow_html=True)

    # User table
    for u in users:
        uid = u["id"]
        is_self = uid == current_user.get("id")
        is_active = u.get("is_active", True)

        with st.container():
            c1, c2, c3, c4, c5 = st.columns([3, 2, 1.5, 1.5, 2])
            with c1:
                name_display = u.get("name", "Unknown")
                if is_self:
                    name_display += " (you)"
                status_dot = "🟢" if is_active else "🔴"
                st.markdown(
                    f"{status_dot} **{name_display}**<br/>"
                    f"<span style='color: #8b92b3; font-size: 0.8rem;'>{u.get('email', '')}</span>",
                    unsafe_allow_html=True,
                )
            with c2:
                role_display = u.get("role", "analyst").title()
                st.markdown(
                    f"<span style='color: #8b92b3;'>{role_display}</span>",
                    unsafe_allow_html=True,
                )
            with c3:
                if not is_self:
                    new_role = st.selectbox(
                        "Role",
                        ["analyst", "admin", "owner"],
                        index=["analyst", "admin", "owner"].index(u.get("role", "analyst")),
                        key=f"role_{uid}",
                        label_visibility="collapsed",
                    )
                    if new_role != u.get("role"):
                        if st.button("Save", key=f"save_role_{uid}"):
                            update_user_role(uid, new_role)
                            st.rerun()
            with c4:
                if not is_self:
                    if is_active:
                        if st.button("Deactivate", key=f"deact_{uid}"):
                            deactivate_user(uid)
                            st.rerun()
                    else:
                        if st.button("Reactivate", key=f"react_{uid}"):
                            reactivate_user(uid)
                            st.rerun()
            with c5:
                if not is_self:
                    with st.popover("Reset Password"):
                        new_pw = st.text_input(
                            "New password",
                            type="password",
                            key=f"pw_{uid}",
                        )
                        if st.button("Reset", key=f"reset_pw_{uid}"):
                            if new_pw and len(new_pw) >= 6:
                                try:
                                    reset_user_password(uid, new_pw)
                                    st.success("Password reset.")
                                except Exception as e:
                                    st.error(str(e))
                            else:
                                st.warning("Minimum 6 characters.")


def _render_add_user(admin_role: str) -> None:
    """Render the add user form."""
    st.markdown("#### Add New User")

    with st.form("add_user_form"):
        name = st.text_input("Full Name", placeholder="Jane Doe")
        email = st.text_input("Email", placeholder="jane@company.com")
        password = st.text_input("Temporary Password", type="password", placeholder="Min 6 characters")

        role_options = ["analyst", "admin"]
        if admin_role == "owner":
            role_options.append("owner")
        role = st.selectbox("Role", role_options)

        submitted = st.form_submit_button("Create User", type="primary")

        if submitted:
            if not name or not email or not password:
                st.error("All fields are required.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters.")
            else:
                try:
                    sign_up(email, password, name, role)
                    st.success(f"User **{name}** created successfully.")
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Failed to create user: {e}")
