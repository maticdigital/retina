"""Project CRUD endpoints."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel
from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File

from api.deps import CurrentUser, get_supabase
from app.services.pipeline_status import create_run, get_run
from app.services.projects import recalculate_scores
from app.services.archive_store import (
    archive_project as _archive,
    unarchive_project as _unarchive,
    is_archived,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])


# ── Response models ───────────────────────────────────────────────────────────


class ProjectOut(BaseModel):
    id: str
    name: str
    primary_url: str
    competitor_urls: list[str]
    status: str
    created_by: str | None = None
    created_at: str
    updated_at: str
    archived: bool = False
    screenshot_url: str | None = None
    retina_score: float | None = None


class ProjectDetail(ProjectOut):
    """Single project with optional scores / report data."""
    project_data: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []
    analyst_scores: list[dict[str, Any]] = []


class CreateProjectRequest(BaseModel):
    name: str
    primary_url: str
    competitor_urls: list[str] = []


class LensScore(BaseModel):
    lens_id: str
    lens_name: str
    score: float | None = None
    max_score: float = 20.0


class CompetitorSummary(BaseModel):
    url: str
    retina_score: float | None = None


class RecommendationQuadrant(BaseModel):
    quadrant: str
    items: list[Any] = []


class ProjectSummary(BaseModel):
    id: str
    name: str
    primary_url: str
    status: str
    screenshot_url: str | None = None
    retina_score: float | None = None
    lens_scores: list[LensScore] = []
    tech_stack: dict[str, list[str]] | None = None
    competitors: list[CompetitorSummary] = []
    recommendations: list[RecommendationQuadrant] = []


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get("", response_model=list[ProjectOut])
def list_projects(user: CurrentUser, include_archived: bool = False):
    """Return all projects visible to the current user."""
    sb = get_supabase()
    query = sb.table("projects").select("*")
    if user["role"] == "analyst":
        query = query.eq("created_by", user["id"])
    resp = query.order("updated_at", desc=True).execute()
    rows = resp.data or []

    # Fetch screenshot paths for all projects in one query
    project_ids = [r["id"] for r in rows]
    if project_ids:
        pd_resp = (
            sb.table("project_data")
            .select("project_id, screenshot_paths")
            .in_("project_id", project_ids)
            .execute()
        )
        screenshot_map = {}
        for pd in (pd_resp.data or []):
            sp = pd.get("screenshot_paths") or {}
            if isinstance(sp, dict):
                url = sp.get("viewport") or sp.get("full_page") or sp.get("desktop") or sp.get("mobile")
            elif isinstance(sp, str) and sp:
                url = sp
            else:
                url = None
            if url:
                screenshot_map[pd["project_id"]] = url
    else:
        screenshot_map = {}

    # Fetch latest retina_score from reports table
    score_map: dict[str, float] = {}
    if project_ids:
        rpt_resp = (
            sb.table("reports")
            .select("project_id, retina_score")
            .in_("project_id", project_ids)
            .order("generated_at", desc=True)
            .execute()
        )
        for rpt in (rpt_resp.data or []):
            pid = rpt["project_id"]
            if pid not in score_map and rpt.get("retina_score") is not None:
                score_map[pid] = rpt["retina_score"]

    for row in rows:
        row["screenshot_url"] = screenshot_map.get(row["id"])
        row["retina_score"] = score_map.get(row["id"])

    if not include_archived:
        rows = [r for r in rows if not r.get("archived", False)]

    return rows


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(
    body: CreateProjectRequest,
    user: CurrentUser,
):
    """Create a new project and immediately trigger the analysis pipeline."""
    sb = get_supabase()
    resp = (
        sb.table("projects")
        .insert({
            "name": body.name,
            "primary_url": body.primary_url,
            "competitor_urls": body.competitor_urls,
            "status": "draft",
            "created_by": user["id"],
        })
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create project")

    project = resp.data[0]
    project_id = project["id"]

    # Create pipeline status tracker and launch background pipeline
    create_run(project_id)
    import asyncio
    asyncio.ensure_future(
        _run_pipeline_background_async(project_id, body.primary_url, body.competitor_urls)
    )

    return project


@router.patch("/{project_id}/archive")
def archive_project(project_id: str, user: CurrentUser):
    """Archive a project (soft-delete)."""
    sb = get_supabase()
    proj_resp = sb.table("projects").select("id, created_by").eq("id", project_id).execute()
    if not proj_resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    project = proj_resp.data[0]
    if user["role"] == "analyst" and project["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    _archive(project_id)
    return {"ok": True}


@router.patch("/{project_id}/unarchive")
def unarchive_project(project_id: str, user: CurrentUser):
    """Unarchive a previously archived project."""
    sb = get_supabase()
    proj_resp = sb.table("projects").select("id, created_by").eq("id", project_id).execute()
    if not proj_resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    project = proj_resp.data[0]
    if user["role"] == "analyst" and project["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    _unarchive(project_id)
    return {"ok": True}


@router.delete("/{project_id}", status_code=200)
def delete_project(project_id: str, user: CurrentUser):
    """Permanently delete a project. Must be archived first."""
    sb = get_supabase()
    proj_resp = sb.table("projects").select("id, created_by").eq("id", project_id).execute()
    if not proj_resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    project = proj_resp.data[0]
    if user["role"] == "analyst" and project["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    if not is_archived(project_id):
        raise HTTPException(status_code=400, detail="Project must be archived before deletion")
    # Delete from Supabase (cascades to project_data, reports, etc.)
    sb.table("projects").delete().eq("id", project_id).execute()
    _unarchive(project_id)  # Clean up archive store
    return {"ok": True}


@router.post("/{project_id}/recommendations/generate")
def generate_recommendations_endpoint(
    project_id: str,
    user: CurrentUser,
    background_tasks: BackgroundTasks,
):
    """Generate AI recommendations for a project."""
    sb = get_supabase()
    proj_resp = sb.table("projects").select("id, created_by").eq("id", project_id).execute()
    if not proj_resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    project = proj_resp.data[0]
    if user["role"] == "analyst" and project["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Run in background so it doesn't block
    background_tasks.add_task(_generate_recs_background, project_id)
    return {"ok": True, "message": "Generating recommendations..."}


class UpdateRecommendationsRequest(BaseModel):
    """Quadrant data keyed by quadrant ID."""
    no_brainers: list[dict[str, Any]] = []
    quick_wins: list[dict[str, Any]] = []
    growth_moves: list[dict[str, Any]] = []
    transformational: list[dict[str, Any]] = []


@router.patch("/{project_id}/recommendations")
def update_recommendations(project_id: str, body: UpdateRecommendationsRequest, user: CurrentUser):
    """Save edited recommendations to the report's quadrant_data."""
    sb = get_supabase()
    proj_resp = sb.table("projects").select("id, created_by").eq("id", project_id).execute()
    if not proj_resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    project = proj_resp.data[0]
    if user["role"] == "analyst" and project["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    quadrant_data = {
        "no_brainers": body.no_brainers,
        "quick_wins": body.quick_wins,
        "growth_moves": body.growth_moves,
        "transformational": body.transformational,
    }

    # Update the latest report's quadrant_data
    reports_resp = (
        sb.table("reports").select("id").eq("project_id", project_id)
        .order("generated_at", desc=True).limit(1).execute()
    )
    if reports_resp.data:
        sb.table("reports").update({"quadrant_data": quadrant_data}).eq(
            "id", reports_resp.data[0]["id"]
        ).execute()
    else:
        # Create a minimal report
        sb.table("reports").insert({
            "project_id": project_id,
            "retina_score": 0,
            "ai_analysis": {},
            "quadrant_data": quadrant_data,
        }).execute()

    return {"ok": True}


