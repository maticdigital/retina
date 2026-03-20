"""Standards library fetcher — loads active standards for injection into analysis prompts.

Queries the retina_standards table in Supabase and formats them for inclusion
in Claude API system prompts. Falls back gracefully if the table doesn't exist
or the query fails.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


def _get_supabase_client():
    """Get a Supabase client for standards queries."""
    try:
        from supabase import create_client
    except ImportError:
        logger.warning("supabase package not installed — standards will not be loaded")
        return None

    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        logger.warning("Supabase credentials not configured — standards will not be loaded")
        return None

    return create_client(url, key)


def fetch_standards_for_lens(lens: str) -> list[dict[str, Any]]:
    """Fetch all active standards for a given lens from Supabase.

    Args:
        lens: One of 'performance', 'seo', 'brand', 'experience', 'conversion'

    Returns:
        List of standard dicts, or empty list on failure.
    """
    sb = _get_supabase_client()
    if not sb:
        return []

    try:
        resp = (
            sb.table("retina_standards")
            .select("category, principle, source, source_url, evaluation_criteria, scoring_guidance")
            .eq("lens", lens)
            .eq("is_active", True)
            .order("category")
            .execute()
        )
        standards = resp.data or []
        logger.info("Loaded %d standards for lens '%s'", len(standards), lens)
        return standards
    except Exception as e:
        logger.warning("Failed to fetch standards for lens '%s': %s", lens, e)
        return []


def build_standards_context(standards: list[dict[str, Any]]) -> str:
    """Format a list of standards into a text block for prompt injection.

    Args:
        standards: List of standard dicts from fetch_standards_for_lens().

    Returns:
        Formatted string ready for inclusion in a system prompt, or empty string.
    """
    if not standards:
        return ""

    blocks = []
    for s in standards:
        source_line = f"**{s['source']}**"
        if s.get("source_url"):
            source_line += f" ({s['source_url']})"

        blocks.append(
            f"{source_line} — {s['principle']}\n"
            f"Evaluate: {s['evaluation_criteria']}\n"
            f"Scoring: {s['scoring_guidance']}"
        )

    return "\n\n".join(blocks)


def get_standards_prompt_block(lens: str) -> str:
    """One-call convenience: fetch standards and format them for prompt injection.

    Args:
        lens: The lens name to fetch standards for.

    Returns:
        A formatted prompt block with header, or empty string if no standards found.
    """
    standards = fetch_standards_for_lens(lens)
    context = build_standards_context(standards)

    if not context:
        return ""

    return (
        "\n\n## Research Standards & Evaluation Criteria\n\n"
        "Ground your analysis in these established research standards. "
        "Reference specific standards where applicable — for example: "
        "\"Based on NNG's trust pyramid framework, this site...\" or "
        "\"Google's Core Web Vitals threshold for LCP is 2.5s; this site's 4.1s score...\"\n"
        "Do not simply list the standards — use them to inform your specific observations "
        "about this website. They provide the grounding, not the content.\n\n"
        f"{context}"
    )
