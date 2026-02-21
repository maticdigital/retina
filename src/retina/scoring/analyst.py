"""Analyst-scored lenses loaded from a YAML rubric file.

Handles the three manual scoring lenses:
- Brand & Messaging (20 pts)
- Experience & Design (20 pts)
- Conversion & Strategy (20 pts)

Each lens has sub-dimensions that sum to 20. Scores are clamped to valid
ranges and validated against the lens definitions.
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator

from retina.models.normalized import LensScore, ScoringLensType

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sub-dimension definitions (max points per sub-dimension)
# ---------------------------------------------------------------------------

LENS_DEFINITIONS: dict[str, dict[str, float]] = {
    "brand_messaging": {
        "brand_clarity_consistency": 5.0,
        "value_proposition_strength": 5.0,
        "content_quality_tone": 5.0,
        "visual_identity_differentiation": 5.0,
    },
    "experience_design": {
        "visual_design_quality": 4.0,
        "navigation_information_architecture": 4.0,
        "interaction_design_micro_interactions": 4.0,
        "responsiveness_cross_device": 4.0,
        "content_layout_readability": 4.0,
    },
    "conversion_strategy": {
        "cta_effectiveness": 4.0,
        "user_journey_funnel_design": 4.0,
        "trust_signals_social_proof": 4.0,
        "lead_capture_form_design": 4.0,
        "strategic_positioning_vs_competitors": 4.0,
    },
}

LENS_TYPE_MAP: dict[str, ScoringLensType] = {
    "brand_messaging": ScoringLensType.BRAND_MESSAGING,
    "experience_design": ScoringLensType.EXPERIENCE_DESIGN,
    "conversion_strategy": ScoringLensType.CONVERSION_STRATEGY,
}


# ---------------------------------------------------------------------------
# Pydantic models for YAML rubric structure
# ---------------------------------------------------------------------------


class RubricLens(BaseModel):
    """A single lens entry from the YAML rubric."""

    scores: dict[str, float] = Field(default_factory=dict)
    observations: str | None = None
    screenshots: list[str] = Field(default_factory=list)

    @field_validator("screenshots", mode="before")
    @classmethod
    def coerce_screenshots(cls, v: object) -> list[str]:
        """Accept a single string or list of strings."""
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return list(v)


class AnalystRubric(BaseModel):
    """A single site entry from the rubric YAML."""

    url: str
    analyst: str | None = None
    brand_messaging: RubricLens | None = None
    experience_design: RubricLens | None = None
    conversion_strategy: RubricLens | None = None


class RubricFile(BaseModel):
    """Root YAML structure containing site evaluations."""

    sites: list[AnalystRubric]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_rubric(path: str | Path) -> RubricFile:
    """Parse and validate a YAML rubric file.

    Supports three input formats:
    1. ``{sites: [...]}``: explicit wrapper
    2. ``[{url: ..., ...}]``: bare list of sites
    3. ``{url: ..., ...}``: single-site shorthand

    Args:
        path: Path to the YAML rubric file.

    Returns:
        Validated RubricFile.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the YAML is invalid or empty.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Rubric file not found: {path}")

    with open(path) as f:
        raw = yaml.safe_load(f)

    if raw is None:
        raise ValueError(f"Rubric file is empty: {path}")

    # Normalize to {sites: [...]} format
    if isinstance(raw, list):
        raw = {"sites": raw}
    elif isinstance(raw, dict) and "sites" not in raw:
        raw = {"sites": [raw]}

    rubric = RubricFile.model_validate(raw)

    # Log validation warnings for each site
    for site in rubric.sites:
        for lens_key in LENS_TYPE_MAP:
            rubric_lens: RubricLens | None = getattr(site, lens_key, None)
            if rubric_lens is not None:
                warnings = validate_lens_scores(lens_key, rubric_lens.scores)
                for w in warnings:
                    logger.warning("Rubric [%s]: %s", site.url, w)

    return rubric


def validate_lens_scores(
    lens_key: str,
    scores: dict[str, float],
) -> list[str]:
    """Validate sub-dimension scores against the lens definitions.

    Args:
        lens_key: The lens identifier (e.g., "brand_messaging").
        scores: Dict of sub-dimension name → score value.

    Returns:
        List of warning messages (empty if everything is valid).
    """
    warnings: list[str] = []
    definitions = LENS_DEFINITIONS.get(lens_key, {})

    for dim, value in scores.items():
        if dim not in definitions:
            warnings.append(f"Unknown sub-dimension '{dim}' in {lens_key}")
        else:
            max_val = definitions[dim]
            if value < 0:
                warnings.append(f"{lens_key}.{dim}: score {value} is negative, will clamp to 0")
            elif value > max_val:
                warnings.append(
                    f"{lens_key}.{dim}: score {value} exceeds max {max_val}, will clamp"
                )

    for dim in definitions:
        if dim not in scores:
            warnings.append(f"{lens_key}.{dim}: missing (will default to 0)")

    return warnings


def scores_for_url(
    rubric: RubricFile,
    normalized_url: str,
) -> list[LensScore]:
    """Extract LensScore objects for a specific URL from the rubric.

    Matches the URL against rubric entries using exact match first,
    then falls back to substring matching for flexibility.

    Args:
        rubric: Parsed and validated rubric file.
        normalized_url: The normalized URL to match.

    Returns:
        List of LensScore objects (0-3 items).
    """
    results: list[LensScore] = []

    site_entry = _find_site_entry(rubric, normalized_url)
    if site_entry is None:
        logger.warning("No rubric entry found for %s", normalized_url)
        return results

    for lens_key, lens_type in LENS_TYPE_MAP.items():
        rubric_lens: RubricLens | None = getattr(site_entry, lens_key, None)
        if rubric_lens is None:
            continue

        definitions = LENS_DEFINITIONS[lens_key]
        breakdown: dict[str, float] = {}

        for dim, max_val in definitions.items():
            raw_score = rubric_lens.scores.get(dim, 0.0)
            breakdown[dim] = round(min(max(raw_score, 0.0), max_val), 2)

        total = min(sum(breakdown.values()), 20.0)

        results.append(
            LensScore(
                lens=lens_type,
                score=round(total, 2),
                breakdown=breakdown,
                notes=rubric_lens.observations,
                is_automated=False,
            )
        )

    return results


def get_rubric_screenshots(
    rubric: RubricFile,
    normalized_url: str,
) -> dict[str, list[str]]:
    """Extract analyst-provided screenshot paths from the rubric.

    Args:
        rubric: Parsed rubric file.
        normalized_url: The URL to look up.

    Returns:
        Dict mapping lens_key to list of file paths.
    """
    result: dict[str, list[str]] = {}

    site_entry = _find_site_entry(rubric, normalized_url)
    if site_entry is None:
        return result

    for lens_key in LENS_TYPE_MAP:
        rubric_lens: RubricLens | None = getattr(site_entry, lens_key, None)
        if rubric_lens and rubric_lens.screenshots:
            result[lens_key] = rubric_lens.screenshots

    return result


def _find_site_entry(
    rubric: RubricFile,
    normalized_url: str,
) -> AnalystRubric | None:
    """Find a matching site entry in the rubric.

    Tries exact match first, then substring match for flexibility.
    """
    # Exact match
    for site in rubric.sites:
        if site.url == normalized_url:
            return site

    # Substring fallback (analyst may use partial URLs)
    for site in rubric.sites:
        if normalized_url in site.url or site.url in normalized_url:
            return site

    return None
