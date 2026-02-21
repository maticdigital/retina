"""Retina CLI — analyze websites from the command line."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import uuid
from urllib.parse import urlparse

from retina.analysis.claude import ClaudeAnalyzer
from retina.clients.builtwith import BuiltWithClient
from retina.clients.pagespeed import PageSpeedClient
from retina.clients.screenshot import ScreenshotClient
from retina.config import Settings
from retina.models.normalized import (
    AnalysisRun,
    DeviceStrategy,
    ScreenshotData,
    SiteReport,
    StrategicQuadrant,
)
from retina.normalizers.builtwith import normalize_builtwith
from retina.normalizers.pagespeed import normalize_pagespeed
from retina.scoring.analyst import (
    RubricFile,
    get_rubric_screenshots,
    load_rubric,
    scores_for_url,
)
from retina.scoring.performance import score_performance_lens
from retina.scoring.seo import score_seo_lens
from retina.utils.url import normalize_url

logger = logging.getLogger(__name__)


async def collect_site_data(
    url: str,
    psi_client: PageSpeedClient,
    bw_client: BuiltWithClient,
    screenshot_client: ScreenshotClient | None = None,
) -> SiteReport:
    """Collect all API data for a single URL and return a normalized SiteReport.

    Runs PageSpeed (mobile + desktop), BuiltWith, and screenshot capture
    in parallel. Normalizes responses and computes automated scoring lenses.

    Args:
        url: The URL to analyze.
        psi_client: Configured PageSpeed Insights client.
        bw_client: Configured BuiltWith client.
        screenshot_client: Optional Playwright screenshot client.

    Returns:
        A fully populated SiteReport.
    """
    normalized = normalize_url(url)
    domain = urlparse(normalized).netloc
    logger.info("Collecting data for %s", normalized)

    # Build task list — screenshots run alongside API calls
    tasks: list = [
        psi_client.analyze_both_strategies(normalized),
        bw_client.lookup(normalized),
    ]
    if screenshot_client:
        tasks.append(screenshot_client.capture(normalized, domain))

    # Run all tasks in parallel, isolating failures
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Extract PageSpeed results
    psi_results = results[0]
    if isinstance(psi_results, Exception):
        logger.error("PageSpeed failed for %s: %s", normalized, psi_results)
        psi_results = {"mobile": {}, "desktop": {}}

    # Extract BuiltWith results
    bw_raw = results[1]
    if isinstance(bw_raw, Exception):
        logger.error("BuiltWith failed for %s: %s", normalized, bw_raw)
        bw_raw = {}

    # Extract screenshot results
    screenshot_data: ScreenshotData | None = None
    if screenshot_client and len(results) > 2:
        ss_result = results[2]
        if isinstance(ss_result, Exception):
            logger.warning("Screenshots failed for %s: %s", normalized, ss_result)
        elif isinstance(ss_result, ScreenshotData):
            screenshot_data = ss_result

    # Normalize API responses
    perf_mobile = normalize_pagespeed(psi_results.get("mobile", {}), DeviceStrategy.MOBILE)
    perf_desktop = normalize_pagespeed(psi_results.get("desktop", {}), DeviceStrategy.DESKTOP)
    tech_stack = normalize_builtwith(bw_raw)

    # Build the report
    report = SiteReport(
        url=url,
        normalized_url=normalized,
        performance=[perf_mobile, perf_desktop],
        tech_stack=tech_stack,
        screenshots=screenshot_data,
        raw_responses={"pagespeed": psi_results, "builtwith": bw_raw},
    )

    # Compute automated scoring lenses
    perf_score = score_performance_lens(report)
    seo_score = score_seo_lens(report)
    report.retina_score.lens_scores = [perf_score, seo_score]
    report.retina_score.compute_total()

    logger.info(
        "Completed %s — Retina Score: %.1f/40 (automated lenses)",
        normalized,
        report.retina_score.total,
    )
    return report


def _merge_analyst_scores(
    reports: list[SiteReport],
    rubric: RubricFile,
) -> None:
    """Merge analyst rubric scores into site reports.

    Extends each report's lens_scores with analyst-scored lenses
    and applies screenshot overrides from the rubric.
    """
    for report in reports:
        analyst_scores = scores_for_url(rubric, report.normalized_url)
        if analyst_scores:
            report.retina_score.lens_scores.extend(analyst_scores)
            report.retina_score.compute_total()

            # Apply screenshot overrides from rubric
            rubric_ss = get_rubric_screenshots(rubric, report.normalized_url)
            if rubric_ss:
                if report.screenshots is None:
                    report.screenshots = ScreenshotData()
                report.screenshots.analyst_overrides = {
                    k: v[0] for k, v in rubric_ss.items() if v
                }


async def run(args: argparse.Namespace) -> None:
    """Execute the full analysis pipeline."""
    settings = Settings()
    psi = PageSpeedClient(settings)
    bw = BuiltWithClient(settings)
    ss = None if args.no_screenshots else ScreenshotClient(settings)

    # Load rubric if provided
    rubric: RubricFile | None = None
    if args.rubric:
        try:
            rubric = load_rubric(args.rubric)
            print(f"  📋 Loaded analyst rubric from {args.rubric}")
        except (FileNotFoundError, ValueError) as e:
            print(f"  ⚠️  Could not load rubric: {e}")

    try:
        all_urls = [args.primary] + (args.competitors or [])
        print(f"\n🔍 Retina — Analyzing {len(all_urls)} site(s)...\n")

        for url in all_urls:
            print(f"  • {url}")
        print()

        print("📸 Capturing screenshots...")

        # Collect data for all sites in parallel (including screenshots)
        reports = await asyncio.gather(
            *[collect_site_data(u, psi, bw, ss) for u in all_urls]
        )

        # Count successful screenshots
        ss_count = sum(
            1 for r in reports
            if r.screenshots and (r.screenshots.full_page or r.screenshots.viewport)
        )
        print(f"  Screenshots captured for {ss_count}/{len(reports)} sites\n")

        # Merge analyst scores if rubric provided
        if rubric:
            _merge_analyst_scores(list(reports), rubric)
            scored_count = sum(
                1 for r in reports
                if any(not ls.is_automated for ls in r.retina_score.lens_scores)
            )
            print(f"  📋 Analyst scores applied to {scored_count}/{len(reports)} sites\n")

        # Build analysis run
        analysis = AnalysisRun(
            run_id=str(uuid.uuid4()),
            primary_site=reports[0],
            competitors=list(reports[1:]),
        )

        # Run AI analysis if we have competitors and the key is configured
        if analysis.competitors and settings.anthropic_api_key:
            print("🤖 Running Claude AI competitive analysis...")
            try:
                analyzer = ClaudeAnalyzer(settings)
                analysis.ai_analysis = analyzer.analyze(analysis)
                print("✅ AI analysis complete\n")
            except Exception as e:
                logger.exception("AI analysis failed")
                print(f"⚠️  AI analysis failed: {e}\n")
        elif not analysis.competitors:
            print("ℹ️  Skipping AI analysis (no competitors to compare against)\n")
        elif not settings.anthropic_api_key:
            print("ℹ️  Skipping AI analysis (ANTHROPIC_API_KEY not set)\n")

        # Output results
        output = analysis.model_dump_json(indent=2)

        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"✅ Report saved to {args.output}")
        else:
            print(output)

        # Print summary
        _print_summary(analysis, has_rubric=rubric is not None)

    finally:
        await psi.close()
        await bw.close()
        if ss:
            await ss.close()


def _print_summary(analysis: AnalysisRun, *, has_rubric: bool = False) -> None:
    """Print a quick summary table of scores and AI analysis highlights."""
    print("\n" + "=" * 60)
    print("  RETINA SCORE SUMMARY")
    print("=" * 60)

    all_reports = [analysis.primary_site] + analysis.competitors

    for i, report in enumerate(all_reports):
        label = "PRIMARY" if i == 0 else f"COMP {i}"
        score = report.retina_score.total
        has_analyst = any(not ls.is_automated for ls in report.retina_score.lens_scores)
        max_score = 100 if has_analyst else 40

        print(f"\n  [{label}] {report.normalized_url}")
        print(f"  Retina Score: {score:.1f} / {max_score}")

        # Group lenses by type
        automated = [ls for ls in report.retina_score.lens_scores if ls.is_automated]
        analyst = [ls for ls in report.retina_score.lens_scores if not ls.is_automated]

        if automated:
            print("    Automated:")
            for lens in automated:
                lens_name = lens.lens.value.replace("_", " ").title()
                print(f"      • {lens_name}: {lens.score:.1f} / 20")

        if analyst:
            print("    Analyst:")
            for lens in analyst:
                lens_name = lens.lens.value.replace("_", " ").title()
                print(f"      • {lens_name}: {lens.score:.1f} / 20")

        # Show screenshot status
        if report.screenshots:
            ss = report.screenshots
            parts = []
            if ss.full_page:
                parts.append("full-page")
            if ss.viewport:
                parts.append("viewport")
            if ss.analyst_overrides:
                parts.append(f"{len(ss.analyst_overrides)} analyst")
            if parts:
                print(f"    📸 Screenshots: {', '.join(parts)}")

    # AI Analysis summary
    if analysis.ai_analysis:
        ai = analysis.ai_analysis
        print("\n" + "=" * 60)
        print("  AI COMPETITIVE ANALYSIS")
        print("=" * 60)

        if ai.executive_summary:
            summary_preview = ai.executive_summary[:300]
            if len(ai.executive_summary) > 300:
                summary_preview += "..."
            print(f"\n  {summary_preview}")

        if ai.recommendations:
            quadrant_labels = {
                StrategicQuadrant.NO_BRAINER: "🎯 No-Brainers",
                StrategicQuadrant.GROWTH_MOVE: "🚀 Growth Moves",
                StrategicQuadrant.QUICK_WIN: "⚡ Quick Wins",
                StrategicQuadrant.TRANSFORMATIONAL: "🔮 Transformational",
            }
            print(f"\n  Recommendations ({len(ai.recommendations)} total):")
            for quadrant, label in quadrant_labels.items():
                count = sum(
                    1 for r in ai.recommendations if r.quadrant == quadrant
                )
                if count > 0:
                    print(f"    {label}: {count}")

        if ai.gaps:
            critical = [g for g in ai.gaps if g.severity == "critical"]
            if critical:
                print(f"\n  ⚠️  Critical Gaps ({len(critical)}):")
                for gap in critical[:3]:
                    print(f"    • {gap.title}")

        if ai.tokens_used:
            print(f"\n  Tokens used: {ai.tokens_used:,}")

    # Footer
    print("\n" + "=" * 60)
    if not has_rubric:
        print("  Analyst lenses pending — provide a rubric file with --rubric")
        print("  to unlock the full 100-point Retina Score.")
        print("  Template: rubric_template.yaml")
    else:
        any_missing = any(
            len(r.retina_score.lens_scores) < 5
            for r in [analysis.primary_site] + analysis.competitors
        )
        if any_missing:
            print("  Some sites are missing analyst scores in the rubric.")
            print("  Add entries for all URLs for full 100-point scoring.")
        else:
            print("  Full 100-point Retina Score computed for all sites.")
    print("=" * 60 + "\n")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="retina",
        description="Retina — AI-enabled website intelligence platform",
    )
    parser.add_argument(
        "primary",
        help="Primary URL to analyze",
    )
    parser.add_argument(
        "-c",
        "--competitors",
        nargs="*",
        default=[],
        help="Up to 3 competitor URLs",
    )
    parser.add_argument(
        "-r",
        "--rubric",
        help="Path to analyst rubric YAML file for manual scoring lenses",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file path for JSON report",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--no-screenshots",
        action="store_true",
        help="Skip automated screenshot capture",
    )

    args = parser.parse_args()

    # Validate competitor count
    if args.competitors and len(args.competitors) > 3:
        parser.error("Maximum 3 competitor URLs allowed")

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        print("\n\nAnalysis cancelled.")
        sys.exit(1)
    except Exception as e:
        logger.exception("Analysis failed")
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
