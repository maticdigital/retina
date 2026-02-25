"""PDF export endpoints.

Uses an in-memory job store for status tracking. PDF URLs are also
persisted to the reports table for long-term storage.
"""

from __future__ import annotations

import logging
import os
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from threading import Lock

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from api.deps import CurrentUser, get_supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["export"])


# ── In-memory job store ───────────────────────────────────────────────────────

_jobs: dict[str, dict] = {}  # job_id → {project_id, status, download_url, error}
_project_jobs: dict[str, str] = {}  # project_id → latest job_id
_lock = Lock()


def _set_job(job_id: str, project_id: str, **fields):
    """Create or update a job record."""
    with _lock:
        if job_id not in _jobs:
            _jobs[job_id] = {"project_id": project_id}
        _jobs[job_id].update(fields)
        _project_jobs[project_id] = job_id


def _get_latest_job(project_id: str) -> dict | None:
    """Get the latest job for a project."""
    with _lock:
        job_id = _project_jobs.get(project_id)
        if job_id and job_id in _jobs:
            return {**_jobs[job_id], "job_id": job_id}
    return None


# ── Response models ───────────────────────────────────────────────────────────


class ExportJobResponse(BaseModel):
    job_id: str
    status: str


class ExportStatusResponse(BaseModel):
    status: str  # none | pending | generating | complete | error
    download_url: str | None = None
    error: str | None = None


# ── Background task ───────────────────────────────────────────────────────────


def _run_export(project_id: str, job_id: str):
    """Background task: build PDF and upload to storage."""
    try:
        _set_job(job_id, project_id, status="generating")

        # Ensure src is on path for retina imports
        src_path = os.path.join(os.path.dirname(__file__), "..", "..", "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        # Ensure WeasyPrint can find native libs
        os.environ.setdefault("DYLD_LIBRARY_PATH", "/opt/homebrew/lib")

        from api.services.pdf_adapter import build_analysis_run
        from retina.report.renderer import render_pdf
        from app.services.storage import upload_report_pdf

        # 1. Build AnalysisRun from Supabase data
        logger.info("Export %s: building AnalysisRun", job_id[:8])
        analysis_run = build_analysis_run(project_id)

        # 2. Render PDF
        logger.info("Export %s: rendering PDF", job_id[:8])
        assets_dir = os.path.join(os.path.dirname(__file__), "..", "..", "assets")
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = tmp.name

        render_pdf(analysis_run, tmp_path, assets_dir=assets_dir)
        pdf_size = os.path.getsize(tmp_path)

        # 3. Upload to Supabase Storage
        logger.info("Export %s: uploading PDF (%d bytes)", job_id[:8], pdf_size)
        download_url = upload_report_pdf(tmp_path, project_id)

        # 4. Clean up temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

        # 5. Update in-memory job status
        _set_job(job_id, project_id, status="complete", download_url=download_url)

        # 6. Also store PDF URL in the reports table for persistence
        try:
            sb = get_supabase()
            reports_resp = (
                sb.table("reports")
                .select("id")
                .eq("project_id", project_id)
                .order("generated_at", desc=True)
                .limit(1)
                .execute()
            )
            if reports_resp.data:
                sb.table("reports").update({"pdf_url": download_url}).eq(
                    "id", reports_resp.data[0]["id"]
                ).execute()
        except Exception as e:
            logger.warning("Could not update reports table with pdf_url: %s", e)

        logger.info("Export %s: complete → %s", job_id[:8], download_url)

    except Exception as e:
        logger.exception("Export %s failed: %s", job_id[:8], e)
        _set_job(job_id, project_id, status="error", error=str(e)[:500])


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/{project_id}/export/pdf", response_model=ExportJobResponse)
async def export_pdf(
    project_id: str,
    background_tasks: BackgroundTasks,
    user: CurrentUser,
):
    """Start a PDF export job. Returns immediately with a job ID."""
    sb = get_supabase()

    # Verify project exists
    proj = sb.table("projects").select("id").eq("id", project_id).execute()
    if not proj.data:
        raise HTTPException(404, "Project not found")

    # Create job
    job_id = str(uuid.uuid4())
    _set_job(job_id, project_id, status="pending")

    # Start background task
    background_tasks.add_task(_run_export, project_id, job_id)

    return ExportJobResponse(job_id=job_id, status="pending")


@router.get("/{project_id}/export/status", response_model=ExportStatusResponse)
async def export_status(
    project_id: str,
    user: CurrentUser,
):
    """Get the latest export job status for a project."""
    job = _get_latest_job(project_id)

    if not job:
        return ExportStatusResponse(status="none")

    return ExportStatusResponse(
        status=job.get("status", "pending"),
        download_url=job.get("download_url"),
        error=job.get("error"),
    )
