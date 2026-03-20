"""Site interpretation engine — generates strategic, three-part interpretations for all findings.

Calls the Claude API once per site to produce contextual interpretations
following the pattern: What it is → Why it matters → Where you stand.
Results are cached in Supabase alongside raw data.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import anthropic

from retina.config import Settings
from retina.analysis.standards import get_standards_prompt_block

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# System prompt — defines the Matic voice and output schema
# ---------------------------------------------------------------------------

INTERPRETER_SYSTEM_PROMPT = """\
You are Retina, a senior digital strategist at Matic Digital. Your job is to
interpret raw website performance data and produce strategic, business-focused
interpretations that a CMO or VP of Marketing would find immediately useful.

## Voice Rules
- Lead with the INSIGHT, never with the score. Don't open with "You scored 23%."
  Open with what that number means for the business.
- Reference competitor performance when data is available. "You vs. them" is more
  actionable than abstract benchmarks.
- Frame gaps as OPPORTUNITIES, not failures. Say "This is where improvement would
  have the most visible impact" not "this is broken."
- Be specific and actionable. Not "improve your SEO" but "adding structured data
  markup would help search engines display richer results for your services pages."
- Assume the reader is a smart non-technical leader. A CMO should understand every
  word. A developer should not feel it's dumbed down.
- Never lead with negativity. Acknowledge strengths before surfacing gaps.
- Use Matic voice: "digital readiness" not "website quality", "conversion pathway"
  not "funnel", "visitor experience" not "UX", "creates friction" not "is broken".

## Three-Part Interpretation Pattern
For each data point, produce three fields:
- "what": One plain-English sentence explaining what this is and what the current
  value means. No jargon assumed.
- "why": The business impact — not the technical explanation. Connect to outcomes
  like conversion rates, visitor confidence, competitive positioning.
- "where": Competitive context. If competitor data is provided, compare directly
  (e.g., "Your LCP of 4.2s is 1.8s slower than the strongest competitor").
  If no competitor data, reference industry benchmarks or Google thresholds.

## Section Narratives
For "section_narrative" fields, write 2-3 sentences that frame what the data
reveals strategically. These introduce a section of findings to a non-technical
reader. Start with what works, then frame gaps as opportunities.

## Output Format
Return ONLY valid JSON matching this exact schema. No markdown fences, no
commentary outside the JSON.

{
  "overall": {
    "retina_score": {"what": "...", "why": "...", "where": "..."},
    "score_tier": "Poor|Challenging|Functional|Ideal"
  },
  "performance": {
    "section_narrative": "...",
    "lighthouse": {
      "performance": {"what": "...", "why": "...", "where": "..."},
      "accessibility": {"what": "...", "why": "...", "where": "..."},
      "best-practices": {"what": "...", "why": "...", "where": "..."}
    },
    "cwv": {
      "<metric_key>": {"what": "...", "why": "...", "where": "..."}
    },
    "tech_stack": {
      "section_narrative": "...",
      "findings": [
        {"name": "...", "category": "...", "what": "...", "why": "...", "where": "..."}
      ]
    },
    "audits": {
      "<audit_id>": {"what": "...", "why": "...", "where": "..."}
    }
  },
  "seo": {
    "section_narrative": "...",
    "lighthouse_seo": {"what": "...", "why": "...", "where": "..."},
    "meta": {
      "<audit_id>": {"what": "...", "why": "...", "where": "..."}
    },
    "crawlability": {
      "<audit_id>": {"what": "...", "why": "...", "where": "..."}
    },
    "audits": {
      "<audit_id>": {"what": "...", "why": "...", "where": "..."}
    }
  },
  "analyst_lenses": {
    "brand_messaging": {
      "orientation": "What this lens evaluates and what to pay attention to",
      "what_good_looks_like": "Description of excellence in this lens"
    },
    "experience_design": {
      "orientation": "...",
      "what_good_looks_like": "..."
    },
    "conversion_strategy": {
      "orientation": "...",
      "what_good_looks_like": "..."
    }
  },
  "competitive_narrative": "A paragraph summarizing competitive positioning"
}

IMPORTANT RULES:
- Include ONLY metrics/audits/technologies actually present in the input data.
  Do not invent findings for data that wasn't provided.
- For CWV metrics, use the metric key exactly as provided (e.g., "largest_contentful_paint_ms").
- For audits, use the audit ID exactly as provided (e.g., "document-title", "robots-txt").
- For tech stack findings, include only technologies found in the BuiltWith data.
- If no competitors are provided, use Google's recommended thresholds and
  industry benchmarks for the "where" field.
