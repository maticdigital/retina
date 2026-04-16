"""Password-protected project sharing endpoints."""

from __future__ import annotations

import math
import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Any

import bcrypt
import httpx
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Request

from api.deps import CurrentUser, get_supabase

logger = logging.getLogger(__name__)

router = APIRouter(tags=["sharing"])


# ── Request / response models ────────────────────────────────────────────────

class EnableShareRequest(BaseModel):
    password: str = Field(..., min_length=4)


class EnableShareResponse(BaseModel):
    share_token: str
    share_url: str


class VerifyShareRequest(BaseModel):
    password: str


# ── Constants (duplicated from projects router to avoid coupling) ─────────────

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

LENS_COLORS = {
    "performance_technical_health": "#076EFF",
    "seo_ai_visibility": "#00C864",
    "brand_messaging": "#9B59B6",
    "experience_design": "#E74C3C",
    "conversion_strategy": "#FF8C00",
}

QUADRANT_ORDER = ["no_brainers", "quick_wins", "growth_moves", "transformational"]
QUADRANT_LABELS = {
    "no_brainers": "No Brainers",
    "quick_wins": "Quick Wins",
    "growth_moves": "Growth Moves",
    "transformational": "Transformational",
}

DEFAULT_SUB_DIMS: dict[str, list[str]] = {
    "brand_messaging": ["brand_visual_language", "brand_voice_messaging", "value_proposition", "brand_differentiation"],
    "experience_design": ["interface_design", "content_taxonomy", "navigation_architecture", "responsiveness"],
    "conversion_strategy": ["call_to_action_logic", "lead_capture_form_design", "trust_signals", "funnel_design"],
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/projects/{project_id}/share", response_model=EnableShareResponse)
def enable_sharing(project_id: str, body: EnableShareRequest, user: CurrentUser):
    """Enable or update password-protected sharing for a project."""
    sb = get_supabase()

    # Verify project exists and user has access
    proj_resp = sb.table("projects").select("id, share_token, created_by").eq("id", project_id).execute()
    if not proj_resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    project = proj_resp.data[0]

    if user["role"] == "analyst" and project["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    # Keep existing token or generate a new one
    token = project.get("share_token") or uuid.uuid4().hex[:12]

    sb.table("projects").update({
        "share_token": token,
        "share_password_hash": _hash_password(body.password),
        "is_shared": True,
    }).eq("id", project_id).execute()

    return {"share_token": token, "share_url": f"/shared/{token}"}


@router.delete("/projects/{project_id}/share")
def disable_sharing(project_id: str, user: CurrentUser):
    """Disable sharing for a project (keeps token and hash for re-enabling)."""
    sb = get_supabase()

    proj_resp = sb.table("projects").select("id, created_by").eq("id", project_id).execute()
    if not proj_resp.data:
        raise HTTPException(status_code=404, detail="Project not found")
    project = proj_resp.data[0]

    if user["role"] == "analyst" and project["created_by"] != user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    sb.table("projects").update({"is_shared": False}).eq("id", project_id).execute()
    return {"message": "Sharing disabled"}


@router.post("/shared/{share_token}/verify")
def verify_shared_project(share_token: str, body: VerifyShareRequest, request: Request):
    """
    Public endpoint — no auth required.
    Verify password and return the full project report data.
    """
    sb = get_supabase()

    # Look up project by share_token where sharing is enabled
    proj_resp = (
        sb.table("projects")
        .select("*")
        .eq("share_token", share_token)
        .eq("is_shared", True)
        .execute()
    )
    if not proj_resp.data:
        raise HTTPException(status_code=404, detail="Shared project not found")
    project = proj_resp.data[0]

    # Verify password
    stored_hash = project.get("share_password_hash")
    if not stored_hash or not _verify_password(body.password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid password")

    project_id = project["id"]

    # ── Log the view and (best-effort) notify Slack ──────────────────────
    _record_share_view(sb, project, share_token, request)

    # ── Fetch all related data ────────────────────────────────────────────
    data_resp = sb.table("project_data").select("*").eq("project_id", project_id).execute()
    reports_resp = (
        sb.table("reports").select("*").eq("project_id", project_id)
        .order("generated_at", desc=True).execute()
    )
    scores_resp = sb.table("analyst_scores").select("*").eq("project_id", project_id).execute()

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
        screenshot_url = sp.get("viewport") or sp.get("full_page") or sp.get("desktop") or sp.get("mobile")
    elif isinstance(sp, str) and sp:
        screenshot_url = sp

    # ── Lens scores ───────────────────────────────────────────────────────
    automated = project_data.get("automated_scores") or {}
    analyst_map: dict[str, Any] = {}
    for s in analyst_scores:
        ln = s.get("lens_name", "")
        if ln not in analyst_map or s.get("site_url") == project.get("primary_url"):
            analyst_map[ln] = s

    lens_scores: list[dict[str, Any]] = []
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
        lens_scores.append({
            "lens_id": lid,
            "lens_name": LENS_MAP[lid],
            "score": math.floor(score + 0.5) if score is not None else None,
            "max_score": 20.0,
        })

    # ── Retina score ──────────────────────────────────────────────────────
    scored = [ls["score"] for ls in lens_scores if ls["score"] is not None]
    retina_score = round(sum(scored), 2) if scored else report.get("retina_score")

    # ── Technology stack ──────────────────────────────────────────────────
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
            items = list(qd)
        elif isinstance(qd, dict):
            items = list(qd.get("items", []))
        recs.append({"quadrant": QUADRANT_LABELS[qid], "items": items})

    # ── Lens details (all 5 lenses) ──────────────────────────────────────
    all_interps = project_data.get("interpretations") or {}
    interp_key_map = {
        "performance_technical_health": "performance",
        "seo_ai_visibility": "seo",
        "brand_messaging": "brand_messaging",
        "experience_design": "experience_design",
        "conversion_strategy": "conversion_strategy",
    }
    user_edits = all_interps.get("_user_edits") or {}
    all_artifacts = all_interps.get("_artifacts") or {}
    primary_url = project.get("primary_url", "")

    lenses: list[dict[str, Any]] = []
    for lens_id in LENS_ORDER:
        # Interpretations
        interps: dict[str, Any] = {}
        primary_key = interp_key_map.get(lens_id, "")
        if primary_key in all_interps:
            interps[primary_key] = all_interps[primary_key]
        analyst_lenses_interp = all_interps.get("analyst_lenses") or {}
        if lens_id in analyst_lenses_interp:
            interps["analyst_narrative"] = analyst_lenses_interp[lens_id]

        # Analyst sub-scores + observations
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

        sub_scores_raw = analyst_entry.get("sub_scores") or {}
        analyst_sub: dict[str, Any] = {}
        if isinstance(sub_scores_raw, dict):
            for k, v in sub_scores_raw.items():
                if isinstance(v, dict) and "score" in v:
                    analyst_sub[k] = {"score": float(v["score"]), "observation": v.get("observation", "")}
                elif isinstance(v, (int, float)):
                    analyst_sub[k] = {"score": float(v), "observation": ""}
                else:
                    analyst_sub[k] = {"score": 0.0, "observation": ""}

        if lens_id in DEFAULT_SUB_DIMS:
            for dim_key in DEFAULT_SUB_DIMS[lens_id]:
                if dim_key not in analyst_sub:
                    analyst_sub[dim_key] = {"score": 0.0, "observation": ""}

        observations = analyst_entry.get("raw_observations") or "" if isinstance(analyst_entry, dict) else ""

        current_lens = next((ls for ls in lens_scores if ls["lens_id"] == lens_id), None)

        lenses.append({
            "lens_id": lens_id,
            "lens_name": LENS_MAP[lens_id],
            "lens_color": LENS_COLORS[lens_id],
            "lens_score": current_lens["score"] if current_lens else None,
            "max_score": 20.0,
            "lighthouse_data": project_data.get("lighthouse_data") or {},
            "builtwith_data": project_data.get("builtwith_data") or {},
            "interpretations": interps,
            "analyst_sub_scores": analyst_sub,
            "analyst_observations": observations,
            "user_observations": user_edits.get(lens_id),
            "artifacts": all_artifacts.get(lens_id) or [],
        })

    return {
        "project": {
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
        },
        "lenses": lenses,
    }


# ── Share view logging + Slack notify ─────────────────────────────────────────

def _client_ip(request: Request) -> str | None:
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    client = request.client
    return client.host if client else None


def _record_share_view(sb, project: dict, share_token: str, request: Request) -> None:
    """Insert a share_views row and fire a Slack notification. Never raises."""
    ip = _client_ip(request)
    user_agent = request.headers.get("user-agent")

    try:
        sb.table("share_views").insert({
            "project_id": project["id"],
            "share_token": share_token,
            "ip_address": ip,
            "user_agent": user_agent,
        }).execute()
    except Exception:
        logger.exception("Failed to insert share_views row")

    try:
        _notify_slack_share_view(project)
    except Exception:
        logger.exception("Failed to send Slack share-view notification")


def _notify_slack_share_view(project: dict) -> None:
    webhook_url = os.getenv("SLACK_SHARE_WEBHOOK_URL", "").strip()
    logger.info("Slack webhook URL present: %s", bool(webhook_url))
    if not webhook_url:
        return

    project_name = project.get("name") or "(unnamed project)"
    cohort = (
        project.get("cohort_name")
        or project.get("entity_name")
        or project.get("client_name")
        or project.get("primary_url")
    )
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [f"*Shared report viewed:* {project_name}"]
    if cohort:
        lines.append(f"• Cohort/entity: {cohort}")
    lines.append(f"• Viewed at: {timestamp}")

    try:
        resp = httpx.post(webhook_url, json={"text": "\n".join(lines)}, timeout=5)
        logger.info("Slack webhook response status: %s", resp.status_code)
    except Exception as e:
        logger.error("Slack webhook error: %s", str(e))


# ── Utility ───────────────────────────────────────────────────────────────────

def _extract_tech_stack(builtwith_data: dict) -> dict[str, list[str]]:
    """Extract key technology stack info from BuiltWith data.

    Uses name overrides for common tools (highest priority) then falls
    back to BuiltWith category matching.  Mirrors the logic in
    projects.py so analyst and shared views show identical results.
    """
    techs = builtwith_data.get("technologies") or []
    if not techs:
        return {}

    CATEGORY_MAP = {
        "Hosted Solution": "cms", "Headless": "cms", "Enterprise": "cms",
        "CMS": "cms", "WordPress": "cms", "Blogs": "cms", "Ecommerce": "cms",
        "CDN": "cdn", "Content Delivery Network": "cdn",
        "Analytics": "analytics", "Analytics and tracking": "analytics",
        "Audience Measurement": "analytics", "Visitor Count Tracking": "analytics",
        "Tag Management": "analytics",
        "CRM": "crm", "Marketing automation": "crm", "Live chat": "crm",
        "Feedback Forms and Surveys": "crm", "Transactional Email": "crm",
    }

    NAME_OVERRIDES = {
        "Webflow": "cms", "WordPress": "cms", "Contentful": "cms",
        "Shopify": "cms", "Squarespace": "cms", "Wix": "cms", "Drupal": "cms",
        "HubSpot COS": "cms", "HubSpot CMS": "cms",
        "HubSpot": "crm", "Salesforce": "crm", "Marketo": "crm",
        "Pardot": "crm", "Mailchimp": "crm", "ActiveCampaign": "crm",
        "Google Analytics": "analytics", "Google Analytics 4": "analytics",
        "Google Tag Manager": "analytics", "Hotjar": "analytics",
        "Mixpanel": "analytics", "Segment": "analytics",
        "Cloudflare": "cdn", "Fastly": "cdn", "Akamai": "cdn",
        "Amazon CloudFront": "cdn", "KeyCDN": "cdn",
        "Bunny CDN": "cdn", "StackPath": "cdn",
    }

    result: dict[str, set[str]] = {}
    seen: set[str] = set()

    for tech in techs:
        name = tech.get("name", "").strip()
        if not name:
            continue

        cat = NAME_OVERRIDES.get(name)
        if cat:
            if name not in seen:
                result.setdefault(cat, set()).add(name)
                seen.add(name)
            continue

        for bw_cat in tech.get("categories", []):
            cat = CATEGORY_MAP.get(bw_cat)
            if cat and name not in seen:
                result.setdefault(cat, set()).add(name)
                seen.add(name)
                break

    return {k: sorted(v)[:8] for k, v in result.items() if v}
