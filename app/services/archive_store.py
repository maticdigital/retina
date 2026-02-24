"""Persistent archive state for projects.

Stores archived project IDs in a JSON file on disk.
This is a workaround because we can't ALTER TABLE on the hosted
Supabase instance without Dashboard / direct-SQL access.

When you gain DB access, run:
    ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS archived boolean DEFAULT false;
and replace this module with a simple column check.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

_STORE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "archived_projects.json"
_lock = threading.Lock()


def _ensure_dir() -> None:
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load() -> set[str]:
    if not _STORE_PATH.exists():
        return set()
    try:
        data = json.loads(_STORE_PATH.read_text())
        return set(data) if isinstance(data, list) else set()
    except (json.JSONDecodeError, OSError):
        return set()


def _save(ids: set[str]) -> None:
    _ensure_dir()
    _STORE_PATH.write_text(json.dumps(sorted(ids)))


def archive_project(project_id: str) -> None:
    """Mark a project as archived."""
    with _lock:
        ids = _load()
        ids.add(project_id)
        _save(ids)


def unarchive_project(project_id: str) -> None:
    """Remove archive flag from a project."""
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