def _generate_recs_background(project_id: str) -> None:
    """Generate recommendations in background thread."""
    from app.services.recommendations import generate_recommendations

    try:
        # Recalculate scores first so recommendations see correct totals
        recalculate_scores(project_id)
        generate_recommendations(project_id)
        logger.info("Recommendations generated for project %s", project_id)
    except Exception:
        logger.exception("Recommendation generation failed for project %s", project_id)


async def _run_pipeline_background_async(
    project_id: str, primary_url: str, competitor_urls: list[str]
) -> None:
    """Run the analysis pipeline as an async task on the main event loop.

    Using async instead of sync-in-thread because Chromium subprocesses
    crash ("Target crashed") when launched from background thread contexts.
    Running on the main event loop avoids this issue.
    """
    from app.services.pipeline import run_analysis

    try:
        await run_analysis(project_id, primary_url, competitor_urls)
    except Exception:
        logger.exception("Background pipeline failed for project %s", project_id)


def _run_pipeline_background(
    project_id: str, primary_url: str, competitor_urls: list[str]
) -> None:
    """Run the analysis pipeline in a background thread (legacy)."""
    from app.services.pipeline import run_analysis_sync

    try:
        run_analysis_sync(project_id, primary_url, competitor_urls)
    except Exception:
        logger.exception("Background pipeline failed for project %s", project_id)


# ── Competitor management ──────────────────────────────────────────────────────


class AddCompetitorRequest(BaseModel):
    url: str


