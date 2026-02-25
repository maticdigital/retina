"""AI-powered seeder for analyst lens starting scores and observations.

Uses the Claude API to evaluate a site across the three analyst lenses
(Brand & Messaging, Experience & Design, Conversion & Strategy) and produce
starting scores and draft observation narratives that analysts can refine.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import anthropic

from retina.config import Settings
from retina.scoring.analyst import LENS_DEFINITIONS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt — strategic, consultative tone inspired by Matic deliverables
# ---------------------------------------------------------------------------
SEEDER_SYSTEM_PROMPT = """\
You are Retina, the intelligence engine behind Matic Digital's website \
evaluation platform. Matic is a strategic digital consultancy that helps \
brands understand where online performance is being won or lost.

Your voice is that of a senior strategist — confident, direct, and always \
connecting technical findings to business outcomes. You frame every observation \
in terms of competitive positioning, visitor experience, and pipeline impact. \
You are constructive, not critical: gaps are opportunities, not failures.

You will receive structured data about a website including:
- Lighthouse performance and accessibility scores
- Core Web Vitals measurements
- Technology stack (CMS, frameworks, hosting, CDN, analytics)
- Automated Retina Scores for performance and SEO lenses

Your job is to produce an initial evaluation across three analyst lenses, \
scoring each sub-dimension and writing a strategic observation narrative.

## Lens Definitions

**Brand & Messaging**: How clearly the website communicates who it is for, \
what it offers, and why it matters.

**Experience & Design**: How intuitive, modern, and intentional the website \
feels — from navigation and layout to visual hierarchy and mobile responsiveness.

**Conversion & Strategy**: How effectively the website turns attention into \
action through clear CTAs, logical user paths, and trust-building content.

## Scoring Guidelines

Score each sub-dimension on a scale from 0 to its maximum value, in 0.5 \
increments. Be calibrated:
- 0-25% of max: Critical gaps, immediate attention needed
- 26-50%: Below expectations, targeted improvement required
- 51-75%: Functional with room for growth
- 76-100%: Strong execution, competitive advantage

Most sites land in the 40-70% range. Only truly exceptional implementations \
score above 80%.

Common signals that lower scores:
- Brand: Visual language inconsistent across pages, voice doesn't match target \
audience, value proposition unclear within 5 seconds, nothing differentiates \
from competitors
- Experience: Interface design feels dated or inconsistent, content lacks clear \
taxonomy, navigation requires effort to parse, mobile rendering creates friction
- Conversion: CTAs are weak or buried, lead capture forms create friction, trust \
signals absent or hard to find, conversion funnel has gaps or dead ends

## Observation Narrative Guidelines

Write each observation as a ~150-200 word strategic brief following this structure:

1. **Open with positioning assessment**: "The site presents..." or "From a \
competitive standpoint..." — set the overall impression
2. **Acknowledge 1-2 strengths**: What the site does well, framed as assets \
worth preserving. Be specific — reference actual elements.
3. **Identify 2-3 gaps as opportunities**: Frame each gap in terms of business \
impact. Use "This creates an opportunity to..." or "Addressing this will \
improve..." — never "This is broken" or "This is bad."
4. **Close with directional recommendation**: One sentence pointing toward \
the highest-impact improvement area.

Language rules:
- Use "digital readiness" not "website quality"
- Use "visitor experience" not "UX"
- Use "conversion pathway" not "funnel"
- Use "creates friction" not "is broken"
- Every sentence must reference something specific about this site
- No filler — if a sentence could apply to any website, cut it

## Sub-Dimension Observation Guidelines

For each sub-dimension, write a 2-3 sentence observation that:
- References specific elements or patterns observed on the site
- Connects findings to business impact or visitor experience
- Frames gaps as opportunities, not failures

## Output Format

Respond with ONLY valid JSON matching this exact structure. Each sub-dimension \
includes both a numeric score AND a brief observation:

{
  "brand_messaging": {
    "sub_scores": {
      "brand_visual_language": {"score": 3.5, "observation": "The brand identity is communicated through consistent visual elements, though the logo treatment varies between pages. Strengthening the header lockup would reinforce recognition across touchpoints."},
      "brand_voice_messaging": {"score": 3.0, "observation": "Copy maintains a professional tone but defaults to feature-listing rather than benefit-framing. Shifting to client-outcome language would strengthen engagement."},
      "value_proposition": {"score": 2.5, "observation": "The value proposition is present but buried below the fold. Leading with outcome-focused language would better communicate differentiation to first-time visitors."},
      "brand_differentiation": {"score": 4.0, "observation": "The visual system uses a distinctive color palette and typography that sets it apart from competitors. This is an asset worth preserving and extending."}
    },
    "observations": "Overall strategic observation narrative for this lens..."
  },
  "experience_design": {
    "sub_scores": {
      "interface_design": {"score": 3.0, "observation": "Specific observation..."},
      "content_taxonomy": {"score": 3.0, "observation": "Specific observation..."},
      "navigation_architecture": {"score": 2.5, "observation": "Specific observation..."},
      "responsiveness": {"score": 3.5, "observation": "Specific observation..."}
    },
    "observations": "Overall strategic observation narrative for this lens..."
  },
  "conversion_strategy": {
    "sub_scores": {
      "call_to_action_logic": {"score": 2.5, "observation": "Specific observation..."},
      "lead_capture_form_design": {"score": 2.5, "observation": "Specific observation..."},
      "trust_signals": {"score": 3.0, "observation": "Specific observation..."},
      "funnel_design": {"score": 2.0, "observation": "Specific observation..."}
    },
    "observations": "Overall strategic observation narrative for this lens..."
  }
}

