"""Persistent archive state for projects.

Uses Supabase database to store archived project status.
This replaces the file-based storage which doesn't work in Vercel's read-only environment.
"""

from __future__ import annotations

import logging
import threading

logger = logging.getLogger(__name__)
_lock = threading.Lock()

# In-memory cache for archived project IDs
_archived_cache: set[str] | None = None


def _get_supabase():
    """Get Supabase client - import here to avoid circular imports."""
    try:
        from api.deps import get_supabase
        return get_supabase()
    except ImportError:
        logger.error("Could not import Supabase client")
        return None


def _load() -> set[str]:
    """Load archived project IDs from database or cache."""
    global _archived_cache
    
    if _archived_cache is not None:
        return _archived_cache
    
    sb = _get_supabase()
    if not sb:
        logger.warning("No Supabase client available, using empty archive set")
        _archived_cache = set()
        return _archived_cache
    
    try:
        # Try to get archived status from a metadata table or use project status
        resp = sb.table("projects").select("id").eq("status", "archived").execute()
        archived_ids = {row["id"] for row in resp.data or []}
        _archived_cache = archived_ids
        return archived_ids
    except Exception as e:
        logger.warning("Failed to load archived projects from database: %s", e)
        _archived_cache = set()
        return _archived_cache


def _save(ids: set[str]) -> None:
    """Save archived project IDs - update cache only in Vercel environment."""
    global _archived_cache
    _archived_cache = ids.copy()


def archive_project(project_id: str) -> None:
    """Mark a project as archived by updating database status."""
    sb = _get_supabase()
    if sb:
        try:
            sb.table("projects").update({"status": "archived"}).eq("id", project_id).execute()
            logger.info("Project %s archived in database", project_id)
        except Exception as e:
            logger.error("Failed to archive project %s in database: %s", project_id, e)
    
    # Update cache
    with _lock:
        ids = _load()
        ids.add(project_id)
        _save(ids)


def unarchive_project(project_id: str) -> None:
    """Remove archive flag from a project by updating database status."""
    sb = _get_supabase()
    if sb:
        try:
            sb.table("projects").update({"status": "active"}).eq("id", project_id).execute()
            logger.info("Project %s unarchived in database", project_id)
        except Exception as e:
            logger.error("Failed to unarchive project %s in database: %s", project_id, e)
    
    # Update cache
    with _lock:
        ids = _load()
        ids.discard(project_id)
        _save(ids)


def is_archived(project_id: str) -> bool:
    """Check if a project is archived."""
    with _lock:
        return project_id in _load()


def get_archived_ids() -> set[str]:
    """Return all archived project IDs."""
    with _lock:
        return _load()