@router.post("/{project_id}/competitors")
def add_competitor(
    project_id: str,
    body: AddCompetitorRequest,
    user: CurrentUser,
    background_tasks: BackgroundTasks,
):
    """Add a competitor URL and trigger a background pipeline run for it."""
    sb = get_supabase()
    proj_resp = sb.table("projects").select("*").eq("id", project_id).execute()
    if not proj_resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    project = proj_resp.data[0]
    if user["role"] == "analyst" and project["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    comp_urls: list[str] = list(project.get("competitor_urls") or [])
    normalized = body.url.strip().rstrip("/")
    if normalized in [u.rstrip("/") for u in comp_urls]:
        raise HTTPException(status_code=409, detail="Competitor already exists")

    comp_urls.append(normalized)
    sb.table("projects").update({"competitor_urls": comp_urls}).eq("id", project_id).execute()

    # Run a lightweight pipeline for just this competitor URL
    background_tasks.add_task(
        _run_competitor_pipeline_background,
        project_id,
        normalized,
    )

    return {"ok": True, "url": normalized}


@router.delete("/{project_id}/competitors/{comp_index}")
def remove_competitor(project_id: str, comp_index: int, user: CurrentUser):
    """Remove a competitor by its index in the competitor_urls list."""
    sb = get_supabase()
    proj_resp = sb.table("projects").select("*").eq("id", project_id).execute()
    if not proj_resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    project = proj_resp.data[0]
    if user["role"] == "analyst" and project["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    comp_urls: list[str] = list(project.get("competitor_urls") or [])
    if comp_index < 0 or comp_index >= len(comp_urls):
        raise HTTPException(status_code=404, detail="Competitor index out of range")

    removed_url = comp_urls.pop(comp_index)
    sb.table("projects").update({"competitor_urls": comp_urls}).eq("id", project_id).execute()

    return {"ok": True, "removed": removed_url}


def _run_competitor_pipeline_background(project_id: str, competitor_url: str) -> None:
    """Run a lightweight pipeline for a single competitor URL (Lighthouse + BuiltWith + screenshot)."""
    try:
        import asyncio
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
        from app.services.pipeline import collect_site_data
        from retina.clients.pagespeed import PageSpeedClient
        from retina.clients.builtwith import BuiltWithClient
        from retina.clients.screenshot import ScreenshotClient
        from retina.config import Settings

        settings = Settings()

        async def _run():
            psi = PageSpeedClient(settings.pagespeed_api_key)
            bw = BuiltWithClient(settings.builtwith_api_key)
            ss = ScreenshotClient(get_supabase())
            try:
                report = await collect_site_data(competitor_url, psi, bw, ss)
                logger.info("Competitor pipeline complete for %s in project %s", competitor_url, project_id)
            except Exception:
                logger.exception("Competitor pipeline failed for %s", competitor_url)

        try:
            asyncio.run(_run())
        except Exception:
            logger.exception("Competitor pipeline runner failed for %s", competitor_url)
    except ImportError:
        logger.warning("Heavy dependencies not available, skipping competitor pipeline for %s", competitor_url)


class PipelineStatusOut(BaseModel):
    project_id: str
    status: str
    current_step: str
    progress: int
    error_message: str | None = None
    started_at: float | None = None
    completed_at: float | None = None
    step_times: dict[str, float] = {}


@router.get("/{project_id}/status", response_model=PipelineStatusOut)
def get_project_status(project_id: str, user: CurrentUser):
    """Return current pipeline status for a project."""
    # Verify project access
    sb = get_supabase()
    proj_resp = sb.table("projects").select("id, created_by, status").eq("id", project_id).execute()
    if not proj_resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    project = proj_resp.data[0]
    if user["role"] == "analyst" and project["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Check in-memory status first
    run = get_run(project_id)
    if run:
        return run

    # Fallback: if no in-memory run exists, derive from project status
    proj_status = project["status"]
    if proj_status == "complete":
        return {
            "project_id": project_id,
            "status": "complete",
            "current_step": "complete",
            "progress": 100,
            "error_message": None,
            "started_at": None,
            "completed_at": None,
            "step_times": {},
        }
    else:
        return {
            "project_id": project_id,
            "status": "running" if proj_status == "in_progress" else "error",
            "current_step": "queued",
            "progress": 0,
            "error_message": None,
            "started_at": None,
            "completed_at": None,
            "step_times": {},
        }


@router.post("/{project_id}/retry", response_model=PipelineStatusOut)
async def retry_pipeline(
    project_id: str,
    user: CurrentUser,
):
    """Re-trigger the pipeline for a project after an error."""
    sb = get_supabase()
    proj_resp = sb.table("projects").select("*").eq("id", project_id).execute()
    if not proj_resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    project = proj_resp.data[0]
    if user["role"] == "analyst" and project["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Reset and re-trigger
    run = create_run(project_id)
    import asyncio
    asyncio.ensure_future(
        _run_pipeline_background_async(project_id, project["primary_url"], project.get("competitor_urls", []))
    )
    return run.to_dict()


@router.post("/{project_id}/refresh")
async def refresh_project(
    project_id: str,
    user: CurrentUser,
):
    """Re-run full analysis pipeline for a project."""
    sb = get_supabase()
    proj_resp = sb.table("projects").select("*").eq("id", project_id).execute()
    if not proj_resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    project = proj_resp.data[0]
    if user["role"] == "analyst" and project["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Reset status and re-trigger
    run = create_run(project_id)
    import asyncio
    asyncio.ensure_future(
        _run_pipeline_background_async(project_id, project["primary_url"], project.get("competitor_urls", []))
    )
    return run.to_dict()


# ── Screenshot upload / delete ─────────────────────────────────────────────


@router.post("/{project_id}/screenshot")
async def upload_project_screenshot(
    project_id: str,
    user: CurrentUser,
    file: UploadFile = File(...),
):
    """Upload or replace the project screenshot."""
    import os
    import uuid as _uuid

    # Validate file type
    allowed = {"image/png", "image/jpeg", "image/webp"}
    ct = file.content_type or ""
    if ct not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ct}")

    sb = get_supabase()

    # Verify project exists and user has access
    proj_resp = sb.table("projects").select("id, created_by").eq("id", project_id).execute()
    if not proj_resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    project = proj_resp.data[0]
    if user["role"] == "analyst" and project["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Delete old screenshot if exists
    data_resp = (
        sb.table("project_data")
        .select("screenshot_paths")
        .eq("project_id", project_id)
        .execute()
    )
    if data_resp.data:
        old_paths = data_resp.data[0].get("screenshot_paths") or {}
        if isinstance(old_paths, dict):
            for key in ("viewport", "full_page"):
                old_url = old_paths.get(key)
                if old_url and "supabase" in old_url:
                    # Extract storage path from URL
                    try:
                        path_part = old_url.split("/screenshots/", 1)[1]
                        sb.storage.from_("screenshots").remove([path_part])
                    except Exception:
                        pass  # Best-effort deletion

    # Upload new file
    content = await file.read()
    ext_map = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}
    ext = ext_map.get(ct, ".png")
    remote_name = f"{_uuid.uuid4().hex}{ext}"
    remote_path = f"{project_id}/{remote_name}"

    sb.storage.from_("screenshots").upload(
        path=remote_path,
        file=content,
        file_options={"content-type": ct},
    )
    public_url = sb.storage.from_("screenshots").get_public_url(remote_path)

    # Update project_data with new screenshot path
    new_paths = {"viewport": public_url}
    existing = (
        sb.table("project_data")
        .select("project_id")
        .eq("project_id", project_id)
        .execute()
    )
    if existing.data:
        sb.table("project_data").update(
            {"screenshot_paths": new_paths}
        ).eq("project_id", project_id).execute()
    else:
        sb.table("project_data").insert(
            {"project_id": project_id, "site_url": "", "screenshot_paths": new_paths}
        ).execute()

    return {"screenshot_url": public_url}


@router.delete("/{project_id}/screenshot")
def delete_project_screenshot(
    project_id: str,
    user: CurrentUser,
):
    """Remove the project screenshot."""
    sb = get_supabase()

    # Verify project exists and user has access
    proj_resp = sb.table("projects").select("id, created_by").eq("id", project_id).execute()
    if not proj_resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    project = proj_resp.data[0]
    if user["role"] == "analyst" and project["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get current screenshot paths
    data_resp = (
        sb.table("project_data")
        .select("screenshot_paths")
        .eq("project_id", project_id)
        .execute()
    )
    if data_resp.data:
        old_paths = data_resp.data[0].get("screenshot_paths") or {}
        if isinstance(old_paths, dict):
            for key in ("viewport", "full_page"):
                old_url = old_paths.get(key)
                if old_url and "supabase" in old_url:
                    try:
                        path_part = old_url.split("/screenshots/", 1)[1]
                        sb.storage.from_("screenshots").remove([path_part])
                    except Exception:
                        pass

        # Clear screenshot_paths
        sb.table("project_data").update(
            {"screenshot_paths": {}}
        ).eq("project_id", project_id).execute()

    return {"ok": True}


LENS_MAP = {
    "performance_technical_health": "Performance & Platform",
    "seo_ai_visibility": "SEO & AI Visibility",
    "brand_messaging": "Brand & Messaging",
    "experience_design": "Experience & Design",
    "conversion_strategy": "Conversion & Strategy",
}

LENS_ORDER = [
    "performance_technical_health",
    "seo_ai_visibility",
    "brand_messaging",
    "experience_design",
    "conversion_strategy",
]

QUADRANT_ORDER = ["no_brainers", "quick_wins", "growth_moves", "transformational"]
QUADRANT_LABELS = {
    "no_brainers": "No Brainers",
    "quick_wins": "Quick Wins",
    "growth_moves": "Growth Moves",
    "transformational": "Transformational",
}


@router.get("/{project_id}/summary", response_model=ProjectSummary)
def get_project_summary(project_id: str, user: CurrentUser):
    """Return a shaped summary for the Report page UI."""
    sb = get_supabase()

    # Fetch project
    proj_resp = sb.table("projects").select("*").eq("id", project_id).execute()
    if not proj_resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    project = proj_resp.data[0]

    if user["role"] == "analyst" and project["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Fetch related data
    data_resp = sb.table("project_data").select("*").eq("project_id", project_id).execute()
    reports_resp = (
        sb.table("reports").select("*").eq("project_id", project_id)
        .order("generated_at", desc=True).execute()
    )
    scores_resp = (
        sb.table("analyst_scores").select("*").eq("project_id", project_id).execute()
    )

    # Prefer the primary URL's project_data row (multiple rows may exist for competitors)
    raw_primary = project.get("primary_url", "")
    norm_primary = raw_primary.strip()
    if norm_primary and not norm_primary.startswith(("http://", "https://")):
        norm_primary = "https://" + norm_primary
    norm_primary = norm_primary.rstrip("/").lower()
    project_data: dict[str, Any] = {}
    if data_resp.data:
        for row in data_resp.data:
            site_url = (row.get("site_url") or "").rstrip("/").lower()
            if site_url == norm_primary:
                project_data = row
                break
        if not project_data:
            project_data = data_resp.data[0]
    report = reports_resp.data[0] if reports_resp.data else {}
    analyst_scores = scores_resp.data or []

    # ── Screenshot URL ────────────────────────────────────────────────────
    screenshot_url: str | None = None
    sp = project_data.get("screenshot_paths") or {}
    if isinstance(sp, dict):
        # Try viewport first (most common), then full_page, then legacy keys
        screenshot_url = (
            sp.get("viewport")
            or sp.get("full_page")
            or sp.get("desktop")
            or sp.get("mobile")
            or None
        )
    elif isinstance(sp, str) and sp:
        screenshot_url = sp

    # ── Lens scores ───────────────────────────────────────────────────────
    automated = project_data.get("automated_scores") or {}
    # Build analyst map, preferring entries for the primary_url
    analyst_map: dict[str, Any] = {}
    for s in analyst_scores:
        ln = s.get("lens_name", "")
        if ln not in analyst_map or s.get("site_url") == raw_primary:
            analyst_map[ln] = s

    lens_scores: list[dict[str, Any]] = []
    for lid in LENS_ORDER:
        score: float | None = None
        # Automated scores
        auto = automated.get(lid)
        if auto and auto.get("score") is not None:
            score = auto["score"]
        # Analyst scores (sum of sub_scores) — override automated for analyst lenses
        a = analyst_map.get(lid)
        if a and a.get("sub_scores"):
            sub_vals = a["sub_scores"]
            if isinstance(sub_vals, dict):
                total = 0.0
                for v in sub_vals.values():
                    if isinstance(v, (int, float)):
                        total += v
                    elif isinstance(v, dict) and "score" in v:
                        total += float(v["score"])
                if total > 0:
                    score = total
        lens_scores.append({
            "lens_id": lid,
            "lens_name": LENS_MAP[lid],
            "score": round(score, 2) if score is not None else None,
            "max_score": 20.0,
        })

    # ── Retina score ──────────────────────────────────────────────────────
    # Always compute from live lens scores (never trust stale DB value)
    scored = [ls["score"] for ls in lens_scores if ls["score"] is not None]
    retina_score = round(sum(scored), 2) if scored else report.get("retina_score")

    # ── Technology Stack ────────────────────────────────────────────────
    tech_stack = _extract_tech_stack(project_data.get("builtwith_data") or {})

    # ── Competitors ───────────────────────────────────────────────────────
    competitors = [
        {"url": url, "retina_score": None}
        for url in (project.get("competitor_urls") or [])
    ]

    # ── Recommendations ───────────────────────────────────────────────────
    quadrant_data = report.get("quadrant_data") or {}
    recs: list[dict[str, Any]] = []
    for qid in QUADRANT_ORDER:
        items: list[Any] = []
        qd = quadrant_data.get(qid)
        if isinstance(qd, list):
            # Pass through objects (title/description/lens) as-is
            items = list(qd)
        elif isinstance(qd, dict):
            items = list(qd.get("items", []))
        recs.append({"quadrant": QUADRANT_LABELS[qid], "items": items})

    return {
        "id": project["id"],
        "name": project["name"],
        "primary_url": project["primary_url"],
        "status": project["status"],
        "screenshot_url": screenshot_url,
        "retina_score": retina_score,
        "lens_scores": lens_scores,
        "tech_stack": tech_stack,
        "competitors": competitors,
        "recommendations": recs,
    }


def _extract_tech_stack(builtwith_data: dict) -> dict[str, list[str]]:
    """Extract key technology stack info from BuiltWith data for the summary page.

    Only surfaces CMS, Analytics, and CRM — the high-level business tools.
    Framework, hosting, CDN, etc. live on the Performance lens detail page.
    """
    techs = builtwith_data.get("technologies") or []
    if not techs:
        return {}

    # Category mapping: BuiltWith category name → our display category
    CATEGORY_MAP = {
        # CMS / Headless
        "Hosted Solution": "cms",
        "Headless": "cms",
        "Enterprise": "cms",
        # CDN
        "CDN": "cdn",
        "Content Delivery Network": "cdn",
        # Analytics
        "Audience Measurement": "analytics",
        "Visitor Count Tracking": "analytics",
        "Tag Management": "analytics",
        # CRM / Marketing
        "Feedback Forms and Surveys": "crm",
        "Transactional Email": "crm",
    }

    # Known technologies to force-categorize (override for common ones)
    NAME_OVERRIDES = {
        "Webflow": "cms",
        "WordPress": "cms",
        "Contentful": "cms",
        "Shopify": "cms",
        "Squarespace": "cms",
        "Wix": "cms",
        "Drupal": "cms",
        "HubSpot COS": "cms",
        "HubSpot CMS": "cms",
        "HubSpot": "crm",
        "Salesforce": "crm",
        "Marketo": "crm",
        "Pardot": "crm",
        "Mailchimp": "crm",
        "ActiveCampaign": "crm",
        "Google Analytics": "analytics",
        "Google Analytics 4": "analytics",
        "Google Tag Manager": "analytics",
        "Hotjar": "analytics",
        "Mixpanel": "analytics",
        "Segment": "analytics",
        # CDN
        "Cloudflare": "cdn",
        "Fastly": "cdn",
        "Akamai": "cdn",
        "Amazon CloudFront": "cdn",
        "KeyCDN": "cdn",
        "Bunny CDN": "cdn",
        "StackPath": "cdn",
    }

    result: dict[str, set[str]] = {}
    seen_names: set[str] = set()

    for tech in techs:
        name = tech.get("name", "").strip()
        if not name:
            continue

        # Check name overrides first
        cat = NAME_OVERRIDES.get(name)
        if cat:
            if name not in seen_names:
                result.setdefault(cat, set()).add(name)
                seen_names.add(name)
            continue

        # Check category mapping
        for bw_cat in tech.get("categories", []):
            cat = CATEGORY_MAP.get(bw_cat)
            if cat and name not in seen_names:
                result.setdefault(cat, set()).add(name)
                seen_names.add(name)
                break

    # If multiple CMS platforms detected, flag for analyst review
    cms_conflict = False
    bw_meta = builtwith_data.get("meta") or {}
    if bw_meta.get("cms_conflict") == "true":
        cms_conflict = True

    # Convert sets to sorted lists, limit each category
    output: dict[str, Any] = {k: sorted(v)[:8] for k, v in result.items() if v}
    if cms_conflict:
        output["_cms_conflict"] = True
        output["_cms_conflict_note"] = (
            f"Multiple CMS platforms detected ({bw_meta.get('cms_detected', '')}) — "
            "flagged for analyst review. Verify which is currently active."
        )
    return output


LENS_COLORS = {
    "performance_technical_health": "#076EFF",
    "seo_ai_visibility": "#00C864",
    "brand_messaging": "#9B59B6",
    "experience_design": "#E74C3C",
    "conversion_strategy": "#FF8C00",
}


class LensDetail(BaseModel):
    """Shaped response for the lens detail pages."""
    project_id: str
    project_name: str
    lens_id: str
    lens_name: str
    lens_color: str
    lens_score: float | None = None
    max_score: float = 20.0
    lens_scores: list[LensScore] = []
    lighthouse_data: dict[str, Any] = {}
    builtwith_data: dict[str, Any] = {}
    interpretations: dict[str, Any] = {}
    analyst_sub_scores: dict[str, Any] = {}
    analyst_observations: str = ""
    user_observations: str | None = None  # User-edited observations text
    artifacts: list[dict[str, Any]] = []


@router.get("/{project_id}/lens/{lens_id}", response_model=LensDetail)
def get_lens_detail(project_id: str, lens_id: str, user: CurrentUser):
    """Return shaped data for a specific lens detail page."""
    if lens_id not in LENS_MAP:
        raise HTTPException(status_code=404, detail="Unknown lens")
    sb = get_supabase()

    # Fetch project
    proj_resp = sb.table("projects").select("*").eq("id", project_id).execute()
    if not proj_resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    project = proj_resp.data[0]
    if user["role"] == "analyst" and project["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Fetch related data
    data_resp = sb.table("project_data").select("*").eq("project_id", project_id).execute()
    scores_resp = sb.table("analyst_scores").select("*").eq("project_id", project_id).execute()
    reports_resp = (
        sb.table("reports").select("retina_score").eq("project_id", project_id)
        .order("generated_at", desc=True).limit(1).execute()
    )
    # Prefer the primary URL's project_data row (multiple rows may exist for competitors)
    # Normalize for comparison since pipeline normalizes URLs before storing
    raw_primary = project.get("primary_url", "")
    norm_primary = raw_primary.strip()
    if norm_primary and not norm_primary.startswith(("http://", "https://")):
        norm_primary = "https://" + norm_primary
    norm_primary = norm_primary.rstrip("/").lower()
    project_data: dict[str, Any] = {}
    if data_resp.data:
        for row in data_resp.data:
            site_url = (row.get("site_url") or "").rstrip("/").lower()
            if site_url == norm_primary:
                project_data = row
                break
        if not project_data:
            project_data = data_resp.data[0]
    analyst_scores = scores_resp.data or []
    report = reports_resp.data[0] if reports_resp.data else {}

    # Build all lens scores for the nav bar
    automated = project_data.get("automated_scores") or {}
    # Build analyst map, preferring entries for the primary_url
    analyst_map: dict[str, Any] = {}
    for s in analyst_scores:
        ln = s.get("lens_name", "")
        if ln not in analyst_map or s.get("site_url") == project.get("primary_url"):
            analyst_map[ln] = s
    lens_scores_list: list[dict[str, Any]] = []
    for lid in LENS_ORDER:
        score: float | None = None
        auto = automated.get(lid)
        if auto and auto.get("score") is not None:
            score = auto["score"]
        a = analyst_map.get(lid)
        if a and a.get("sub_scores"):
            sub_vals = a["sub_scores"]
            if isinstance(sub_vals, dict):
                total = 0.0
                for v in sub_vals.values():
                    if isinstance(v, (int, float)):
                        total += v
                    elif isinstance(v, dict) and "score" in v:
                        total += float(v["score"])
                if total > 0:
                    score = total
        lens_scores_list.append({
            "lens_id": lid,
            "lens_name": LENS_MAP[lid],
            "score": round(score, 2) if score is not None else None,
            "max_score": 20.0,
        })

    # Current lens score
    current_lens = next((ls for ls in lens_scores_list if ls["lens_id"] == lens_id), None)
    lens_score = current_lens["score"] if current_lens else None

    # Interpretations — collect relevant ones
    all_interps = project_data.get("interpretations") or {}
    interp_key_map = {
        "performance_technical_health": "performance",
        "seo_ai_visibility": "seo",
        "brand_messaging": "brand_messaging",
        "experience_design": "experience_design",
        "conversion_strategy": "conversion_strategy",
    }
    interps: dict[str, Any] = {}
    primary_key = interp_key_map.get(lens_id, "")
    if primary_key in all_interps:
        interps[primary_key] = all_interps[primary_key]
    # For analyst lenses, also include from analyst_lenses interpretation
    analyst_lenses_interp = all_interps.get("analyst_lenses") or {}
    if lens_id in analyst_lenses_interp:
        interps["analyst_narrative"] = analyst_lenses_interp[lens_id]

    # Analyst sub-scores + observations for this lens
    # Prefer scores for primary_url; fall back to any available entry
    primary_url = project.get("primary_url", "")
    analyst_entry = None
    analyst_fallback = None
    for s in analyst_scores:
        if s.get("lens_name") == lens_id:
            if s.get("site_url") == primary_url:
                analyst_entry = s
                break
            if analyst_fallback is None:
                analyst_fallback = s
    if analyst_entry is None:
        analyst_entry = analyst_fallback or {}

    # Normalize to {key: {score: float, observation: str}} shape
    sub_scores_raw = analyst_entry.get("sub_scores") or {}
    analyst_sub: dict[str, Any] = {}
    if isinstance(sub_scores_raw, dict):
        for k, v in sub_scores_raw.items():
            if isinstance(v, dict) and "score" in v:
                analyst_sub[k] = {
                    "score": float(v["score"]),
                    "observation": v.get("observation", ""),
                }
            elif isinstance(v, (int, float)):
                analyst_sub[k] = {"score": float(v), "observation": ""}
            else:
                analyst_sub[k] = {"score": 0.0, "observation": ""}

    # For analyst lenses, ensure all expected sub-dimensions are always present
    # so the frontend always renders the structure even before analyst input
    DEFAULT_SUB_DIMS: dict[str, list[str]] = {
        "brand_messaging": ["brand_visual_language", "brand_voice_messaging", "value_proposition", "brand_differentiation"],
        "experience_design": ["interface_design", "content_taxonomy", "navigation_architecture", "responsiveness"],
        "conversion_strategy": ["call_to_action_logic", "lead_capture_form_design", "trust_signals", "funnel_design"],
    }
    if lens_id in DEFAULT_SUB_DIMS:
        for dim_key in DEFAULT_SUB_DIMS[lens_id]:
            if dim_key not in analyst_sub:
                analyst_sub[dim_key] = {"score": 0.0, "observation": ""}

    observations = analyst_entry.get("raw_observations") or "" if isinstance(analyst_entry, dict) else ""

    # User-edited observations
    all_interps_raw = project_data.get("interpretations") or {}
    user_edits = all_interps_raw.get("_user_edits") or {}
    user_obs = user_edits.get(lens_id)

    # Artifacts for this lens
    all_artifacts = all_interps_raw.get("_artifacts") or {}
    lens_artifacts = all_artifacts.get(lens_id) or []

    return {
        "project_id": project_id,
        "project_name": project["name"],
        "lens_id": lens_id,
        "lens_name": LENS_MAP[lens_id],
        "lens_color": LENS_COLORS[lens_id],
        "lens_score": lens_score,
        "max_score": 20.0,
        "lens_scores": lens_scores_list,
        "lighthouse_data": project_data.get("lighthouse_data") or {},
        "builtwith_data": project_data.get("builtwith_data") or {},
        "interpretations": interps,
        "analyst_sub_scores": analyst_sub,
        "analyst_observations": observations,
        "user_observations": user_obs,
        "artifacts": lens_artifacts,
    }


class UpdateObservationsRequest(BaseModel):
    text: str


@router.patch("/{project_id}/lens/{lens_id}/observations")
def update_lens_observations(
    project_id: str,
    lens_id: str,
    body: UpdateObservationsRequest,
    user: CurrentUser,
):
    """Save edited observations text for a specific lens."""
    if lens_id not in LENS_MAP:
        raise HTTPException(status_code=404, detail="Unknown lens")
    sb = get_supabase()
    proj_resp = sb.table("projects").select("id, created_by").eq("id", project_id).execute()
    if not proj_resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    project = proj_resp.data[0]
    if user["role"] == "analyst" and project["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get project_data and update interpretations
    data_resp = sb.table("project_data").select("id, interpretations").eq("project_id", project_id).execute()
    if not data_resp.data:
        raise HTTPException(status_code=404, detail="No project data found")

    pd = data_resp.data[0]
    interps = pd.get("interpretations") or {}

    # Store user edits in a separate key to preserve AI originals
    user_edits = interps.get("_user_edits") or {}
    user_edits[lens_id] = body.text
    interps["_user_edits"] = user_edits

    sb.table("project_data").update({"interpretations": interps}).eq("id", pd["id"]).execute()
    return {"ok": True}


# ── Copilot chat endpoint ────────────────────────────────────────────────────


class CopilotMessageItem(BaseModel):
    role: str
    content: str


class CopilotContext(BaseModel):
    project_name: str = ""
    site_url: str = ""
    lens_name: str = ""
    lens_definition: str = ""
    sub_scores: dict[str, Any] = {}
    current_observations: str = ""


class CopilotRequest(BaseModel):
    message: str
    history: list[CopilotMessageItem] = []
    context: CopilotContext = CopilotContext()


@router.post("/{project_id}/lens/{lens_id}/copilot")
def copilot_chat(
    project_id: str,
    lens_id: str,
    body: CopilotRequest,
    user: CurrentUser,
):
    """Send a message to the Retina Copilot for a specific lens."""
    if lens_id not in LENS_MAP:
        raise HTTPException(status_code=404, detail="Unknown lens")

    # Auth check
    sb = get_supabase()
    proj_resp = sb.table("projects").select("id, created_by").eq("id", project_id).execute()
    if not proj_resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    project = proj_resp.data[0]
    if user["role"] == "analyst" and project["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    import json
    try:
        import anthropic
        from retina.config import Settings
        settings = Settings()
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    except Exception as exc:
        logger.error("Copilot: failed to init Anthropic client: %s", exc)
        raise HTTPException(status_code=500, detail="AI service unavailable")

    ctx = body.context

    # Build sub-dimension context block from analyst scores
    sub_dim_lines: list[str] = []
    if ctx.sub_scores:
        # Fetch full sub-dimension data (scores + observations) from Supabase
        analyst_resp = sb.table("analyst_scores").select("sub_scores").eq(
            "project_id", project_id
        ).eq("lens_name", LENS_MAP.get(lens_id, "")).execute()
        full_sub = {}
        if analyst_resp.data:
            full_sub = analyst_resp.data[0].get("sub_scores", {})

        for dim_key, dim_val in full_sub.items():
            label = dim_key.replace("_", " ").title()
            if isinstance(dim_val, dict):
                score = dim_val.get("score", 0)
                obs = dim_val.get("observation", "")
                if obs:
                    sub_dim_lines.append(f"{label}: {score}/5\n{obs}")
                else:
                    sub_dim_lines.append(f"{label}: {score}/5")
            elif isinstance(dim_val, (int, float)):
                sub_dim_lines.append(f"{label}: {dim_val}/5")

    # Build the system prompt with rich sub-dimension context
    sub_context = ""
    if sub_dim_lines:
        total = sum(
            (v.get("score", 0) if isinstance(v, dict) else float(v))
            for v in full_sub.values()
        )
        sub_context = (
            f"\n\nThe analyst has completed the following sub-dimension assessments:\n\n"
            + "\n\n".join(sub_dim_lines)
            + f"\n\nTotal lens score: {total:.0f}/20"
            + "\n\nUse these sub-dimension assessments as your primary context. "
            "Synthesize them into a cohesive strategic narrative. "
            "Lead with what is working. Frame gaps as opportunities. "
            "Do not repeat sub-dimension names verbatim — synthesize them."
        )

    system_prompt = (
        f"You are Retina Copilot, an AI assistant helping an analyst synthesize "
        f"the {ctx.lens_name} observations for a client website analysis.\n\n"
        f"Project: {ctx.project_name}\n"
        f"Site URL: {ctx.site_url}\n"
        f"Lens: {ctx.lens_name} — {ctx.lens_definition}\n"
        + (f"Current observations:\n{ctx.current_observations}\n" if ctx.current_observations else "")
        + sub_context + "\n\n"
        "Be specific, strategic, and opportunity-framed. Reference the actual "
        "site where possible. Keep responses concise and actionable. "
        "Use Matic's consultative voice — confident, direct, always connecting "
        "findings to business outcomes. Write 2-3 paragraphs of expert strategic "
        "commentary, not a checklist review."
    )

    # Build messages list
    messages = [{"role": m.role, "content": m.content} for m in body.history]
    messages.append({"role": "user", "content": body.message})

    try:
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        )
        text = "".join(b.text for b in response.content if b.type == "text")
        return {"response": text}
    except Exception as exc:
        logger.error("Copilot: Claude API error: %s", exc)
        raise HTTPException(status_code=500, detail="AI request failed")


# ── Sub-dimension update endpoint ─────────────────────────────────────────────


class UpdateSubDimensionRequest(BaseModel):
    score: float
    observation: str = ""


@router.patch("/{project_id}/lens/{lens_id}/subdimension/{subdim_id}")
def update_subdimension(
    project_id: str,
    lens_id: str,
    subdim_id: str,
    body: UpdateSubDimensionRequest,
    user: CurrentUser,
):
    """Update a single sub-dimension score and observation."""
    if lens_id not in LENS_MAP:
        raise HTTPException(status_code=404, detail="Unknown lens")

    sb = get_supabase()
    proj_resp = sb.table("projects").select("id, created_by, primary_url").eq("id", project_id).execute()
    if not proj_resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    project = proj_resp.data[0]
    if user["role"] == "analyst" and project["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    site_url = project.get("primary_url", "")

    # Get existing analyst_scores row for the primary URL
    scores_resp = (
        sb.table("analyst_scores")
        .select("*")
        .eq("project_id", project_id)
        .eq("lens_name", lens_id)
        .execute()
    )

    # Prefer the row matching primary_url (multiple rows may exist for competitors)
    row = None
    if scores_resp.data:
        row = scores_resp.data[0]
        for r in scores_resp.data:
            if r.get("site_url") == site_url:
                row = r
                break
    sub_scores = (row.get("sub_scores") or {}) if row else {}

    # Update this sub-dimension with new shape
    sub_scores[subdim_id] = {
        "score": body.score,
        "observation": body.observation,
    }

    # Upsert
    if row:
        sb.table("analyst_scores").update({
            "sub_scores": sub_scores,
        }).eq("id", row["id"]).execute()
    else:
        sb.table("analyst_scores").insert({
            "project_id": project_id,
            "site_url": site_url,
            "lens_name": lens_id,
            "sub_scores": sub_scores,
        }).execute()

    # Recalculate composite Retina Score
    recalculate_scores(project_id)

    return {"ok": True}


# ── Artifacts endpoints ──────────────────────────────────────────────────────


@router.get("/{project_id}/lens/{lens_id}/artifacts")
def list_artifacts(project_id: str, lens_id: str, user: CurrentUser):
    """List artifacts for a specific lens."""
    sb = get_supabase()
    data_resp = sb.table("project_data").select("interpretations").eq("project_id", project_id).execute()
    if not data_resp.data:
        return {"artifacts": []}
    interps = data_resp.data[0].get("interpretations") or {}
    all_artifacts = interps.get("_artifacts") or {}
    lens_artifacts = all_artifacts.get(lens_id) or []
    return {"artifacts": lens_artifacts}


@router.post("/{project_id}/lens/{lens_id}/artifacts")
async def upload_artifact(
    project_id: str,
    lens_id: str,
    user: CurrentUser,
    file: UploadFile = File(...),
):
    """Upload an artifact image for a specific lens."""
    if lens_id not in LENS_MAP:
        raise HTTPException(status_code=404, detail="Unknown lens")

    sb = get_supabase()

    # Auth check
    proj_resp = sb.table("projects").select("id, created_by").eq("id", project_id).execute()
    if not proj_resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    project = proj_resp.data[0]
    if user["role"] == "analyst" and project["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Check current count
    data_resp = sb.table("project_data").select("interpretations").eq("project_id", project_id).execute()
    interps = {}
    if data_resp.data:
        interps = data_resp.data[0].get("interpretations") or {}
    all_artifacts = interps.get("_artifacts") or {}
    lens_artifacts = all_artifacts.get(lens_id) or []

    if len(lens_artifacts) >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 artifacts per lens")

    # Upload to storage
    import uuid
    file_bytes = await file.read()
    ext = (file.filename or "image.png").rsplit(".", 1)[-1] if "." in (file.filename or "") else "png"
    storage_path = f"{project_id}/{lens_id}/{uuid.uuid4().hex}.{ext}"

    sb.storage.from_("artifacts").upload(
        storage_path,
        file_bytes,
        file_options={"content-type": file.content_type or "image/png"},
    )

    file_url = f"{sb.supabase_url}/storage/v1/object/public/artifacts/{storage_path}"

    # Add artifact metadata
    artifact = {
        "id": uuid.uuid4().hex,
        "file_url": file_url,
        "file_name": file.filename or "image.png",
        "uploaded_by": user["id"],
        "storage_path": storage_path,
    }
    lens_artifacts.append(artifact)
    all_artifacts[lens_id] = lens_artifacts
    interps["_artifacts"] = all_artifacts

    sb.table("project_data").update({"interpretations": interps}).eq("project_id", project_id).execute()

    return artifact


@router.delete("/{project_id}/lens/{lens_id}/artifacts/{artifact_id}")
def delete_artifact(project_id: str, lens_id: str, artifact_id: str, user: CurrentUser):
    """Delete an artifact."""
    sb = get_supabase()

    # Auth check
    proj_resp = sb.table("projects").select("id, created_by").eq("id", project_id).execute()
    if not proj_resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    project = proj_resp.data[0]
    if user["role"] == "analyst" and project["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    data_resp = sb.table("project_data").select("interpretations").eq("project_id", project_id).execute()
    if not data_resp.data:
        raise HTTPException(status_code=404, detail="Artifact not found")

    interps = data_resp.data[0].get("interpretations") or {}
    all_artifacts = interps.get("_artifacts") or {}
    lens_artifacts = all_artifacts.get(lens_id) or []

    # Find and remove
    target = None
    remaining = []
    for a in lens_artifacts:
        if a.get("id") == artifact_id:
            target = a
        else:
            remaining.append(a)

    if not target:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Delete from storage
    storage_path = target.get("storage_path")
    if storage_path:
        try:
            sb.storage.from_("artifacts").remove([storage_path])
        except Exception:
            pass  # Best-effort cleanup

    # Update metadata
    all_artifacts[lens_id] = remaining
    interps["_artifacts"] = all_artifacts
    sb.table("project_data").update({"interpretations": interps}).eq("project_id", project_id).execute()

    return {"ok": True}


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(project_id: str, user: CurrentUser):
    """Return a single project with all associated data."""
    sb = get_supabase()

    # Fetch project
    proj_resp = sb.table("projects").select("*").eq("id", project_id).execute()
    if not proj_resp.data:
        raise HTTPException(status_code=404, detail="Project not found")

    project = proj_resp.data[0]

    # Enforce access: analysts can only see their own
    if user["role"] == "analyst" and project["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Fetch related data
    data_resp = sb.table("project_data").select("*").eq("project_id", project_id).execute()
    reports_resp = (
        sb.table("reports")
        .select("*")
        .eq("project_id", project_id)
        .order("generated_at", desc=True)
        .execute()
    )
    scores_resp = (
        sb.table("analyst_scores")
        .select("*")
        .eq("project_id", project_id)
        .execute()
    )

    return {
        **project,
        "project_data": data_resp.data or [],
        "reports": reports_resp.data or [],
        "analyst_scores": scores_resp.data or [],
    }
