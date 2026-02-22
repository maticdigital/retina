"""Project CRUD operations via Supabase."""

from __future__ import annotations

from typing import Any

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
