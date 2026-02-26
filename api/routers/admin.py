"""Admin endpoints — user management (owner/admin only)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, HTTPException

from api.deps import CurrentUser, get_supabase

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Helpers ──────────────────────────────────────────────────────────────────


def _require_admin(user: dict[str, Any]) -> None:
    if user["role"] not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Admin access required")


# ── Models ───────────────────────────────────────────────────────────────────


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str
    is_active: bool
    created_at: str


class InviteUserRequest(BaseModel):
    email: EmailStr
    name: str
    role: str = "analyst"
    password: str


class UpdateUserRequest(BaseModel):
    name: str | None = None
    role: str | None = None
    is_active: bool | None = None


# ── Routes ───────────────────────────────────────────────────────────────────


@router.get("/users", response_model=list[UserOut])
def list_users(user: CurrentUser):
    """Return all users (admin/owner only)."""
    _require_admin(user)
    sb = get_supabase()
    resp = sb.table("users").select("*").order("created_at", desc=True).execute()
    return resp.data or []


@router.post("/users", response_model=UserOut, status_code=201)
def invite_user(body: InviteUserRequest, user: CurrentUser):
    """Create a new user account and send invitation email (admin/owner only).

    Creates an auth account in Supabase Auth with a password, then sends
    an invitation email so the user knows they have an account. Also
    upserts a profile row in the users table.
    """
    _require_admin(user)
    sb = get_supabase()

    # Create auth account via admin API
    try:
        auth_resp = sb.auth.admin.create_user({
            "email": body.email,
            "password": body.password,
            "email_confirm": True,
            "user_metadata": {"name": body.name, "role": body.role},
        })
    except Exception as e:
        detail = str(e)
        if "already been registered" in detail.lower() or "already exists" in detail.lower():
            raise HTTPException(status_code=409, detail="A user with this email already exists")
        raise HTTPException(status_code=500, detail=f"Failed to create auth user: {detail}")

    auth_user = auth_resp.user
    if not auth_user:
        raise HTTPException(status_code=500, detail="Auth user creation returned no user")

    # Upsert profile row (trigger may have already created it)
    try:
        profile_resp = (
            sb.table("users")
            .upsert({
                "id": str(auth_user.id),
                "email": body.email,
                "name": body.name,
                "role": body.role,
                "is_active": True,
            })
            .execute()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create profile: {e}")

    if not profile_resp.data:
        raise HTTPException(status_code=500, detail="Profile insert returned no data")

    # Send invitation email via Supabase Auth (best-effort, don't fail if email fails)
    try:
        sb.auth.admin.invite_user_by_email(body.email)
    except Exception:
        pass  # Account is created; email delivery is best-effort

    return profile_resp.data[0]


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: str, body: UpdateUserRequest, user: CurrentUser):
    """Update a user's profile (admin/owner only)."""
    _require_admin(user)
    sb = get_supabase()

    updates: dict[str, Any] = {}
    if body.name is not None:
        updates["name"] = body.name
    if body.role is not None:
        updates["role"] = body.role
    if body.is_active is not None:
        updates["is_active"] = body.is_active

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    resp = sb.table("users").update(updates).eq("id", user_id).execute()
    if not resp.data:
        raise HTTPException(status_code=404, detail="User not found")

    return resp.data[0]


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: str, user: CurrentUser):
    """Delete a user account (admin/owner only).

    Removes the user from both the users profile table and Supabase Auth.
    Admins cannot delete themselves.
    """
    _require_admin(user)

    if user_id == user["id"]:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")

    sb = get_supabase()

    # Delete from users profile table first
    sb.table("users").delete().eq("id", user_id).execute()

    # Delete from Supabase Auth
    try:
        sb.auth.admin.delete_user(user_id)
    except Exception as e:
        detail = str(e)
        if "not found" in detail.lower():
            pass  # Auth user already gone, that's fine
        else:
            raise HTTPException(status_code=500, detail=f"Failed to delete auth user: {detail}")
