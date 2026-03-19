"""Project CRUD operations via Supabase."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

from app.services.supabase_client import get_supabase


def create_project(
    name: str,
    primary_url: str,
    competitor_urls: list[str],
    created_by: str,
) -> dict[str, Any]:
    """Create a new project."""
    sb = get_supabase()
    resp = (
        sb.table("projects")
        .insert({
            "name": name,
            "primary_url": primary_url,
            "competitor_urls": competitor_urls,
            "status": "draft",
            "created_by": created_by,
        })
        .execute()
    )
    return resp.data[0]


def list_projects(user_id: str, user_role: str) -> list[dict[str, Any]]:
    """List projects visible to the user."""
    sb = get_supabase()
    query = sb.table("projects").select("*, users(name, email)")
    if user_role == "analyst":
        query = query.eq("created_by", user_id)
    resp = query.order("updated_at", desc=True).execute()
    return resp.data or []


def get_project(project_id: str) -> dict[str, Any] | None:
    """Get a single project by ID."""
    sb = get_supabase()
    resp = sb.table("projects").select("*").eq("id", project_id).execute()
    return resp.data[0] if resp.data else None


def update_project_status(project_id: str, status: str) -> None:
    """Update project status."""
    sb = get_supabase()
    sb.table("projects").update({"status": status}).eq("id", project_id).execute()


def delete_project(project_id: str) -> None:
    """Delete a project and all related data (cascade)."""
    sb = get_supabase()
    sb.table("projects").delete().eq("id", project_id).execute()


def duplicate_project(project_id: str, user_id: str) -> dict[str, Any]:
    """Duplicate a project with a new name."""
    original = get_project(project_id)
    if not original:
        raise ValueError("Project not found")
    return create_project(
        name=f"{original['name']} (Copy)",
        primary_url=original["primary_url"],
        competitor_urls=original.get("competitor_urls", []),
        created_by=user_id,
    )


# --- Project Data ---


def save_project_data(
    project_id: str,
    site_url: str,
    lighthouse_data: dict,
    builtwith_data: dict,
    screenshot_paths: dict,
    automated_scores: dict,
) -> dict[str, Any]:
    """Save or update site analysis data for a project."""
    sb = get_supabase()
    # Upsert: check if entry exists
    existing = (
        sb.table("project_data")
        .select("id")
        .eq("project_id", project_id)
        .eq("site_url", site_url)
        .execute()
    )
    row = {
        "project_id": project_id,
        "site_url": site_url,
        "lighthouse_data": lighthouse_data,
        "builtwith_data": builtwith_data,
        "screenshot_paths": screenshot_paths,
        "automated_scores": automated_scores,
    }
    if existing.data:
        resp = (
            sb.table("project_data")
            .update(row)
            .eq("id", existing.data[0]["id"])
            .execute()
        )
    else:
        resp = sb.table("project_data").insert(row).execute()
    return resp.data[0]


def get_project_data(project_id: str) -> list[dict[str, Any]]:
    """Get all site data for a project."""
    sb = get_supabase()
    resp = (
        sb.table("project_data")
        .select("*")
        .eq("project_id", project_id)
        .execute()
    )
    return resp.data or []


def update_interpretations(
    project_id: str,
    site_url: str,
    interpretations: dict,
) -> None:
    """Store AI-generated interpretations for a site in project_data.

    Merges new AI interpretations with existing data, preserving
    manually-entered user edits (_user_edits) and artifact metadata (_artifacts).
    """
    sb = get_supabase()
    existing = (
        sb.table("project_data")
        .select("id, interpretations")
        .eq("project_id", project_id)
        .eq("site_url", site_url)
        .execute()
    )
    if existing.data:
        # Preserve manually-entered data that lives under reserved keys
        old_interps = existing.data[0].get("interpretations") or {}
        merged = {**interpretations}
        for protected_key in ("_user_edits", "_artifacts"):
            if protected_key in old_interps:
                merged[protected_key] = old_interps[protected_key]
        sb.table("project_data").update(
            {"interpretations": merged}
        ).eq("id", existing.data[0]["id"]).execute()
    else:
        logger.warning(
            "No project_data row found for %s / %s — skipping interpretation storage",
            project_id, site_url,
        )


# --- Reports ---


def save_report(
    project_id: str,
    retina_score: float,
    ai_analysis: dict,
    quadrant_data: dict,
    pdf_path: str | None = None,
) -> dict[str, Any]:
    """Save a generated report."""
    sb = get_supabase()
    resp = (
        sb.table("reports")
        .insert({
            "project_id": project_id,
            "retina_score": retina_score,
            "ai_analysis": ai_analysis,
            "quadrant_data": quadrant_data,
            "pdf_path": pdf_path,
        })
        .execute()
    )
    return resp.data[0]


def get_reports(project_id: str) -> list[dict[str, Any]]:
    """Get all reports for a project."""
    sb = get_supabase()
    resp = (
        sb.table("reports")
        .select("*")
        .eq("project_id", project_id)
        .order("generated_at", desc=True)
        .execute()
    )
    return resp.data or []


# --- Analyst Scores ---


def save_analyst_score(
    project_id: str,
    site_url: str,
    lens_name: str,
    sub_scores: dict,
    raw_observations: str = "",
    refined_observations: str = "",
    screenshots: list[str] | None = None,
) -> dict[str, Any]:
    """Save analyst score for a lens."""
    sb = get_supabase()
    resp = (
        sb.table("analyst_scores")
        .insert({
            "project_id": project_id,
            "site_url": site_url,
            "lens_name": lens_name,
            "sub_scores": sub_scores,
            "raw_observations": raw_observations,
            "refined_observations": refined_observations,
            "screenshots": screenshots or [],
        })
        .execute()
    )
    return resp.data[0]


def upsert_analyst_score(
    project_id: str,
    site_url: str,
    lens_name: str,
    sub_scores: dict,
    raw_observations: str = "",
    refined_observations: str = "",
    screenshots: list[str] | None = None,
) -> dict[str, Any]:
    """Save or update analyst score for a lens (upsert for auto-save)."""
    sb = get_supabase()
    existing = (
        sb.table("analyst_scores")
        .select("id")
        .eq("project_id", project_id)
        .eq("site_url", site_url)
        .eq("lens_name", lens_name)
        .execute()
    )
    row = {
        "project_id": project_id,
        "site_url": site_url,
        "lens_name": lens_name,
        "sub_scores": sub_scores,
        "raw_observations": raw_observations,
        "refined_observations": refined_observations,
        "screenshots": screenshots or [],
    }
    if existing.data:
        resp = (
            sb.table("analyst_scores")
            .update(row)
            .eq("id", existing.data[0]["id"])
            .execute()
        )
    else:
        resp = sb.table("analyst_scores").insert(row).execute()
    return resp.data[0]


def get_analyst_scores(project_id: str) -> list[dict[str, Any]]:
    """Get all analyst scores for a project."""
    sb = get_supabase()
    resp = (
        sb.table("analyst_scores")
        .select("*")
        .eq("project_id", project_id)
        .execute()
    )
    return resp.data or []


# --- Score Recalculation ---


AUTOMATED_LENS_KEYS = ["performance_technical_health", "seo_ai_visibility"]
ANALYST_LENS_KEYS = ["brand_messaging", "experience_design", "conversion_strategy"]


def _sum_sub_scores(sub_scores: dict) -> float:
    """Sum sub-dimension scores from analyst_scores.sub_scores JSON."""
    total = 0.0
    for v in sub_scores.values():
        if isinstance(v, (int, float)):
            total += float(v)
        elif isinstance(v, dict) and "score" in v:
            total += float(v["score"])
    return total


def recalculate_scores(project_id: str) -> dict[str, float]:
    """Recalculate all lens scores and the composite Retina Score.

    Fetches current data from Supabase, computes correct totals, and
    updates the latest report row with the new composite score.

    Uses only the primary URL's scores when multiple rows exist (competitors).

    Returns:
        Dict with keys: performance, seo, brand, experience, conversion,
        retina_score — all floats.
    """
    sb = get_supabase()

    # Look up primary URL for filtering
    proj_resp = (
        sb.table("projects")
        .select("primary_url")
        .eq("id", project_id)
        .execute()
    )
    primary_url = ""
    if proj_resp.data:
        primary_url = proj_resp.data[0].get("primary_url", "")

    # 1. Automated scores from project_data (prefer primary URL row)
    pd_resp = (
        sb.table("project_data")
        .select("automated_scores, site_url")
        .eq("project_id", project_id)
        .execute()
    )
    auto_scores = {}
    if pd_resp.data:
        # Prefer the primary URL's row
        norm_primary = primary_url.strip()
        if norm_primary and not norm_primary.startswith(("http://", "https://")):
            norm_primary = "https://" + norm_primary
        norm_primary = norm_primary.rstrip("/").lower()
        chosen = pd_resp.data[0]
        for row in pd_resp.data:
            site_url = (row.get("site_url") or "").rstrip("/").lower()
            if site_url == norm_primary:
                chosen = row
                break
        auto_scores = chosen.get("automated_scores") or {}

    perf = 0.0
    seo = 0.0
    if isinstance(auto_scores.get("performance_technical_health"), dict):
        perf = float(auto_scores["performance_technical_health"].get("score") or 0)
    if isinstance(auto_scores.get("seo_ai_visibility"), dict):
        seo = float(auto_scores["seo_ai_visibility"].get("score") or 0)

    # 2. Analyst scores from analyst_scores table (prefer primary URL rows)
    as_resp = (
        sb.table("analyst_scores")
        .select("lens_name, sub_scores, site_url")
        .eq("project_id", project_id)
        .execute()
    )
    analyst_map: dict[str, float] = {}
    for row in as_resp.data or []:
        lens = row.get("lens_name", "")
        sub = row.get("sub_scores") or {}
        # Only overwrite if this is the first entry or matches primary URL
        if lens not in analyst_map or row.get("site_url") == primary_url:
            analyst_map[lens] = round(_sum_sub_scores(sub), 2)

    brand = analyst_map.get("brand_messaging", 0.0)
    experience = analyst_map.get("experience_design", 0.0)
    conversion = analyst_map.get("conversion_strategy", 0.0)

    # 3. Composite score
    retina_score = round(perf + seo + brand + experience + conversion, 2)

    # 4. Update latest report row
    rpt_resp = (
        sb.table("reports")
        .select("id")
        .eq("project_id", project_id)
        .order("generated_at", desc=True)
        .limit(1)
        .execute()
    )
    if rpt_resp.data:
        sb.table("reports").update(
            {"retina_score": retina_score}
        ).eq("id", rpt_resp.data[0]["id"]).execute()
        logger.info(
            "Recalculated scores for %s: perf=%.1f seo=%.1f brand=%.1f exp=%.1f conv=%.1f → retina=%.2f",
            project_id, perf, seo, brand, experience, conversion, retina_score,
        )
    else:
        logger.warning("No report row found for %s — cannot store recalculated score", project_id)

    return {
        "performance": perf,
        "seo": seo,
        "brand": brand,
        "experience": experience,
        "conversion": conversion,
        "retina_score": retina_score,
    }
