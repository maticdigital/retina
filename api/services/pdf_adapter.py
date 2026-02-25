"""Adapter that fetches project data from Supabase and builds an AnalysisRun.

The AnalysisRun model is what renderer.py expects. This adapter bridges the
gap between the Supabase-backed web app and the existing PDF renderer that
was written for the CLI pipeline.
"""

from __future__ import annotations

import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import httpx

from app.services.supabase_client import get_supabase

from retina.models.normalized import (
    AIAnalysis,
    AnalysisRun,
    CoreWebVitals,
    EffortLevel,
    ImpactLevel,
    LensScore,
    LighthouseScores,
    PerformanceData,
    Recommendation,
    RetinaScore,
    ScreenshotData,
    ScoringLensType,
    SiteReport,
    StrategicQuadrant,
    Technology,
    TechStackData,
    DeviceStrategy,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------

LENS_KEY_TO_TYPE = {
    "brand_messaging": ScoringLensType.BRAND_MESSAGING,
    "experience_design": ScoringLensType.EXPERIENCE_DESIGN,
    "conversion_strategy": ScoringLensType.CONVERSION_STRATEGY,
}

# Quadrant name mapping: recommendations.py uses plural keys like "no_brainers"
# while the normalized model uses StrategicQuadrant enum values
QUADRANT_MAP = {
    "no_brainers": StrategicQuadrant.NO_BRAINER,
    "quick_wins": StrategicQuadrant.QUICK_WIN,
    "growth_moves": StrategicQuadrant.GROWTH_MOVE,
    "transformational": StrategicQuadrant.TRANSFORMATIONAL,
}

# Sub-dimension display names for each analyst lens
SUB_DIM_LABELS = {
    "brand_visual_language": "Brand Visual Language",
    "brand_voice_messaging": "Brand Voice & Messaging",
    "value_proposition": "Value Proposition",
    "brand_differentiation": "Brand Differentiation",
    "interface_design": "Interface Design",
    "content_taxonomy": "Content Taxonomy",
    "navigation_architecture": "Navigation Architecture",
    "responsiveness": "Responsiveness",
    "call_to_action_logic": "Call to Action Logic",
    "lead_capture_form_design": "Lead Capture Form Design",
    "trust_signals": "Trust Signals",
    "funnel_design": "Funnel Design",
}


def _sum_sub_scores(sub: dict) -> float:
    """Sum sub_scores handling both {key: float} and {key: {score, observation}} shapes."""
    total = 0.0
    for v in sub.values():
        if isinstance(v, (int, float)):
            total += float(v)
        elif isinstance(v, dict) and "score" in v:
            total += float(v["score"])
    return total


def _extract_breakdown(sub_scores: dict) -> dict[str, float]:
    """Extract a flat {dim_key: score} breakdown from sub_scores."""
    breakdown: dict[str, float] = {}
    for k, v in sub_scores.items():
        if isinstance(v, (int, float)):
            breakdown[k] = float(v)
        elif isinstance(v, dict) and "score" in v:
            breakdown[k] = float(v["score"])
    return breakdown


def _extract_observations(sub_scores: dict) -> str:
    """Extract concatenated observations from sub_scores."""
    parts: list[str] = []
    for k, v in sub_scores.items():
        if isinstance(v, dict) and v.get("observation"):
            label = SUB_DIM_LABELS.get(k, k.replace("_", " ").title())
            parts.append(f"{label}: {v['observation']}")
    return "\n".join(parts)


def _extract_subdim_observations(sub_scores: dict) -> dict[str, str]:
    """Extract per-subdimension observation text from sub_scores.

    Returns a dict of {subdim_key: observation_text} for use
    in lens page rendering.
    """
    obs: dict[str, str] = {}
    for k, v in sub_scores.items():
        if isinstance(v, dict) and v.get("observation"):
            obs[k] = v["observation"]
    return obs


# ---------------------------------------------------------------------------
# Performance data mapping
# ---------------------------------------------------------------------------


def _build_performance(lighthouse_data: dict) -> list[PerformanceData]:
    """Map Supabase lighthouse_data to PerformanceData models."""
    results: list[PerformanceData] = []
    for device_key, strategy in [("mobile", DeviceStrategy.MOBILE), ("desktop", DeviceStrategy.DESKTOP)]:
        device_data = lighthouse_data.get(device_key)
        if not device_data:
            continue

        lh_scores_raw = device_data.get("lighthouse_scores", {})
        cwv_raw = device_data.get("core_web_vitals", {})

        lh_scores = LighthouseScores(
            performance=lh_scores_raw.get("performance"),
            accessibility=lh_scores_raw.get("accessibility"),
            best_practices=lh_scores_raw.get("best_practices") or lh_scores_raw.get("best-practices"),
            seo=lh_scores_raw.get("seo"),
        )

        cwv = CoreWebVitals(
            largest_contentful_paint_ms=cwv_raw.get("largest_contentful_paint_ms") or cwv_raw.get("LCP"),
            first_contentful_paint_ms=cwv_raw.get("first_contentful_paint_ms") or cwv_raw.get("FCP"),
            cumulative_layout_shift=cwv_raw.get("cumulative_layout_shift") or cwv_raw.get("CLS"),
            interaction_to_next_paint_ms=cwv_raw.get("interaction_to_next_paint_ms") or cwv_raw.get("INP"),
            total_blocking_time_ms=cwv_raw.get("total_blocking_time_ms") or cwv_raw.get("TBT"),
            speed_index_ms=cwv_raw.get("speed_index_ms") or cwv_raw.get("SI"),
        )

        results.append(PerformanceData(
            strategy=strategy,
            lighthouse_scores=lh_scores,
            core_web_vitals=cwv,
        ))

    return results


# ---------------------------------------------------------------------------
# Tech stack mapping
# ---------------------------------------------------------------------------


def _build_tech_stack(builtwith_data: dict) -> TechStackData:
    """Map Supabase builtwith_data to TechStackData model."""
    techs: list[Technology] = []
    for t in builtwith_data.get("technologies", []):
        techs.append(Technology(
            name=t.get("name", ""),
            description=t.get("description"),
            link=t.get("link"),
            categories=t.get("categories", []),
            tag=t.get("tag"),
        ))
    return TechStackData(
        technologies=techs,
        meta=builtwith_data.get("meta", {}),
        social_profiles=builtwith_data.get("social_profiles", []),
    )


# ---------------------------------------------------------------------------
# Screenshot handling
# ---------------------------------------------------------------------------


def _download_image(url: str, dest_dir: Path) -> str | None:
    """Download an image from a URL to a local temp directory. Returns local path."""
    try:
        resp = httpx.get(url, timeout=30, follow_redirects=True)
        resp.raise_for_status()
        # Determine extension from content-type
        ct = resp.headers.get("content-type", "")
        ext = ".png"
        if "jpeg" in ct or "jpg" in ct:
            ext = ".jpg"
        elif "webp" in ct:
            ext = ".webp"

        filename = f"{hash(url) & 0xFFFFFFFF:08x}{ext}"
        local_path = dest_dir / filename
        local_path.write_bytes(resp.content)
        return str(local_path)
    except Exception as e:
        logger.warning("Failed to download image %s: %s", url, e)
        return None


def _get_screenshot_url(sb, project_id: str) -> str | None:
    """Get the primary screenshot URL from Supabase storage."""
    try:
        # Check for uploaded screenshots in the screenshots bucket
        files = sb.storage.from_("screenshots").list(project_id)
        if files:
            # Use the first file found
            remote_path = f"{project_id}/{files[0]['name']}"
            return sb.storage.from_("screenshots").get_public_url(remote_path)
    except Exception as e:
        logger.warning("Could not list screenshots: %s", e)
    return None


# ---------------------------------------------------------------------------
# Recommendations mapping
# ---------------------------------------------------------------------------


def _build_recommendations(quadrant_data: dict) -> list[Recommendation]:
    """Map report quadrant_data to list of Recommendation models."""
    recs: list[Recommendation] = []

    for quad_key, quad_enum in QUADRANT_MAP.items():
        items = quadrant_data.get(quad_key, [])
        if not isinstance(items, list):
            continue

        # Determine effort/impact from quadrant
        if quad_enum == StrategicQuadrant.NO_BRAINER:
            effort, impact = EffortLevel.LOW, ImpactLevel.HIGH
        elif quad_enum == StrategicQuadrant.QUICK_WIN:
            effort, impact = EffortLevel.LOW, ImpactLevel.LOW
        elif quad_enum == StrategicQuadrant.GROWTH_MOVE:
            effort, impact = EffortLevel.HIGH, ImpactLevel.HIGH
        else:  # TRANSFORMATIONAL
            effort, impact = EffortLevel.HIGH, ImpactLevel.HIGH

        for item in items:
            recs.append(Recommendation(
                title=item.get("title", ""),
                description=item.get("description", ""),
                effort=effort,
                impact=impact,
                quadrant=quad_enum,
                rationale=item.get("description", ""),
            ))

    return recs


# ---------------------------------------------------------------------------
# Main adapter
# ---------------------------------------------------------------------------


def build_analysis_run(project_id: str) -> dict:
    """Fetch all project data from Supabase and build an AnalysisRun.

    This is the bridge between the Supabase-backed web app and the
    existing PDF renderer. It produces the exact model that render_pdf()
    expects, plus extra metadata for the render call.

    Args:
        project_id: The project UUID.

    Returns:
        A dict with keys:
            analysis: AnalysisRun — the core data model
            project_title: str | None — display name for the project
            analyst_name: str | None — name of the analyst
            subdim_observations: dict — per-lens per-subdim observation text
    """
    sb = get_supabase()

    # ── Fetch all data ────────────────────────────────────────────────────

    # Project record
    proj_resp = sb.table("projects").select("*").eq("id", project_id).execute()
    if not proj_resp.data:
        raise ValueError(f"Project not found: {project_id}")
    project = proj_resp.data[0]

    # Project data (lighthouse, builtwith, automated scores, interpretations)
    data_resp = sb.table("project_data").select("*").eq("project_id", project_id).execute()
    project_data = data_resp.data[0] if data_resp.data else {}

    # Analyst scores
    scores_resp = sb.table("analyst_scores").select("*").eq("project_id", project_id).execute()
    analyst_scores = scores_resp.data or []

    # Latest report
    reports_resp = (
        sb.table("reports")
        .select("*")
        .eq("project_id", project_id)
        .order("generated_at", desc=True)
        .limit(1)
        .execute()
    )
    report = reports_resp.data[0] if reports_resp.data else None

    # ── Build lens scores ─────────────────────────────────────────────────

    lens_scores: list[LensScore] = []

    # Automated scores (Performance & Platform, SEO & AI Visibility)
    auto_scores = project_data.get("automated_scores") or {}
    for lens_key, lens_type in [
        ("performance_technical_health", ScoringLensType.PERFORMANCE_TECHNICAL),
        ("seo_ai_visibility", ScoringLensType.SEO_AI_VISIBILITY),
    ]:
        data = auto_scores.get(lens_key, {})
        if isinstance(data, dict) and data.get("score") is not None:
            lens_scores.append(LensScore(
                lens=lens_type,
                score=float(data["score"]),
                breakdown=data.get("breakdown", {}),
                notes=data.get("notes"),
                is_automated=True,
            ))

    # Analyst scores (Brand, Experience, Conversion)
    subdim_observations: dict[str, dict[str, str]] = {}
    analyst_name: str | None = None

    for a_score in analyst_scores:
        lens_name = a_score.get("lens_name", "")
        lens_type = LENS_KEY_TO_TYPE.get(lens_name)
        if not lens_type:
            continue

        # Track analyst name from first score that has one
        if not analyst_name and a_score.get("analyst_name"):
            analyst_name = a_score["analyst_name"]

        sub_scores = a_score.get("sub_scores") or {}
        total = _sum_sub_scores(sub_scores)
        breakdown = _extract_breakdown(sub_scores)

        # Observations: prefer user raw_observations, then AI-generated
        raw_obs = a_score.get("raw_observations") or ""
        sub_obs = _extract_observations(sub_scores)
        notes = raw_obs or sub_obs or None

        # Per-subdim observations for lens page rendering
        per_subdim = _extract_subdim_observations(sub_scores)
        if per_subdim:
            subdim_observations[lens_name] = per_subdim

        lens_scores.append(LensScore(
            lens=lens_type,
            score=min(round(total, 2), 20.0),
            breakdown=breakdown,
            notes=notes,
            is_automated=False,
        ))

    # ── Build RetinaScore ─────────────────────────────────────────────────

    retina_score_value = 0.0
    if report and report.get("retina_score"):
        retina_score_value = float(report["retina_score"])
    else:
        retina_score_value = sum(ls.score for ls in lens_scores)

    retina_score = RetinaScore(
        lens_scores=lens_scores,
        total=round(retina_score_value, 2),
    )

    # ── Performance data ──────────────────────────────────────────────────

    lighthouse_data = project_data.get("lighthouse_data") or {}
    performance = _build_performance(lighthouse_data)

    # ── Tech stack ────────────────────────────────────────────────────────

    builtwith_data = project_data.get("builtwith_data") or {}
    tech_stack = _build_tech_stack(builtwith_data) if builtwith_data else None

    # ── Screenshots ───────────────────────────────────────────────────────

    # Create a temp directory for downloaded images
    tmp_dir = Path(tempfile.mkdtemp(prefix="retina_pdf_"))
    screenshots = None

    screenshot_url = _get_screenshot_url(sb, project_id)
    if screenshot_url:
        local_path = _download_image(screenshot_url, tmp_dir)
        if local_path:
            screenshots = ScreenshotData(viewport=local_path)

    # ── Build SiteReport ──────────────────────────────────────────────────

    primary_site = SiteReport(
        url=project["primary_url"],
        normalized_url=project["primary_url"],
        performance=performance,
        tech_stack=tech_stack,
        screenshots=screenshots,
        retina_score=retina_score,
    )

    # ── AI Analysis (from quadrant_data / interpretations) ────────────────

    ai_analysis = None
    quadrant_data = (report or {}).get("quadrant_data") or {}
    interpretations = project_data.get("interpretations") or {}

    # Executive summary from interpretations
    exec_summary = ""
    overall_interp = interpretations.get("overall", {})
    if isinstance(overall_interp, dict):
        retina_interp = overall_interp.get("retina_score", {})
        if isinstance(retina_interp, dict):
            exec_summary = retina_interp.get("what", "")

    recommendations = _build_recommendations(quadrant_data)

    if exec_summary or recommendations:
        ai_analysis = AIAnalysis(
            executive_summary=exec_summary,
            recommendations=recommendations,
        )

    # ── Assemble AnalysisRun ──────────────────────────────────────────────

    created_at = datetime.now(timezone.utc)
    if project.get("created_at"):
        try:
            created_at = datetime.fromisoformat(project["created_at"].replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass

    analysis_run = AnalysisRun(
        run_id=project_id,
        created_at=created_at,
        primary_site=primary_site,
        competitors=[],
        ai_analysis=ai_analysis,
    )

    # Project title from project record
    project_title = project.get("name") or project.get("primary_url", "")

    logger.info(
        "Built AnalysisRun for %s: score=%.1f, %d lens scores, %d recommendations",
        project_id,
        retina_score_value,
        len(lens_scores),
        len(recommendations),
    )

    return {
        "analysis": analysis_run,
        "project_title": project_title,
        "analyst_name": analyst_name,
        "subdim_observations": subdim_observations,
    }
