"""AI-powered recommendation generator for Retina projects.

Uses Claude to generate structured recommendations based on all available
project data: lighthouse, builtwith, interpretations, and analyst scores.
Stores results in the report's quadrant_data field.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import anthropic
from dotenv import load_dotenv

from app.services.supabase_client import get_supabase

load_dotenv()
logger = logging.getLogger(__name__)

QUADRANT_ORDER = ["no_brainers", "quick_wins", "growth_moves", "transformational"]


def _sum_sub_scores(sub: dict) -> float:
    """Sum sub_scores handling both {key: float} and {key: {score, observation}} shapes."""
    total = 0.0
    for v in sub.values():
        if isinstance(v, (int, float)):
            total += float(v)
        elif isinstance(v, dict) and "score" in v:
            total += float(v["score"])
    return total

SYSTEM_PROMPT = """\
You are Retina, the intelligence engine behind Matic Digital's website \
evaluation platform. Matic is a strategic digital consultancy that helps \
brands understand where online performance is being won or lost.

Your voice is that of a senior strategist — confident, direct, and always \
connecting technical findings to business outcomes. Gaps are opportunities, \
not failures. Every recommendation must reference specific data from the \
input and connect to measurable impact.

## Retina's Five Lenses

Each website is scored across five lenses (0-20 points each, 100 total):

1. **Performance & Platform** (automated): Speed, stability, Core Web Vitals, \
technical infrastructure. Sub-dimensions: Page Speed, Core Web Vitals, \
Mobile Optimization, Security & Accessibility.

2. **SEO & AI Visibility** (automated): Discoverability to search engines and \
AI platforms. Sub-dimensions: Technical SEO, On-Page SEO, Content Strategy, \
AI Readiness.

3. **Brand & Messaging** (analyst): How clearly the website communicates who \
it is for and why it matters. Sub-dimensions: Brand Visual Language (5), \
Brand Voice & Messaging (5), Value Proposition (5), Brand Differentiation (5).

4. **Experience & Design** (analyst): How intuitive, modern, and intentional \
the digital experience feels. Sub-dimensions: Interface Design (5), \
Content Taxonomy (5), Navigation Architecture (5), Responsiveness (5).

5. **Conversion & Strategy** (analyst): How effectively the site turns \
attention into action. Sub-dimensions: Call to Action Logic (5), \
Lead Capture Form Design (5), Trust Signals (5), Funnel Design (5).

## Recommendation Quadrants

Categorize each recommendation into exactly one quadrant:

- **no_brainers**: Low effort, high impact. Quick technical fixes or content \
changes that immediately improve the score. Examples: adding meta descriptions, \
fixing broken links, adding alt text, enabling compression.

- **quick_wins**: Low-to-medium effort, moderate impact. Targeted improvements \
that can be completed in 1-2 sprints. Examples: redesigning CTA buttons, \
adding testimonials section, improving form UX.

- **growth_moves**: Medium effort, high impact. Strategic improvements worth \
investing in over a quarter. Examples: content strategy overhaul, navigation \
restructure, brand voice guidelines.

- **transformational**: High effort, very high impact. Major initiatives that \
redefine the site's competitive position. Examples: full redesign, conversion \
funnel rebuild, personalization engine.

## Output Requirements

For each recommendation provide:
- **title**: A concise action-oriented title (e.g., "Add Structured Data Markup")
- **description**: 2-3 sentences explaining what to do and why it matters. \
Reference specific data points from the input. Frame every recommendation in \
terms of business impact: conversion rates, visitor confidence, search \
visibility, or competitive positioning.
- **lens**: Which Retina lens this relates to. Must be exactly one of: \
"Performance & Platform", "SEO & AI Visibility", "Brand & Messaging", \
"Experience & Design", "Conversion & Strategy"

Generate 8-12 recommendations total, distributed across all four quadrants. \
Prioritize the areas with the lowest scores or most significant gaps. \
Every recommendation must be specific to THIS site — no generic advice.

Return ONLY valid JSON matching this exact schema:
{
  "no_brainers": [{"title": "...", "description": "...", "lens": "..."}],
  "quick_wins": [{"title": "...", "description": "...", "lens": "..."}],
  "growth_moves": [{"title": "...", "description": "...", "lens": "..."}],
  "transformational": [{"title": "...", "description": "...", "lens": "..."}]
}

