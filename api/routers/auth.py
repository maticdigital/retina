"""Authentication endpoints — login, logout, current user."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, HTTPException
from gotrue.errors import AuthApiError

from api.deps import CurrentUser, get_supabase_anon, get_supabase

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Request / response models ─────────────────────────────────────────────────


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    access_token: str


class UserProfile(BaseModel):
    id: str
    email: str
    name: str
    role: str


class UpdateProfileRequest(BaseModel):
    name: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    found: bool
    detail: str


class ResetPasswordRequest(BaseModel):
    access_token: str
    new_password: str


# ── Routes ────────────────────────────────────────────────────────────────────


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    """Authenticate with email + password, return session token."""
    client = get_supabase_anon()
    try:
        resp = client.auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
    except AuthApiError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    except Exception as e:
        # Catch broader exceptions from Supabase client
        detail = str(e)
        if "Invalid login" in detail or "invalid" in detail.lower():
            raise HTTPException(status_code=401, detail=detail) from e
        raise HTTPException(status_code=500, detail=f"Auth error: {detail}") from e

    user = resp.user
    if not user:
        raise HTTPException(status_code=401, detail="Login failed — no user returned")

    session = resp.session
    if not session:
        raise HTTPException(status_code=401, detail="Login failed — no session returned")

    # Fetch profile from users table
    sb = get_supabase()
    profile_resp = sb.table("users").select("*").eq("id", str(user.id)).execute()
    if not profile_resp.data:
        raise HTTPException(
            status_code=401,
            detail="Account exists but no profile found. Contact an admin.",
        )

    profile = profile_resp.data[0]
    if not profile.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account has been deactivated")

    return LoginResponse(
        id=str(user.id),
        email=user.email or "",
        name=profile["name"],
        role=profile["role"],
        access_token=session.access_token,
    )


@router.post("/logout")
def logout(user: CurrentUser):
    """Sign out the current user. Client should discard the token."""
    # Supabase anon client sign-out is client-side.
    # The real work is the client discarding the token.
    # We can optionally invalidate via admin API:
    try:
        sb = get_supabase()
        sb.auth.admin.sign_out(user["access_token"])
    except Exception:
        pass  # Token invalidation is best-effort
    return {"detail": "Signed out"}


@router.get("/me", response_model=UserProfile)
def me(user: CurrentUser):
    """Return the authenticated user's profile."""
    return UserProfile(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        role=user["role"],
    )


@router.put("/me", response_model=UserProfile)
def update_profile(body: UpdateProfileRequest, user: CurrentUser):
    """Update the current user's name."""
    sb = get_supabase()
    resp = (
        sb.table("users")
        .update({"name": body.name})
        .eq("id", user["id"])
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to update profile")
    profile = resp.data[0]
    return UserProfile(
        id=profile["id"],
        email=profile["email"],
        name=profile["name"],
        role=profile["role"],
    )


@router.post("/change-password")
def change_password(body: ChangePasswordRequest, user: CurrentUser):
    """Change the current user's password.

    Validates by re-authenticating with the current password, then uses
    the admin API to set the new password.
    """
    # Verify current password by attempting a sign-in
    client = get_supabase_anon()
    try:
        client.auth.sign_in_with_password(
            {"email": user["email"], "password": body.current_password}
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    # Update password via admin API
    sb = get_supabase()
    try:
        sb.auth.admin.update_user_by_id(
            user["id"],
            {"password": body.new_password},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update password: {e}"
        )

    return {"detail": "Password changed successfully"}


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(body: ForgotPasswordRequest):
    """Request a password reset email.

    If the email exists in the users table, sends a Supabase recovery
    email.  If not, returns a message directing the user to contact
    matic@maticdigital.com.  We intentionally reveal whether the email
    exists since this is an internal analyst tool, not a public app.
    """
    sb = get_supabase()

    # Check if email exists in our users table
    resp = sb.table("users").select("id").eq("email", body.email).execute()
    if not resp.data:
        return ForgotPasswordResponse(
            found=False,
            detail="No account found for that email. Please contact matic@maticdigital.com for assistance.",
        )

    # Send recovery email via Supabase Auth
    try:
        client = get_supabase_anon()
        client.auth.reset_password_for_email(body.email)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to send reset email: {e}"
        ) from e

    return ForgotPasswordResponse(
        found=True,
        detail="Password reset link sent. Check your email.",
    )


@router.post("/reset-password")
def reset_password(body: ResetPasswordRequest):
    """Set a new password using a recovery access token.

    The frontend extracts the access_token from the Supabase redirect
    hash fragment and sends it here.  We verify the token by fetching
    the user, then update the password via the admin API.
    """
    # Verify the recovery token by fetching the user it belongs to
    sb = get_supabase()
    try:
        user_resp = sb.auth.get_user(body.access_token)
        user = user_resp.user
        if not user:
            raise ValueError("No user for token")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    # Update password via admin API
    try:
        sb.auth.admin.update_user_by_id(
            str(user.id),
            {"password": body.new_password},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update password: {e}"
        ) from e

    return {"detail": "Password updated successfully"}
