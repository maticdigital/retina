"""Claude AI analysis engine for competitive intelligence."""

from __future__ import annotations

import json
import logging

import anthropic

from retina.analysis.prompts import SYSTEM_PROMPT, build_user_prompt
from retina.config import Settings
from retina.models.normalized import (
    AIAnalysis,
    AnalysisRun,
    CompetitiveDimension,
    EffortLevel,
    GapItem,
    ImpactLevel,
    Recommendation,
    StrategicQuadrant,
)

logger = logging.getLogger(__name__)


class ClaudeAnalyzer:
    """Uses the Claude API to generate competitive analysis from Retina data.

    Takes a completed AnalysisRun (with scores and normalized data) and produces
    an AIAnalysis with executive summary, competitive comparison, gaps, and
    prioritized recommendations mapped to the strategic quadrant matrix.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def analyze(self, analysis_run: AnalysisRun) -> AIAnalysis:
        """Run Claude analysis on a completed AnalysisRun.

        Args:
            analysis_run: The complete analysis with scored site reports.

        Returns:
            AIAnalysis with comparison, gaps, and recommendations.
        """
        # Prepare the data payload — strip raw_responses to save tokens
        payload = self._prepare_payload(analysis_run)

        logger.info(
            "Sending analysis to Claude (%s) — %d chars of context",
            self._settings.anthropic_model,
            len(payload),
        )

        # Call Claude API
        message = self._client.messages.create(
            model=self._settings.anthropic_model,
            max_tokens=self._settings.anthropic_max_tokens,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": build_user_prompt(payload),
                }
            ],
        )

        # Extract response text
        response_text = ""
        for block in message.content:
            if block.type == "text":
                response_text += block.text

        logger.info(
            "Claude response received — %d tokens used (input: %d, output: %d)",
            message.usage.input_tokens + message.usage.output_tokens,
            message.usage.input_tokens,
            message.usage.output_tokens,
        )

        # Parse JSON response into AIAnalysis
        ai_analysis = self._parse_response(response_text)
        ai_analysis.model_used = self._settings.anthropic_model
        ai_analysis.tokens_used = message.usage.input_tokens + message.usage.output_tokens

        return ai_analysis

    def _prepare_payload(self, analysis_run: AnalysisRun) -> str:
        """Prepare the analysis data payload, stripping bulky raw responses.

        Keeps scores, CWV, tech stack, and audits with non-null scores.
        Strips raw_responses and low-signal audit entries to stay within
        token limits while preserving all actionable data.
        """
        # Serialize without raw_responses
        data = analysis_run.model_dump(
            exclude={
                "primary_site": {"raw_responses"},
                "competitors": {"__all__": {"raw_responses"}},
                "ai_analysis": True,
            },
            mode="json",
        )

        # Further trim: remove audits with null scores (informational only)
        # to reduce token count while keeping scored findings
        for site_key in ["primary_site"]:
            if site_key in data:
                self._trim_audits(data[site_key])
        for comp in data.get("competitors", []):
            self._trim_audits(comp)

        return json.dumps(data, indent=2)

    @staticmethod
    def _trim_audits(site_data: dict) -> None:
        """Remove informational-only audits to save tokens."""
        for perf in site_data.get("performance", []):
            if "audits" in perf:
                perf["audits"] = [
                    a for a in perf["audits"]
                    if a.get("score") is not None and a.get("score") < 1.0
                ]

    def _parse_response(self, response_text: str) -> AIAnalysis:
        """Parse Claude's JSON response into an AIAnalysis model.

        Handles potential formatting issues (markdown fences, trailing text).
        """
        # Strip markdown code fences if present
        text = response_text.strip()
        if text.startswith("```"):
            # Remove opening fence (with optional language tag)
            first_newline = text.index("\n")
            text = text[first_newline + 1:]
        if text.endswith("```"):
            text = text[:-3].rstrip()

        try:
            raw = json.loads(text)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse Claude response as JSON: %s", e)
            logger.debug("Raw response: %s", response_text[:1000])
            # Return a minimal analysis with the raw text as summary
            return AIAnalysis(
                executive_summary=(
                    f"AI analysis response could not be parsed as structured JSON. "
                    f"Raw response preview: {response_text[:500]}"
                ),
            )

        # Build typed models from the parsed JSON, tolerating slight naming variations
        comparison = []
        for dim in raw.get("competitive_comparison", []):
            try:
                comparison.append(CompetitiveDimension(**dim))
            except Exception as e:
                logger.warning("Skipping malformed comparison dimension: %s", e)

        gaps = []
        for gap in raw.get("gaps", []):
            try:
                gaps.append(GapItem(**gap))
            except Exception as e:
                logger.warning("Skipping malformed gap: %s", e)

        recommendations = []
        for rec in raw.get("recommendations", []):
            try:
                rec = self._normalize_recommendation(rec)
                recommendations.append(Recommendation(**rec))
            except Exception as e:
                logger.warning("Skipping malformed recommendation: %s", e)

        return AIAnalysis(
            executive_summary=raw.get("executive_summary", ""),
            competitive_comparison=comparison,
            gaps=gaps,
            recommendations=recommendations,
        )

    @staticmethod
    def _normalize_recommendation(rec: dict) -> dict:
        """Normalize recommendation fields to match our enum values.

        Claude may produce slight variations like 'transformational_initiative'
        instead of 'transformational', or mixed case. This maps them back.
        """
        # Quadrant normalization
        quadrant_map = {
            "no_brainer": "no_brainer",
            "no-brainer": "no_brainer",
            "nobrainer": "no_brainer",
            "no_brainers": "no_brainer",
            "no-brainers": "no_brainer",
            "growth_move": "growth_move",
            "growth-move": "growth_move",
            "growthmove": "growth_move",
            "growth_moves": "growth_move",
            "growth-moves": "growth_move",
            "quick_win": "quick_win",
            "quick-win": "quick_win",
            "quickwin": "quick_win",
            "quick_wins": "quick_win",
            "quick-wins": "quick_win",
            "transformational": "transformational",
            "transformational_initiative": "transformational",
            "transformational-initiative": "transformational",
            "transformational_initiatives": "transformational",
            "transformational-initiatives": "transformational",
        }
        raw_q = rec.get("quadrant", "").lower().strip()
        rec["quadrant"] = quadrant_map.get(raw_q, raw_q)

        # Effort/impact normalization
        for field in ("effort", "impact"):
            val = rec.get(field, "").lower().strip()
            if val in ("low", "high"):
                rec[field] = val
            elif "low" in val:
                rec[field] = "low"
            elif "high" in val:
                rec[field] = "high"

        return rec
