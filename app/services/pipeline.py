"""Pipeline runner — connects existing Retina analysis to Supabase storage."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import tempfile
from typing import Any

# Add src to path so we can import retina modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from retina.analysis.claude import ClaudeAnalyzer
from retina.clients.builtwith import BuiltWithClient
from retina.clients.pagespeed import PageSpeedClient
from retina.clients.screenshot import ScreenshotClient
from retina.config import Settings
from retina.models.normalized import AnalysisRun, DeviceStrategy, ScreenshotData, SiteReport
from retina.normalizers.builtwith import normalize_builtwith
from retina.normalizers.pagespeed import normalize_pagespeed
from retina.report.renderer import render_pdf
from retina.scoring.performance import score_performance_lens
from retina.scoring.seo import score_seo_lens
from retina.utils.url import normalize_url

from app.services.projects import save_project_data, save_report, update_project_status
from app.services.storage import upload_report_pdf, upload_screenshot

logger = logging.getLogger(__name__)


async def collect_site_data(
    url: str,
    psi_client: PageSpeedClient,
    bw_client: BuiltWithClient,
    screenshot_client: ScreenshotClient | None = None,
) -> SiteReport:
    """Collect all data for a single URL — same as cli.collect_site_data."""
    from urllib.parse import urlparse

    normalized = normalize_url(url)
    domain = urlparse(normalized).netloc
    logger.info("Collecting data for %s", normalized)

    tasks: list = [
        psi_client.analyze_both_strategies(normalized),
        bw_client.lookup(normalized),
    ]
    if screenshot_client:
        tasks.append(screenshot_client.capture(normalized, domain))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    psi_results = results[0]
    if isinstance(psi_results, Exception):
        logger.error("PageSpeed failed for %s: %s", normalized, psi_results)
        psi_results = {"mobile": {}, "desktop": {}}

    bw_raw = results[1]
    if isinstance(bw_raw, Exception):
        logger.error("BuiltWith failed for %s: %s", normalized, bw_raw)
        bw_raw = {}

    screenshot_data: ScreenshotData | None = None
    if screenshot_client and len(results) > 2:
        ss_result = results[2]
        if isinstance(ss_result, Exception):
            logger.warning("Screenshots failed for %s: %s", normalized, ss_result)
        elif isinstance(ss_result, ScreenshotData):
            screenshot_data = ss_result

    perf_mobile = normalize_pagespeed(psi_results.get("mobile", {}), DeviceStrategy.MOBILE)
    perf_desktop = normalize_pagespeed(psi_results.get("desktop", {}), DeviceStrategy.DESKTOP)
    tech_stack = normalize_builtwith(bw_raw)

    report = SiteReport(
        url=url,
        normalized_url=normalized,
        performance=[perf_mobile, perf_desktop],
        tech_stack=tech_stack,
        screenshots=screenshot_data,
        raw_responses={"pagespeed": psi_results, "builtwith": bw_raw},
    )

    perf_score = score_performance_lens(report)
    seo_score = score_seo_lens(report)
    report.retina_score.lens_scores = [perf_score, seo_score]
    report.retina_score.compute_total()

    return report


async def run_analysis(
    project_id: str,
    primary_url: str,
    competitor_urls: list[str],
    progress_callback=None,
) -> dict[str, Any]:
    """Run the full analysis pipeline for a project and store results in Supabase.

    Args:
        project_id: The Supabase project ID.
        primary_url: Primary URL to analyze.
        competitor_urls: List of competitor URLs.
        progress_callback: Optional callable(message: str) for status updates.

    Returns:
        Summary dict with scores and report info.
    """

    def _progress(msg: str) -> None:
        if progress_callback:
            progress_callback(msg)
        logger.info(msg)

    update_project_status(project_id, "in_progress")
    _progress("Initializing analysis clients...")

    settings = Settings()
    psi = PageSpeedClient(settings)
    bw = BuiltWithClient(settings)
    ss = ScreenshotClient(settings)

    try:
        all_urls = [primary_url] + competitor_urls
        _progress(f"Analyzing {len(all_urls)} site(s)...")

        # Collect data for all sites
        reports: list[SiteReport] = []
        for i, url in enumerate(all_urls):
            _progress(f"Collecting data for {url} ({i + 1}/{len(all_urls)})...")
            report = await collect_site_data(url, psi, bw, ss)
            reports.append(report)

        # Upload screenshots to Supabase Storage and store data
        for report in reports:
            _progress(f"Storing data for {report.normalized_url}...")

            screenshot_urls = {}
            if report.screenshots:
                if report.screenshots.full_page and os.path.exists(report.screenshots.full_page):
                    url = upload_screenshot(report.screenshots.full_page, project_id)
                    screenshot_urls["full_page"] = url
                if report.screenshots.viewport and os.path.exists(report.screenshots.viewport):
                    url = upload_screenshot(report.screenshots.viewport, project_id)
                    screenshot_urls["viewport"] = url

            # Serialize scores for storage
            automated_scores = {}
            for ls in report.retina_score.lens_scores:
                automated_scores[ls.lens.value] = {
                    "score": ls.score,
                    "breakdown": ls.breakdown,
                    "notes": ls.notes,
                    "is_automated": ls.is_automated,
                }

            # Prepare lighthouse data (strip raw_responses to save space)
            lighthouse_data = {}
            for perf in report.performance:
                lighthouse_data[perf.strategy.value] = {
                    "lighthouse_scores": perf.lighthouse_scores.model_dump(),
                    "core_web_vitals": perf.core_web_vitals.model_dump(),
                }

            builtwith_data = report.tech_stack.model_dump() if report.tech_stack else {}

            save_project_data(
                project_id=project_id,
                site_url=report.normalized_url,
                lighthouse_data=lighthouse_data,
                builtwith_data=builtwith_data,
                screenshot_paths=screenshot_urls,
                automated_scores=automated_scores,
            )

        # Build AnalysisRun for AI analysis + PDF
        import uuid as _uuid

        analysis = AnalysisRun(
            run_id=str(_uuid.uuid4()),
            primary_site=reports[0],
            competitors=list(reports[1:]),
        )

        # Run AI analysis if competitors exist
        ai_analysis_data = {}
        if analysis.competitors and settings.anthropic_api_key:
            _progress("Running AI competitive analysis...")
            try:
                analyzer = ClaudeAnalyzer(settings)
                analysis.ai_analysis = analyzer.analyze(analysis)
                ai_analysis_data = analysis.ai_analysis.model_dump()
                _progress("AI analysis complete.")
            except Exception as e:
                logger.exception("AI analysis failed")
                _progress(f"AI analysis failed: {e}")

        # Generate PDF
        _progress("Generating PDF report...")
        pdf_url = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp_path = tmp.name
            render_pdf(analysis, tmp_path)
            pdf_url = upload_report_pdf(tmp_path, project_id)
            os.unlink(tmp_path)
            _progress("PDF report generated and uploaded.")
        except Exception as e:
            logger.exception("PDF generation failed")
            _progress(f"PDF generation failed: {e}")

        # Compute quadrant data from recommendations
        quadrant_data = {}
        if analysis.ai_analysis and analysis.ai_analysis.recommendations:
            for rec in analysis.ai_analysis.recommendations:
                q = rec.quadrant.value
                quadrant_data.setdefault(q, []).append({
                    "title": rec.title,
                    "effort": rec.effort.value,
                    "impact": rec.impact.value,
                })

        # Save report to Supabase
        total_score = reports[0].retina_score.total
        save_report(
            project_id=project_id,
            retina_score=total_score,
            ai_analysis=ai_analysis_data,
            quadrant_data=quadrant_data,
            pdf_path=pdf_url,
        )

        update_project_status(project_id, "complete")
        _progress("Analysis complete!")

        return {
            "retina_score": total_score,
            "sites_analyzed": len(all_urls),
            "pdf_url": pdf_url,
            "ai_analysis": bool(ai_analysis_data),
        }

    finally:
        await psi.close()
        await bw.close()
        if ss:
            await ss.close()


def run_analysis_sync(
    project_id: str,
    primary_url: str,
    competitor_urls: list[str],
    progress_callback=None,
) -> dict[str, Any]:
    """Synchronous wrapper for run_analysis."""
    return asyncio.run(
        run_analysis(project_id, primary_url, competitor_urls, progress_callback)
    )