- Keep each "what", "why", and "where" field to 1-2 sentences. Be concise.
- The competitive_narrative should be one paragraph (3-5 sentences).
- Return ONLY the JSON object. No surrounding text or markdown.
"""


def build_interpreter_prompt(
    site_url: str,
    lighthouse_data: dict,
    builtwith_data: dict,
    automated_scores: dict,
    competitor_data: list[dict] | None = None,
) -> str:
    """Build the user prompt with all site data for interpretation.

    Args:
        site_url: The URL being interpreted.
        lighthouse_data: Dict with 'mobile' and 'desktop' keys containing
            lighthouse_scores, core_web_vitals, and audits.
        builtwith_data: BuiltWith technology detection results.
        automated_scores: Automated Retina lens scores.
        competitor_data: Optional list of competitor site data dicts for context.
    """
    payload = {
        "site_url": site_url,
        "lighthouse_data": lighthouse_data,
        "builtwith_data": builtwith_data,
        "automated_scores": automated_scores,
    }

    if competitor_data:
        payload["competitors"] = competitor_data

    prompt_parts = [
        f"Interpret the following website analysis data for {site_url}.",
        "",
        "Generate strategic, three-part interpretations (what/why/where) for every "
        "metric, audit finding, and technology detected. Follow the Matic voice "
        "guidelines and output schema exactly as specified in your instructions.",
    ]

    if competitor_data:
        comp_urls = [c.get("site_url", "Unknown") for c in competitor_data]
        prompt_parts.append(
            f"\nCompetitor data is included for: {', '.join(comp_urls)}. "
            "Use it for direct 'where you stand' comparisons."
        )
    else:
        prompt_parts.append(
            "\nNo competitor data available. Use Google's recommended thresholds "
            "and industry benchmarks for the 'where you stand' comparisons."
        )

    prompt_parts.append(f"\n```json\n{json.dumps(payload, indent=2)}\n```")

    return "\n".join(prompt_parts)


# ---------------------------------------------------------------------------
# SiteInterpreter class
# ---------------------------------------------------------------------------


class SiteInterpreter:
    """Generates site-specific interpretations by calling Claude once per site.

    Takes a site's complete analysis data (Lighthouse, BuiltWith, scores) and
    optional competitor context, then produces a structured interpretation dict
    following the three-part pattern: What it is / Why it matters / Where you stand.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def interpret(
        self,
        site_url: str,
        lighthouse_data: dict,
        builtwith_data: dict,
        automated_scores: dict,
        competitor_data: list[dict] | None = None,
    ) -> dict[str, Any]:
        """Generate strategic interpretations for a site's data.

        Args:
            site_url: URL being interpreted.
            lighthouse_data: Lighthouse results (mobile/desktop).
            builtwith_data: BuiltWith technology detection.
            automated_scores: Automated Retina lens scores.
            competitor_data: Optional competitor data for comparative context.

        Returns:
            Interpretation dict matching the schema, or empty dict on failure.
        """
        user_prompt = build_interpreter_prompt(
            site_url=site_url,
            lighthouse_data=lighthouse_data,
            builtwith_data=builtwith_data,
            automated_scores=automated_scores,
            competitor_data=competitor_data,
        )

        logger.info(
            "Generating interpretations for %s (%d chars of context)",
            site_url,
            len(user_prompt),
        )

        # Inject research standards for all lenses into the system prompt
        standards_blocks = []
        for lens_name in ("performance", "seo", "brand", "experience", "conversion"):
            block = get_standards_prompt_block(lens_name)
            if block:
                standards_blocks.append(f"### {lens_name.title()} Lens{block}")

        system_prompt = INTERPRETER_SYSTEM_PROMPT
        if standards_blocks:
            system_prompt += "\n\n" + "\n\n".join(standards_blocks)
            logger.info("Injected standards context for %d lenses", len(standards_blocks))

        try:
            message = self._client.messages.create(
                model=self._settings.anthropic_model,
                max_tokens=self._settings.anthropic_max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Extract response text
            response_text = ""
            for block in message.content:
                if block.type == "text":
                    response_text += block.text

            logger.info(
                "Interpretation response received — %d tokens (input: %d, output: %d)",
                message.usage.input_tokens + message.usage.output_tokens,
                message.usage.input_tokens,
                message.usage.output_tokens,
            )

            return self._parse_response(response_text)

        except anthropic.APIError as e:
            logger.error("Claude API error during interpretation: %s", e)
            return {}
        except Exception as e:
            logger.exception("Unexpected error during interpretation for %s", site_url)
            return {}

    @staticmethod
    def _parse_response(response_text: str) -> dict[str, Any]:
        """Parse Claude's JSON response, stripping markdown fences if present."""
        text = response_text.strip()

        # Strip markdown code fences
        if text.startswith("```"):
            first_newline = text.index("\n")
            text = text[first_newline + 1:]
        if text.endswith("```"):
            text = text[:-3].rstrip()

        try:
            result = json.loads(text)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse interpretation response as JSON: %s", e)
            logger.debug("Raw response: %s", response_text[:1000])
            return {}

        # Basic validation — ensure top-level keys exist
        if not isinstance(result, dict):
            logger.error("Interpretation response is not a dict")
            return {}

        # Ensure expected top-level structure
        for key in ("overall", "performance", "seo"):
            if key not in result:
                logger.warning("Interpretation missing expected key: %s", key)

        return result
