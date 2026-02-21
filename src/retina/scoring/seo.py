"""SEO & AI Visibility scoring lens (0-20 points).

Derived from Lighthouse SEO and accessibility scores,
plus audit-level checks for structured data, meta tags,
mobile friendliness, and indexability signals.
"""

from __future__ import annotations

from retina.models.normalized import (
    LensScore,
    PerformanceData,
    ScoringLensType,
    SiteReport,
)

# Sub-component weights (sum to 20)
WEIGHTS = {
    "lighthouse_seo": 6.0,
    "lighthouse_accessibility": 4.0,
    "structured_data": 3.0,
    "meta_completeness": 3.0,
    "mobile_friendliness": 2.0,
    "indexability_signals": 2.0,
}

# Audit IDs we check for each sub-component
STRUCTURED_DATA_AUDITS = {"structured-data"}
META_AUDITS = {"meta-description", "document-title", "canonical", "hreflang"}
MOBILE_AUDITS = {"viewport", "tap-targets", "font-size"}
INDEXABILITY_AUDITS = {"robots-txt", "crawlable-anchors", "is-crawlable", "http-status-code"}


def score_seo_lens(report: SiteReport) -> LensScore:
    """Compute the SEO & AI Visibility lens (0-20 points).

    Args:
        report: A normalized SiteReport with performance data.

    Returns:
        LensScore with total and per-component breakdown.
    """
    breakdown: dict[str, float] = {}

    breakdown["lighthouse_seo"] = _score_lighthouse_seo(report.performance)
    breakdown["lighthouse_accessibility"] = _score_lighthouse_a11y(report.performance)
    breakdown["structured_data"] = _score_audit_group(
        report.performance, STRUCTURED_DATA_AUDITS, WEIGHTS["structured_data"]
    )
    breakdown["meta_completeness"] = _score_audit_group(
        report.performance, META_AUDITS, WEIGHTS["meta_completeness"]
    )
    breakdown["mobile_friendliness"] = _score_audit_group(
        report.performance, MOBILE_AUDITS, WEIGHTS["mobile_friendliness"]
    )
    breakdown["indexability_signals"] = _score_audit_group(
        report.performance, INDEXABILITY_AUDITS, WEIGHTS["indexability_signals"]
    )

    total = min(sum(breakdown.values()), 20.0)

    return LensScore(
        lens=ScoringLensType.SEO_AI_VISIBILITY,
        score=round(total, 2),
        breakdown={k: round(v, 2) for k, v in breakdown.items()},
        is_automated=True,
    )


def _score_lighthouse_seo(performance: list[PerformanceData]) -> float:
    """Score based on average Lighthouse SEO score (0-100 → 0-6)."""
    scores = [
        p.lighthouse_scores.seo
        for p in performance
        if p.lighthouse_scores.seo is not None
    ]
    if not scores:
        return 0.0
    avg = sum(scores) / len(scores)
    return (avg / 100) * WEIGHTS["lighthouse_seo"]


def _score_lighthouse_a11y(performance: list[PerformanceData]) -> float:
    """Score based on average Lighthouse accessibility score (0-100 → 0-4)."""
    scores = [
        p.lighthouse_scores.accessibility
        for p in performance
        if p.lighthouse_scores.accessibility is not None
    ]
    if not scores:
        return 0.0
    avg = sum(scores) / len(scores)
    return (avg / 100) * WEIGHTS["lighthouse_accessibility"]


def _score_audit_group(
    performance: list[PerformanceData],
    audit_ids: set[str],
    max_points: float,
) -> float:
    """Score a group of audits by their pass/fail rate.

    Looks for specific audit IDs in the performance data and calculates
    the proportion that pass (score >= 0.9 is passing). If an audit isn't
    found, it's treated as a miss (0 score). Averages across strategies.

    Args:
        performance: List of PerformanceData (mobile + desktop).
        audit_ids: Set of Lighthouse audit IDs to check.
        max_points: Maximum points for this sub-component.

    Returns:
        Score proportional to how many audits pass.
    """
    if not performance or not audit_ids:
        return 0.0

    strategy_scores: list[float] = []

    for perf in performance:
        # Build a lookup of audit scores for this strategy
        audit_scores: dict[str, float | None] = {}
        for audit in perf.audits:
            if audit.id in audit_ids:
                audit_scores[audit.id] = audit.score

        # Calculate pass rate for this strategy
        passing = 0
        total = len(audit_ids)

        for audit_id in audit_ids:
            score = audit_scores.get(audit_id)
            if score is not None and score >= 0.9:
                passing += 1
            elif score is not None and score > 0:
                passing += score  # partial credit

        strategy_scores.append(passing / total if total > 0 else 0.0)

    if not strategy_scores:
        return 0.0

    avg = sum(strategy_scores) / len(strategy_scores)
    return avg * max_points
