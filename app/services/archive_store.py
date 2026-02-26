"""Persistent archive state for projects.

Uses a dedicated `archived` boolean column on the projects table.
All operations go directly to the database — no in-memory cache.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def _get_supabase():
    """Get Supabase client - import here to avoid circular imports."""
    try:
        from api.deps import get_supabase
        return get_supabase()
    except ImportError:
        logger.error("Could not import Supabase client")
        return None


def archive_project(project_id: str) -> None:
    """Mark a project as archived."""
    sb = _get_supabase()
    if sb:
        sb.table("projects").update({"archived": True}).eq("id", project_id).execute()
        logger.info("Project %s archived", project_id)


def unarchive_project(project_id: str) -> None:
    """Remove archive flag from a project."""
    sb = _get_supabase()
    if sb:
        sb.table("projects").update({"archived": False}).eq("id", project_id).execute()
        logger.info("Project %s unarchived", project_id)


def is_archived(project_id: str) -> bool:
    """Check if a project is archived."""
    sb = _get_supabase()
    if not sb:
        return False
    resp = sb.table("projects").select("archived").eq("id", project_id).limit(1).execute()
    if resp.data:
        return bool(resp.data[0].get("archived", False))
    return False


def get_archived_ids() -> set[str]:
    """Return all archived project IDs."""
    sb = _get_supabase()
    if not sb:
        return set()
    resp = sb.table("projects").select("id").eq("archived", True).execute()
    return {row["id"] for row in resp.data or []}
