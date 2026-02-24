"""Shared dependencies for the FastAPI app — Supabase clients & auth helpers."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Annotated, Any

from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client, create_client

load_dotenv()

# ── Supabase clients ──────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def get_supabase() -> Client:
    """Service-role client for server-side operations (bypasses RLS)."""
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    return create_client(url, key)


def get_supabase_anon() -> Client:
    """Anon client for auth flows."""
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_ANON_KEY", "")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")
    return create_client(url, key)


# ── Auth dependency ───────────────────────────────────────────────────────────

_bearer = HTTPBearer()


def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> dict[str, Any]:
    """
    Validate the Supabase access token and return the user profile.

    Uses supabase.auth.get_user(token) which calls Supabase's GoTrue
    to verify the JWT and return the authenticated user.
    """
    sb = get_supabase()
    token = creds.credentials

    # Step 1: Verify token with Supabase Auth
    try:
        auth_response = sb.auth.get_user(token)
        auth_user = auth_response.user
        if not auth_user:
            raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {e}") from e

    user_id = str(auth_user.id)

    # Step 2: Fetch user profile from users table
    resp = sb.table("users").select("*").eq("id", user_id).execute()
    if not resp.data:
        raise HTTPException(status_code=401, detail="User profile not found")

    profile = resp.data[0]
    if not profile.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account deactivated")

    return {
        "id": profile["id"],
        "email": profile["email"],
        "name": profile["name"],
        "role": profile["role"],
        "access_token": token,
    }


# Type alias for convenience in route signatures
CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]