Reference actual scores, technologies, and measurements from the input data. \
No markdown, no code fences — just the JSON.\
"""


def _build_seeder_payload(
    site_url: str,
    lighthouse_data: dict,
    builtwith_data: dict,
    screenshot_paths: dict | None = None,
    automated_scores: dict | None = None,
) -> str:
    """Build the user prompt payload for the seeder."""
    payload = {
        "site_url": site_url,
        "lighthouse_data": lighthouse_data,
        "builtwith_data": builtwith_data,
        "screenshot_paths": screenshot_paths or {},
        "automated_scores": automated_scores or {},
    }
    return json.dumps(payload, indent=2, default=str)


class AnalystLensSeeder:
    """Seeds analyst lens scores and observations using Claude AI.

    Takes site analysis data and produces starting evaluations for all three
    analyst lenses. These serve as a foundation that human analysts can
    review, adjust, and enhance.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def seed(
        self,
        site_url: str,
        lighthouse_data: dict,
        builtwith_data: dict,
        screenshot_paths: dict | None = None,
        automated_scores: dict | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Generate starting scores and observations for all analyst lenses.

        Args:
            site_url: The URL being evaluated.
            lighthouse_data: Dict with mobile/desktop lighthouse data.
            builtwith_data: Dict with tech stack data.
            screenshot_paths: Optional dict with screenshot URLs.
            automated_scores: Optional dict with performance/SEO scores.

        Returns:
            Dict mapping lens_name -> {"sub_scores": {...}, "observations": "..."}
            Returns empty dict on failure.
        """
        payload = _build_seeder_payload(
            site_url, lighthouse_data, builtwith_data,
            screenshot_paths, automated_scores,
        )

        logger.info(
            "Seeding analyst lenses for %s (%d chars of context)",
            site_url, len(payload),
        )

        try:
            message = self._client.messages.create(
                model=self._settings.anthropic_model,
                max_tokens=4096,
                system=SEEDER_SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Evaluate the following website and produce starting scores "
                            f"and observations for all three analyst lenses.\n\n"
                            f"## Site Data\n\n{payload}\n\n"
                            f"Respond with ONLY the JSON object. No markdown, no explanation."
                        ),
                    }
                ],
            )
        except Exception as e:
            logger.exception("Analyst lens seeding API call failed for %s", site_url)
            return {}

        # Extract response text
        response_text = ""
        for block in message.content:
            if block.type == "text":
                response_text += block.text

        logger.info(
            "Seeder response for %s — %d tokens (input: %d, output: %d)",
            site_url,
            message.usage.input_tokens + message.usage.output_tokens,
            message.usage.input_tokens,
            message.usage.output_tokens,
        )

        return self._parse_response(response_text)

    def _parse_response(self, response_text: str) -> dict[str, dict[str, Any]]:
        """Parse the seeder JSON response, validating against LENS_DEFINITIONS."""
        text = response_text.strip()
        if text.startswith("```"):
            first_newline = text.index("\n")
            text = text[first_newline + 1:]
        if text.endswith("```"):
            text = text[:-3].rstrip()

        try:
            raw = json.loads(text)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse seeder response as JSON: %s", e)
            logger.debug("Raw response: %s", response_text[:500])
            return {}

        result: dict[str, dict[str, Any]] = {}

        for lens_name, sub_dims in LENS_DEFINITIONS.items():
            lens_data = raw.get(lens_name, {})
            if not isinstance(lens_data, dict):
                continue

            raw_scores = lens_data.get("sub_scores", {})
            observations = lens_data.get("observations", "")

            # Validate and clamp scores to valid ranges
            # Support both old {key: float} and new {key: {score, observation}} shapes
            validated_scores: dict[str, dict[str, Any]] = {}
            for dim_key, max_val in sub_dims.items():
                raw_val = raw_scores.get(dim_key, 0)
                obs_text = ""

                if isinstance(raw_val, dict):
                    # New shape: {score: float, observation: str}
                    score = raw_val.get("score", 0)
                    obs_text = str(raw_val.get("observation", ""))
                else:
                    # Old shape: just a float
                    score = raw_val

                try:
                    score = float(score)
                except (TypeError, ValueError):
                    score = 0.0
                # Round to nearest 0.5 and clamp
                score = round(score * 2) / 2
                score = max(0.0, min(score, max_val))
                validated_scores[dim_key] = {
                    "score": score,
                    "observation": obs_text,
                }

            result[lens_name] = {
                "sub_scores": validated_scores,
                "observations": str(observations),
            }

        return result
