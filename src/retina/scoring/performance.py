"""Performance & Technical Health scoring lens (0-20 points).

Derived from Lighthouse performance scores, Core Web Vitals,
mobile/desktop parity, and tech stack health signals.
"""

from __future__ import annotations

from retina.models.normalized import (
    LensScore,
    PerformanceData,
    ScoringLensType,
    SiteReport,
    TechStackData,
)

# Sub-component weights (sum to 20)
WEIGHTS = {
    "lighthouse_performance": 6.0,
    "lighthouse_best_practices": 3.0,
    "core_web_vitals": 5.0,
    "mobile_desktop_parity": 2.0,
    "tech_stack_health": 4.0,
}

# Google's "good" CWV thresholds
CWV_THRESHOLDS = {
    "largest_contentful_paint_ms": 2500.0,
    "first_contentful_paint_ms": 1800.0,
    "cumulative_layout_shift": 0.1,
    "total_blocking_time_ms": 200.0,
    "speed_index_ms": 3400.0,
    "interaction_to_next_paint_ms": 200.0,
}

# Technologies that signal good technical health
POSITIVE_TECH_SIGNALS = {
    "cdn": ["Cloudflare", "Fastly", "Amazon CloudFront", "Akamai", "Vercel", "Netlify"],
    "modern_framework": [
        "React", "Next.js", "Vue.js", "Nuxt.js", "Svelte", "Angular", "Astro", "Remix",
    ],
    "performance": ["Webpack", "Vite", "esbuild", "Turbopack"],
}


def score_performance_lens(report: SiteReport) -> LensScore:
    """Compute the Performance & Technical Health lens (0-20 points).

    Args:
        report: A normalized SiteReport with performance data and tech stack.

    Returns:
        LensScore with total and per-component breakdown.
    """
    breakdown: dict[str, float] = {}

    breakdown["lighthouse_performance"] = _score_lighthouse_perf(report.performance)
    breakdown["lighthouse_best_practices"] = _score_lighthouse_bp(report.performance)
    breakdown["core_web_vitals"] = _score_cwv(report.performance)
    breakdown["mobile_desktop_parity"] = _score_parity(report.performance)
    breakdown["tech_stack_health"] = _score_tech_stack(report.tech_stack)

    total = min(sum(breakdown.values()), 20.0)

    return LensScore(
        lens=ScoringLensType.PERFORMANCE_TECHNICAL,
        score=round(total, 2),
        breakdown={k: round(v, 2) for k, v in breakdown.items()},
        is_automated=True,
    )


def _score_lighthouse_perf(performance: list[PerformanceData]) -> float:
    """Score based on average Lighthouse performance score (0-100 → 0-6)."""
    scores = [
        p.lighthouse_scores.performance
        for p in performance
        if p.lighthouse_scores.performance is not None
    ]
    if not scores:
        return 0.0
    avg = sum(scores) / len(scores)
    return (avg / 100) * WEIGHTS["lighthouse_performance"]


def _score_lighthouse_bp(performance: list[PerformanceData]) -> float:
    """Score based on average Lighthouse best practices score (0-100 → 0-3)."""
    scores = [
        p.lighthouse_scores.best_practices
        for p in performance
        if p.lighthouse_scores.best_practices is not None
    ]
    if not scores:
        return 0.0
    avg = sum(scores) / len(scores)
    return (avg / 100) * WEIGHTS["lighthouse_best_practices"]


def _score_cwv(performance: list[PerformanceData]) -> float:
    """Score Core Web Vitals against Google's 'good' thresholds (0-5).

    Each metric gets an equal share. Scoring is proportional:
    - At or below threshold = full points
    - Up to 2x threshold = linear decrease to 0
    - Above 2x threshold = 0
    """
    max_points = WEIGHTS["core_web_vitals"]
    metrics_checked = 0
    total_score = 0.0

    for perf in performance:
        cwv = perf.core_web_vitals
        for field, threshold in CWV_THRESHOLDS.items():
            value = getattr(cwv, field, None)
            if value is None:
                continue
            metrics_checked += 1

            if field == "cumulative_layout_shift":
                # CLS is lower-is-better, not milliseconds
                ratio = value / threshold if threshold > 0 else 1.0
            else:
                ratio = value / threshold if threshold > 0 else 1.0

            if ratio <= 1.0:
                total_score += 1.0  # full credit
            elif ratio <= 2.0:
                total_score += max(0.0, 2.0 - ratio)  # linear decrease
            # else: 0 points

    if metrics_checked == 0:
        return 0.0

    return (total_score / metrics_checked) * max_points


def _score_parity(performance: list[PerformanceData]) -> float:
    """Score how close mobile performance is to desktop (0-2).

    Perfect parity = full points. Large gaps reduce the score.
    """
    max_points = WEIGHTS["mobile_desktop_parity"]
    mobile_perf = None
    desktop_perf = None

    for p in performance:
        if p.strategy.value == "mobile" and p.lighthouse_scores.performance is not None:
            mobile_perf = p.lighthouse_scores.performance
        elif p.strategy.value == "desktop" and p.lighthouse_scores.performance is not None:
            desktop_perf = p.lighthouse_scores.performance

    if mobile_perf is None or desktop_perf is None:
        return 0.0

    # Calculate parity as ratio (mobile/desktop), capped at 1.0
    if desktop_perf == 0:
        return 0.0

    parity = min(mobile_perf / desktop_perf, 1.0)
    return parity * max_points


def _score_tech_stack(tech_stack: TechStackData | None) -> float:
    """Score tech stack health signals (0-4).

    Checks for: CDN usage, modern frameworks, build tools, HTTPS.
    Each signal category contributes equally.
    """
    max_points = WEIGHTS["tech_stack_health"]

    if tech_stack is None or not tech_stack.technologies:
        return 0.0

    tech_names = {t.name for t in tech_stack.technologies}
    tech_names_lower = {t.lower() for t in tech_names}
    signals_found = 0
    total_signals = len(POSITIVE_TECH_SIGNALS) + 1  # +1 for HTTPS

    # Check each signal category
    for _category, techs in POSITIVE_TECH_SIGNALS.items():
        if any(t in tech_names for t in techs):
            signals_found += 1

    # Check for HTTPS (often indicated by SSL certificate tech)
    ssl_indicators = {"ssl by default", "https", "ssl", "hsts", "let's encrypt"}
    if any(ind in name for name in tech_names_lower for ind in ssl_indicators):
        signals_found += 1

    return (signals_found / total_signals) * max_points