No markdown, no code fences — just the JSON.\
"""


def generate_recommendations(project_id: str) -> dict[str, Any]:
    """Generate AI recommendations for a project and store in report.

    Gathers all available data, calls Claude, and updates the report's
    quadrant_data field.

    Returns the generated quadrant_data dict.
    """
    # Ensure .env is loaded from project root
    from pathlib import Path
    load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env", override=True)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    sb = get_supabase()

    # Gather project data
    proj_resp = sb.table("projects").select("*").eq("id", project_id).execute()
    if not proj_resp.data:
        raise ValueError("Project not found")
    project = proj_resp.data[0]

    data_resp = (
        sb.table("project_data").select("*").eq("project_id", project_id).execute()
    )
    project_data = data_resp.data[0] if data_resp.data else {}

    scores_resp = (
        sb.table("analyst_scores").select("*").eq("project_id", project_id).execute()
    )
    analyst_scores = scores_resp.data or []

    reports_resp = (
        sb.table("reports")
        .select("*")
        .eq("project_id", project_id)
        .order("generated_at", desc=True)
        .limit(1)
        .execute()
    )
    report = reports_resp.data[0] if reports_resp.data else None

    # Build context for Claude
    context_parts: list[str] = []

    context_parts.append(f"Website: {project['primary_url']}")
    context_parts.append(f"Project: {project['name']}")

    if report and report.get("retina_score"):
        context_parts.append(f"Overall Retina Score: {report['retina_score']}/100")

    # Lighthouse data
    lh = project_data.get("lighthouse_data") or {}
    if lh:
        context_parts.append("\n## Lighthouse Performance Data")
        for device in ["mobile", "desktop"]:
            if device in lh:
                scores = lh[device].get("lighthouse_scores", {})
                vitals = lh[device].get("core_web_vitals", {})
                context_parts.append(f"\n### {device.title()}")
                if scores:
                    context_parts.append(f"Lighthouse Scores: {json.dumps(scores)}")
                if vitals:
                    context_parts.append(f"Core Web Vitals: {json.dumps(vitals)}")

    # BuiltWith data
    bw = project_data.get("builtwith_data") or {}
    if bw:
        techs = bw.get("technologies", [])
        if techs:
            tech_names = [t["name"] for t in techs[:20]]
            context_parts.append(f"\n## Technology Stack\n{', '.join(tech_names)}")

    # Automated scores
    auto_scores = project_data.get("automated_scores") or {}
    if auto_scores:
        context_parts.append("\n## Automated Lens Scores")
        for lens, data in auto_scores.items():
            if isinstance(data, dict) and data.get("score") is not None:
                context_parts.append(f"- {lens}: {data['score']}/20")

    # Analyst scores
    if analyst_scores:
        context_parts.append("\n## Analyst Lens Scores")
        for s in analyst_scores:
            sub = s.get("sub_scores", {})
            total = _sum_sub_scores(sub)
            context_parts.append(f"- {s['lens_name']}: {total:.1f}/20")
            # Include per-sub-dimension scores and observations
            for dim_key, dim_val in sub.items():
                if isinstance(dim_val, dict):
                    dim_score = dim_val.get("score", 0)
                    dim_obs = dim_val.get("observation", "")
                    label = dim_key.replace("_", " ").title()
                    context_parts.append(f"  - {label}: {dim_score}/5")
                    if dim_obs:
                        context_parts.append(f"    {dim_obs[:200]}")
                elif isinstance(dim_val, (int, float)):
                    label = dim_key.replace("_", " ").title()
                    context_parts.append(f"  - {label}: {dim_val}/5")
            if s.get("raw_observations"):
                obs = s["raw_observations"][:500]
                context_parts.append(f"  Overall observations: {obs}")

    # User-edited observations (take priority over AI-generated)
    interps = project_data.get("interpretations") or {}
    user_edits = interps.get("_user_edits") or {}
    if user_edits:
        context_parts.append("\n## Analyst-Edited Observations")
        for lens_key, obs_text in user_edits.items():
            if obs_text and not lens_key.startswith("_"):
                label = lens_key.replace("_", " ").title()
                context_parts.append(f"\n### {label}")
                context_parts.append(str(obs_text)[:500])

    # AI Interpretations
    if interps:
        context_parts.append("\n## AI Interpretations")
        for key, val in interps.items():
            if key.startswith("_") or key == "analyst_lenses":
                continue  # Skip internal keys
            if isinstance(val, dict) and val.get("section_narrative"):
                context_parts.append(f"\n### {key}")
                context_parts.append(val["section_narrative"])

    user_message = "\n".join(context_parts)
    logger.info(
        "Generating recommendations for %s (%d chars context)",
        project_id,
        len(user_message),
    )

    # Call Claude
    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    # Parse response
    raw = response.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

    quadrant_data = json.loads(raw)

    # Validate structure
    for q in QUADRANT_ORDER:
        if q not in quadrant_data:
            quadrant_data[q] = []
        items = quadrant_data[q]
        if not isinstance(items, list):
            quadrant_data[q] = []

    # Store in report
    if report:
        sb.table("reports").update({"quadrant_data": quadrant_data}).eq(
            "id", report["id"]
        ).execute()
        logger.info("Updated existing report with recommendations")
    else:
        # Create a minimal report if none exists
        from app.services.projects import save_report

        # Calculate retina score from available data
        retina_score = 0.0
        for s in analyst_scores:
            sub = s.get("sub_scores", {})
            retina_score += _sum_sub_scores(sub)
        for lens, data in auto_scores.items():
            if isinstance(data, dict) and data.get("score") is not None:
                # Only add auto scores for lenses without analyst scores
                analyst_lens_names = {s["lens_name"] for s in analyst_scores}
                if lens not in analyst_lens_names:
                    retina_score += data["score"]

        save_report(
            project_id=project_id,
            retina_score=round(retina_score, 2),
            ai_analysis={},
            quadrant_data=quadrant_data,
        )
        logger.info("Created new report with recommendations")

    return quadrant_data
