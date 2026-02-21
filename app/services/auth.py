"""Authentication service using Supabase Auth."""

from __future__ import annotations

from typing import Any

from gotrue.errors import AuthApiError

from app.services.supabase_client import get_supabase, get_supabase_anon


def sign_in(email: str, password: str) -> dict[str, Any]:
    """Sign in with email/password. Returns user data or raises."""
    client = get_supabase_anon()
    try:
        resp = client.auth.sign_in_with_password({"email": email, "password": password})
    except AuthApiError as e:
        raise ValueError(str(e)) from e

    user = resp.user
    if not user:
        raise ValueError("Login failed — no user returned.")

    # Fetch profile from users table
    profile = get_user_profile(str(user.id))
    if not profile:
        raise ValueError("Account exists but no profile found. Contact an admin.")
    if not profile.get("is_active", True):
        raise ValueError("Account has been deactivated. Contact an admin.")

    return {
        "id": str(user.id),
        "email": user.email,
        "name": profile["name"],
        "role": profile["role"],
        "access_token": resp.session.access_token if resp.session else None,
    }


def sign_up(email: str, password: str, name: str, role: str = "analyst") -> dict[str, Any]:
    """Create a new user via Supabase Auth + profile row."""
    sb = get_supabase()
    try:
        resp = sb.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {"name": name, "role": role},
        })
    except AuthApiError as e:
        raise ValueError(str(e)) from e

    user = resp.user
    if not user:
        raise ValueError("Signup failed — no user returned.")

    return {"id": str(user.id), "email": email, "name": name, "role": role}


def get_user_profile(user_id: str) -> dict[str, Any] | None:
    """Fetch a user profile from the users table."""
    sb = get_supabase()
    resp = sb.table("users").select("*").eq("id", user_id).execute()
    if resp.data:
        return resp.data[0]
    return None


def update_password(user_id: str, new_password: str) -> None:
    """Update a user's password via admin API."""
    sb = get_supabase()
    sb.auth.admin.update_user_by_id(user_id, {"password": new_password})


def list_users() -> list[dict[str, Any]]:
    """List all users (admin function)."""
    sb = get_supabase()
    resp = sb.table("users").select("*").order("created_at", desc=False).execute()
    return resp.data or []


def update_user_role(user_id: str, role: str) -> None:
    """Update a user's role."""
    sb = get_supabase()
    sb.table("users").update({"role": role}).eq("id", user_id).execute()


def deactivate_user(user_id: str) -> None:
    """Deactivate a user account."""
    sb = get_supabase()
    sb.table("users").update({"is_active": False}).eq("id", user_id).execute()


def reactivate_user(user_id: str) -> None:
    """Reactivate a user account."""
    sb = get_supabase()
    sb.table("users").update({"is_active": True}).eq("id", user_id).execute()


def reset_user_password(user_id: str, new_password: str) -> None:
    """Admin reset of a user's password."""
    sb = get_supabase()
    sb.auth.admin.update_user_by_id(user_id, {"password": new_password})
