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


def _format_sub_dim(dim_key: str, dim_val: Any) -> str | None:
    """Format a single sub-dimension for the prompt. Returns None if empty."""
    label = dim_key.replace("_", " ").title()
    if isinstance(dim_val, dict):
        score = dim_val.get("score", 0)
        obs = dim_val.get("observation", "")
        if obs:
            return f"- {label}: {score}/5 — {obs}"
        return f"- {label}: {score}/5"
    elif isinstance(dim_val, (int, float)):
        return f"- {label}: {dim_val}/5"
    return None


def _get_overall_observations(analyst_row: dict) -> str:
    """Get the best available overall observations text for an analyst lens."""
    # User-edited observations take priority
    if analyst_row.get("refined_observations"):
        return analyst_row["refined_observations"]
    if analyst_row.get("raw_observations"):
        return analyst_row["raw_observations"]
    return ""


def generate_recommendations(project_id: str) -> dict[str, Any]:
    """Generate AI recommendations for a project and store in report.

    Fetches ALL data fresh from Supabase immediately before building
    the Claude prompt — never uses cached or in-memory data.

    Returns the generated quadrant_data dict.
    """
    # Ensure .env is loaded from project root
    from pathlib import Path
    load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env", override=True)
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    sb = get_supabase()

    # ── Fetch ALL fresh data from Supabase ─────────────────────────────────

    proj_resp = sb.table("projects").select("*").eq("id", project_id).execute()
    if not proj_resp.data:
        raise ValueError("Project not found")
    project = proj_resp.data[0]

    data_resp = (
        sb.table("project_data").select("*").eq("project_id", project_id).execute()
    )
    project_data = data_resp.data[0] if data_resp.data else {}

    # Fresh analyst scores — always re-fetch
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

    # ── Build structured prompt ────────────────────────────────────────────

    parts: list[str] = []
    parts.append(
        f"Generate strategic recommendations for {project['name']} "
        f"({project['primary_url']})."
    )

    # --- AUTOMATED ANALYSIS ---

    parts.append("\nAUTOMATED ANALYSIS:")

    # Performance & Platform
    lh = project_data.get("lighthouse_data") or {}
    auto_scores = project_data.get("automated_scores") or {}
    perf_score = auto_scores.get("performance_technical_health", {})
    perf_total = perf_score.get("score", "N/A") if isinstance(perf_score, dict) else "N/A"
    parts.append(f"\nPerformance & Platform ({perf_total}/20):")

    # Core Web Vitals from mobile (primary)
    mobile_lh = lh.get("mobile", {})
    vitals = mobile_lh.get("core_web_vitals", {})
    if vitals:
        lcp = vitals.get("LCP", "N/A")
        fcp = vitals.get("FCP", "N/A")
        cls = vitals.get("CLS", "N/A")
        tbt = vitals.get("TBT", "N/A")
        parts.append(f"- LCP: {lcp} | FCP: {fcp} | CLS: {cls} | TBT: {tbt}")

    # Lighthouse category scores
    for device in ["mobile", "desktop"]:
        dev_data = lh.get(device, {})
        lh_scores = dev_data.get("lighthouse_scores", {})
        if lh_scores:
            perf_s = lh_scores.get("performance", "N/A")
            acc_s = lh_scores.get("accessibility", "N/A")
            bp_s = lh_scores.get("best_practices", lh_scores.get("best-practices", "N/A"))
            seo_s = lh_scores.get("seo", "N/A")
            parts.append(
                f"- Lighthouse ({device.title()}) — Performance: {perf_s} | "
                f"Accessibility: {acc_s} | Best Practices: {bp_s} | SEO: {seo_s}"
            )

    # Technology stack
    bw = project_data.get("builtwith_data") or {}
    techs = bw.get("technologies", [])
    if techs:
        tech_names = [t["name"] for t in techs[:20]]
        parts.append(f"- Stack: {', '.join(tech_names)}")

    # SEO & AI Visibility
    seo_score = auto_scores.get("seo_ai_visibility", {})
    seo_total = seo_score.get("score", "N/A") if isinstance(seo_score, dict) else "N/A"
    parts.append(f"\nSEO & AI Visibility ({seo_total}/20):")

    # Include SEO sub-dimension details if available
    if isinstance(seo_score, dict):
        seo_subs = seo_score.get("sub_scores", {})
        for sk, sv in seo_subs.items():
            label = sk.replace("_", " ").title()
            if isinstance(sv, dict):
                parts.append(f"- {label}: {sv.get('score', 'N/A')}/5")
            elif isinstance(sv, (int, float)):
                parts.append(f"- {label}: {sv}/5")

    # --- ANALYST ASSESSMENT ---

    # Map analyst scores by lens_name for easy lookup
    analyst_by_lens: dict[str, dict] = {}
    for s in analyst_scores:
        analyst_by_lens[s.get("lens_name", "")] = s

    # Also check for user-edited observations stored in project_data
    interps = project_data.get("interpretations") or {}
    user_edits = interps.get("_user_edits") or {}

    analyst_lenses = [
        ("Brand & Messaging", "brand_messaging", [
            "brand_visual_language", "brand_voice_messaging",
            "value_proposition", "brand_differentiation",
        ]),
        ("Experience & Design", "experience_design", [
            "interface_design", "content_taxonomy",
            "navigation_architecture", "responsiveness",
        ]),
        ("Conversion & Strategy", "conversion_strategy", [
            "call_to_action_logic", "lead_capture_form_design",
            "trust_signals", "funnel_design",
        ]),
    ]

    has_analyst = False
    analyst_parts: list[str] = []

    for lens_name, lens_key, expected_dims in analyst_lenses:
        row = analyst_by_lens.get(lens_name, {})
        sub = row.get("sub_scores", {})
        total = _sum_sub_scores(sub)

        # Get overall observations (user-edited > refined > raw)
        overall_obs = ""
        # Check user_edits in project_data.interpretations first
        if user_edits.get(lens_key):
            overall_obs = str(user_edits[lens_key])
        else:
            overall_obs = _get_overall_observations(row)

        # Only include if there's actual content
        if not sub and not overall_obs:
            continue

        has_analyst = True
        analyst_parts.append(f"\n{lens_name} ({total:.0f}/20):")

        if overall_obs:
            analyst_parts.append(f"Overall: {overall_obs}")

        for dim_key in expected_dims:
            dim_val = sub.get(dim_key)
            if dim_val is not None:
                line = _format_sub_dim(dim_key, dim_val)
                if line:
                    analyst_parts.append(line)

    if has_analyst:
        parts.append("\nANALYST ASSESSMENT:")
        parts.extend(analyst_parts)

    # --- JSON output instructions ---

    parts.append("""
Return this exact JSON structure:
{
  "no_brainers": [{"title": "...", "description": "...", "lens": "..."}],
  "quick_wins": [{"title": "...", "description": "...", "lens": "..."}],
  "growth_moves": [{"title": "...", "description": "...", "lens": "..."}],
  "transformational": [{"title": "...", "description": "...", "lens": "..."}]
}

Rules:
- 2-4 items per quadrant where evidence supports it
- Omit a quadrant entirely if there is no genuine recommendation for it
- No-Brainers: low effort, immediate impact
- Quick Wins: low effort, moderate impact
- Growth Moves: significant effort, high impact
- Transformational Initiatives: major investment, long-term strategic payoff
- Never use audit language — frame every recommendation as an opportunity
- Reference specific scores and analyst observations where relevant
- Lead with what is working before identifying gaps""")

    user_message = "\n".join(parts)
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

    try:
        quadrant_data = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.error(
            "Failed to parse Claude recommendations JSON for %s. "
            "Error: %s\nFull response:\n%s",
            project_id,
            exc,
            raw,
        )
        raise ValueError(
            f"AI returned invalid JSON. Parse error: {exc}"
        ) from exc

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
        for lens, score_data in auto_scores.items():
            if isinstance(score_data, dict) and score_data.get("score") is not None:
                analyst_lens_names = {s["lens_name"] for s in analyst_scores}
                if lens not in analyst_lens_names:
                    retina_score += score_data["score"]

        save_report(
            project_id=project_id,
            retina_score=round(retina_score, 2),
            ai_analysis={},
            quadrant_data=quadrant_data,
        )
        logger.info("Created new report with recommendations")

    return quadrant_data
